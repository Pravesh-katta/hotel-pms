# GCP Deployment Architecture

Scale: 20+ hotels, 11-15 rooms each, ~250-300 rooms total.

---

## 1. Infrastructure Overview

```text
┌─────────────────────────────────────────────────────────────┐
│                         GITHUB                               │
│                                                              │
│  Push to main ──▶ GitHub Actions                             │
│                     ├── Lint + Tests                         │
│                     ├── Build Docker image                   │
│                     ├── Push to Artifact Registry            │
│                     ├── Run DB migrations                    │
│                     └── Deploy to Cloud Run (auto)           │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│                     GCP INFRASTRUCTURE                       │
│                                                              │
│  ┌─────────────┐                                            │
│  │  Cloud Run   │◄── Auto-scales 0 → 10 based on traffic    │
│  │  (Django)    │    Scale up when users increase            │
│  └──┬──────┬───┘    Scale down to 0 when idle               │
│     │      │                                                │
│     │      │    ┌──────────────┐                            │
│     │      ├───▶│ Cloud Storage │  Invoices, docs, images    │
│     │      │    └──────────────┘                            │
│     │      │                                                │
│     │      │    ┌──────────────┐                            │
│     │      └───▶│ Secret Manager│  DB pass, API keys         │
│     │           └──────────────┘                            │
│     │                                                       │
│     ▼                                                       │
│  ┌─────────────┐                                            │
│  │  Cloud SQL   │  PostgreSQL 15                             │
│  │  (db-f1-micro)│  Private IP, daily backups               │
│  └─────────────┘                                            │
│                                                              │
│  ┌─────────────┐     ┌─────────────┐                        │
│  │   Cloud      │────▶│  Cloud Run  │  Night audit, OTA sync │
│  │  Scheduler   │     │ (same app)  │                        │
│  └─────────────┘     └─────────────┘                        │
│                                                              │
└──────────────────────────────────────────────────────────────┘

Removed from original design:
  ✗ Redis / Memorystore  — unnecessary at this scale, saves $35/month
  ✗ Cloud Build          — replaced by GitHub Actions
  ✗ Cloud Load Balancer  — Cloud Run has built-in HTTPS + custom domain
  ✗ VPC Connector        — use Cloud SQL Auth Proxy instead (simpler)
```

---

## 2. CI/CD — GitHub Actions (Full Pipeline)

Every push goes through this pipeline. No manual deploys.

### Flow

```text
Developer pushes code to GitHub
        │
        ▼
┌─ GitHub Actions Workflow ──────────────────────────────────┐
│                                                             │
│  ON: push to main branch                                    │
│  ON: pull request to main (runs checks only, no deploy)     │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ STAGE 1: CHECK                                        │  │
│  │                                                       │  │
│  │  1. Checkout code                                     │  │
│  │  2. Set up Python 3.11                                │  │
│  │  3. Install dependencies (pip install -r requirements) │  │
│  │  4. Run linter (flake8 or ruff)                       │  │
│  │  5. Run type checks (optional: mypy)                  │  │
│  │  6. Run tests (python manage.py test)                 │  │
│  │                                                       │  │
│  │  ❌ If ANY check fails → pipeline stops, no deploy    │  │
│  │  ✅ If all pass → continue to Stage 2                 │  │
│  └──────────────────────────────────────────────────────┘  │
│                         │                                   │
│                         ▼                                   │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ STAGE 2: BUILD (only on push to main)                 │  │
│  │                                                       │  │
│  │  1. Authenticate to GCP (Workload Identity Federation)│  │
│  │  2. Build Docker image                                │  │
│  │  3. Tag with commit SHA + "latest"                    │  │
│  │  4. Push to GCP Artifact Registry                     │  │
│  └──────────────────────────────────────────────────────┘  │
│                         │                                   │
│                         ▼                                   │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ STAGE 3: DEPLOY (only on push to main)                │  │
│  │                                                       │  │
│  │  1. Run database migrations against Cloud SQL         │  │
│  │  2. Deploy new image to Cloud Run                     │  │
│  │  3. Cloud Run does zero-downtime rolling update       │  │
│  │  4. Health check passes → traffic shifts to new version│  │
│  │  5. Health check fails → auto-rollback to previous    │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### GitHub Actions Workflow File

```yaml
# .github/workflows/deploy.yml

name: Test, Build & Deploy

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

env:
  PROJECT_ID: your-gcp-project-id
  REGION: asia-south1
  SERVICE_NAME: hotel-pms-web
  REGISTRY: asia-south1-docker.pkg.dev
  IMAGE: asia-south1-docker.pkg.dev/$PROJECT_ID/hotel-pms/web

jobs:
  # ─────────────────────────────────────
  # STAGE 1: Lint + Test (runs on every push and PR)
  # ─────────────────────────────────────
  check:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_DB: test_db
          POSTGRES_USER: test_user
          POSTGRES_PASSWORD: test_pass
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"
          cache: "pip"

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Lint with ruff
        run: ruff check .

      - name: Run tests
        env:
          DATABASE_URL: postgres://test_user:test_pass@localhost:5432/test_db
          DJANGO_SETTINGS_MODULE: hotel_pms.settings.test
          SECRET_KEY: test-secret-key-not-for-production
        run: python manage.py test --verbosity=2

  # ─────────────────────────────────────
  # STAGE 2 + 3: Build & Deploy (only on push to main)
  # ─────────────────────────────────────
  deploy:
    needs: check
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest

    permissions:
      contents: read
      id-token: write    # Required for Workload Identity Federation

    steps:
      - uses: actions/checkout@v4

      - name: Authenticate to GCP
        uses: google-github-actions/auth@v2
        with:
          workload_identity_provider: projects/$PROJECT_NUMBER/locations/global/workloadIdentityPools/github-pool/providers/github-provider
          service_account: github-deploy@$PROJECT_ID.iam.gserviceaccount.com

      - name: Set up Cloud SDK
        uses: google-github-actions/setup-gcloud@v2

      - name: Configure Docker for Artifact Registry
        run: gcloud auth configure-docker $REGISTRY

      - name: Build Docker image
        run: |
          docker build -t $IMAGE:$GITHUB_SHA -t $IMAGE:latest .

      - name: Push Docker image
        run: |
          docker push $IMAGE:$GITHUB_SHA
          docker push $IMAGE:latest

      - name: Run database migrations
        run: |
          gcloud run jobs execute migrate-job \
            --region $REGION \
            --wait

      - name: Deploy to Cloud Run
        uses: google-github-actions/deploy-cloudrun@v2
        with:
          service: $SERVICE_NAME
          region: $REGION
          image: $IMAGE:$GITHUB_SHA

      - name: Verify deployment
        run: |
          URL=$(gcloud run services describe $SERVICE_NAME --region $REGION --format 'value(status.url)')
          curl -f "$URL/health/" || exit 1
```

### Pull Request Flow

```text
Developer creates a PR:
  1. GitHub Actions runs Stage 1 (lint + tests)
  2. PR shows ✅ or ❌ status check
  3. Code review happens
  4. Merge to main triggers full pipeline (Stage 1 + 2 + 3)

Branch protection rules on main:
  - Require status checks to pass before merging
  - Require at least 1 approval (optional, your choice)
  - No direct pushes to main (must go through PR)
```

---

## 3. Cloud Run Auto-Scaling

```text
┌──────────────────────────────────────────────────────────┐
│                  AUTO-SCALING BEHAVIOR                     │
│                                                          │
│  Traffic ──▶ Cloud Run scales instances automatically     │
│                                                          │
│  ┌─────────────────────────────────────────────────────┐ │
│  │                                                      │ │
│  │  Night (no users)     →  0 instances  (costs $0)     │ │
│  │  Morning (staff login)→  1 instance   (auto-start)   │ │
│  │  Peak (all hotels)    →  2-3 instances (auto-scale)  │ │
│  │  Sudden spike         →  up to 10 instances          │ │
│  │  Traffic drops        →  scales back down             │ │
│  │                                                      │ │
│  └─────────────────────────────────────────────────────┘ │
│                                                          │
│  You pay ONLY for what you use. No fixed servers running. │
└──────────────────────────────────────────────────────────┘
```

### Cloud Run Service Configuration

```text
Service:            hotel-pms-web
Region:             asia-south1 (Mumbai)
Port:               8000

Scaling:
  Min instances:    0       (scale to zero when idle — saves money)
  Max instances:    10      (handles sudden traffic spikes)
  Concurrency:      80      (requests per instance before scaling up)

  Scale-up trigger: When existing instances hit ~60% of concurrency (48 requests)
                    Cloud Run spins up a new instance automatically.

  Scale-down:       When an instance has 0 active requests for a period,
                    Cloud Run removes it.

Resources per instance:
  CPU:              1 vCPU
  Memory:           512 MB
  CPU allocation:   "CPU is only allocated during request processing"
                    (cheaper — CPU is not billed when idle)
  Startup CPU boost: enabled (faster cold starts)

Timeouts:
  Request timeout:  60s
  Startup timeout:  120s

Health check:
  Startup probe:    GET /health/ every 10s, 3 failures = unhealthy
  
Revision settings:
  Keep last 5 revisions (for instant rollback)

Environment variables (from Secret Manager):
  DATABASE_URL      → Cloud SQL connection string
  SECRET_KEY        → Django secret key
  GCS_BUCKET_NAME   → Cloud Storage bucket
  ALLOWED_HOSTS     → yourdomain.com
  DJANGO_SETTINGS_MODULE → hotel_pms.settings.production
```

### Cold Start Handling

```text
With min instances = 0, first request after idle period has a cold start.

Cold start time for Django on Cloud Run:
  Container pull:   ~1s (cached in region after first deploy)
  Python startup:   ~1s
  Gunicorn ready:   ~1s
  Total:            ~2-3 seconds

This is acceptable because:
  - Staff tool, not consumer-facing (users won't notice 2s on first load)
  - After first request, instance stays warm for ~15 minutes
  - During work hours, instances stay alive due to constant activity

If you later want instant response always:
  Set min instances = 1 (adds ~$15/month)
```

---

## 4. Cloud SQL Configuration

```text
Instance:           hotel-pms-db
Type:               PostgreSQL 15
Tier:               db-f1-micro
  CPU:              Shared vCPU
  Memory:           614 MB
  Max connections:  25
Storage:            10 GB SSD (auto-increase enabled)
Region:             asia-south1
High availability:  Off (turn on later if needed, doubles cost)
Backups:            Daily, 7-day retention, point-in-time recovery
Connection:         Cloud SQL Auth Proxy (from Cloud Run)

Why db-f1-micro is enough:
  ~300 rooms total, ~20-40 concurrent users
  Peak: ~5-10 queries/second
  db-f1-micro handles ~100 queries/second easily
  25 max connections is fine for 2-3 Cloud Run instances
```

### Database sizing (11-15 rooms per hotel)

```text
Estimated data per year (20 hotels × ~13 rooms avg):
  Hotels:              ~25 rows
  Rooms:               ~260 rows
  Guests:              ~15,000 rows/year
  Reservations:        ~15,000 rows/year
  FolioCharges:        ~100,000 rows/year
  AuditLogs:           ~200,000 rows/year

Total after 5 years:  ~1.5 million rows, under 1 GB
This is trivial for PostgreSQL.
```

---

## 5. Background Jobs

```text
Job                   │ Trigger              │ Frequency
──────────────────────┼──────────────────────┼──────────────────
Night Audit           │ Cloud Scheduler      │ Daily at 00:30 IST
Daily Sales Report    │ Cloud Scheduler      │ Daily at 06:00 IST
OTA Sync Check        │ Cloud Scheduler      │ Every 15 minutes
Stale Booking Cleanup │ Cloud Scheduler      │ Daily at 02:00 IST

Implementation:
  Cloud Scheduler → HTTP request to Cloud Run endpoint
  Django view processes the job
  
  No Cloud Tasks queue needed at this scale.
  Direct HTTP calls from Scheduler to Cloud Run are simpler.

Night audit at this scale:
  20 hotels × 13 rooms = 260 folio charges to post
  Completes in under 1 second.
```

---

## 6. Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN python manage.py collectstatic --noinput

CMD exec gunicorn hotel_pms.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 2 \
    --threads 4 \
    --timeout 60
```

---

## 7. SSL Certificate & Domain Name

```text
┌──────────────────────────────────────────────────────────────┐
│                 HOW YOU ACCESS THE SERVER                      │
│                                                              │
│  ✗ NO IP address needed. Ever.                               │
│  ✓ Always accessed via a domain name with HTTPS.             │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  OPTION 1: GCP Default URL (automatic, free)           │  │
│  │                                                        │  │
│  │  As soon as you deploy, GCP gives you:                 │  │
│  │    https://hotel-pms-web-xxxxx-el.a.run.app            │  │
│  │                                                        │  │
│  │  - Works immediately, no setup                         │  │
│  │  - SSL certificate included automatically              │  │
│  │  - Good for testing / early MVP                        │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  OPTION 2: Custom Domain (automated via Terraform)     │  │
│  │                                                        │  │
│  │  You own a domain like pms.yourcompany.com             │  │
│  │  Map it to Cloud Run:                                  │  │
│  │                                                        │  │
│  │  1. Terraform creates the domain mapping               │  │
│  │  2. You add a DNS record (CNAME) at your registrar     │  │
│  │  3. GCP auto-provisions a free SSL certificate         │  │
│  │  4. HTTPS works within minutes                         │  │
│  │  5. Auto-renews forever, no manual action              │  │
│  │                                                        │  │
│  │  Users access: https://pms.yourcompany.com             │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                              │
│  SSL Details:                                                │
│  - Certificate: Google-managed, free, auto-renewing          │
│  - Protocol: TLS 1.2+ only                                   │
│  - HTTP → HTTPS redirect: automatic                          │
│  - HSTS enabled in Django (forces browsers to use HTTPS)     │
│                                                              │
│  You do NOT need to:                                         │
│  - Buy an SSL certificate                                    │
│  - Configure nginx / apache                                  │
│  - Renew certificates manually                               │
│  - Set up a load balancer                                    │
│  - Know or manage any IP address                             │
└──────────────────────────────────────────────────────────────┘
```

---

## 8. Networking & Security

```text
HTTPS:
  - Cloud Run provides built-in HTTPS (no load balancer needed)
  - Custom domain mapped via Cloud Run domain mapping
  - Managed SSL certificate (free, auto-renew)
  - HTTP → HTTPS redirect automatic

Database:
  - Cloud SQL Auth Proxy handles secure connection
  - No public IP on Cloud SQL
  - IAM-based authentication from Cloud Run

GitHub → GCP authentication:
  - Workload Identity Federation (no service account keys stored in GitHub)
  - GitHub OIDC token → GCP short-lived credentials
  - Zero secrets stored in GitHub (most secure method)

Django security settings:
  SECURE_SSL_REDIRECT = True
  SESSION_COOKIE_SECURE = True
  CSRF_COOKIE_SECURE = True
  SECURE_HSTS_SECONDS = 31536000
```

---

## 9. Fully Automated GCP Infrastructure (Terraform)

Everything is automated. No clicking around in GCP Console.

### Why Terraform

```text
- One command creates ALL GCP resources
- Infrastructure is version-controlled in GitHub (same repo)
- Reproducible: tear down and recreate in minutes
- Changes tracked in git like code
- No manual steps = no human error
```

### What Terraform Creates Automatically

```text
terraform apply creates:

  1. ✓ GCP Project APIs enabled (Cloud Run, SQL, Storage, etc.)
  2. ✓ Artifact Registry repository (Docker images)
  3. ✓ Cloud SQL PostgreSQL instance + database + user
  4. ✓ Cloud Storage bucket (invoices, docs, images)
  5. ✓ Secret Manager secrets (DB URL, Django secret key, etc.)
  6. ✓ Cloud Run service (with auto-scaling config)
  7. ✓ Custom domain mapping + SSL certificate
  8. ✓ Cloud Scheduler jobs (night audit, OTA sync, cleanup)
  9. ✓ Workload Identity Federation (GitHub → GCP auth)
  10. ✓ Service account with minimal permissions
  11. ✓ IAM bindings (who can do what)
```

### Terraform File Structure

```text
infra/
├── main.tf                 # Provider config, project settings
├── cloud_run.tf            # Cloud Run service, scaling, domain mapping
├── cloud_sql.tf            # PostgreSQL instance, database, user
├── storage.tf              # Cloud Storage bucket
├── secrets.tf              # Secret Manager secrets
├── scheduler.tf            # Cloud Scheduler jobs
├── artifact_registry.tf    # Docker image registry
├── iam.tf                  # Service accounts, permissions
├── github_wif.tf           # Workload Identity Federation for GitHub Actions
├── variables.tf            # Input variables (project ID, region, domain, etc.)
├── outputs.tf              # Output values (Cloud Run URL, DB connection, etc.)
└── terraform.tfvars        # Your specific values (not committed to git)
```

### First-Time Setup (Fully Automated)

```text
Only 3 manual steps ever needed:

1. Install Terraform + gcloud CLI
   brew install terraform
   brew install google-cloud-sdk

2. Authenticate and set project
   gcloud auth login
   gcloud auth application-default login

3. Run Terraform
   cd infra/
   terraform init
   terraform plan          # Preview what will be created
   terraform apply         # Create everything

   Output:
     cloud_run_url = "https://hotel-pms-web-xxxxx-el.a.run.app"
     cloud_sql_connection = "project:asia-south1:hotel-pms-db"
     storage_bucket = "hotel-pms-files"
     
   → Done. All infrastructure exists.
   → First GitHub push to main will deploy the app automatically.

Optional 4th step (custom domain):
   Terraform outputs a CNAME record to add at your domain registrar.
   Add it, wait 5-10 minutes, HTTPS works on your custom domain.
```

### Updating Infrastructure

```text
Need to change something (e.g., increase max instances)?

1. Edit the .tf file
2. Commit to git
3. Run: terraform plan → terraform apply
4. Done. Change applied.

OR: Add Terraform to GitHub Actions so infrastructure changes
    also auto-deploy on push (full GitOps).
```

### Destroying Everything (if needed)

```text
terraform destroy
  → Removes ALL GCP resources
  → Clean slate, $0/month
  → Can recreate anytime with terraform apply
```

---

## 10. Estimated Monthly Cost (20 hotels, 11-15 rooms each)

```text
Service                    │ Tier              │ Est. Cost/month
───────────────────────────┼───────────────────┼─────────────────
Cloud Run                  │ 0-2 instances     │ $5 - $20
                           │ (scale to zero)   │
Cloud SQL (PostgreSQL)     │ db-f1-micro       │ $8 - $12
Cloud Storage              │ < 5 GB            │ $0.50
Secret Manager             │ < 10 secrets      │ $0.06
Artifact Registry          │ < 2 GB images     │ $0.50
Cloud Scheduler            │ 4-5 jobs          │ $0.50
───────────────────────────┼───────────────────┼─────────────────
TOTAL                      │                   │ ~$15 - $35/month

Removed from original estimate:
  ✗ Redis/Memorystore     -$35  (not needed)
  ✗ Cloud Load Balancer   -$20  (Cloud Run has built-in HTTPS)
  ✗ VPC Connector         -$7   (using Auth Proxy instead)
  ✗ Cloud Build           -$0   (replaced by GitHub Actions free tier)

GitHub Actions:
  Free tier: 2,000 minutes/month (more than enough)
```

---

## 11. Local Development Setup

```text
docker-compose.yml provides:
  - PostgreSQL 15 on port 5432
  - Django dev server on port 8000

Developers run:
  docker-compose up -d db
  python manage.py runserver

No Redis needed.
No GCP dependency for local development.
Environment variables loaded from .env file locally.
```

---

## 12. Rollback Strategy

```text
If a bad deploy goes out:

Automatic:
  - Cloud Run health check fails → stays on previous revision
  - Deploy step in GitHub Actions fails → no traffic shift

Manual (if bug found after deploy):
  - Cloud Run Console → select previous revision → route 100% traffic
  - Or: gcloud run services update-traffic hotel-pms-web \
         --to-revisions=PREVIOUS_REVISION=100 --region=asia-south1
  - Takes effect in seconds

  Cloud Run keeps last 5 revisions ready to serve.
```
