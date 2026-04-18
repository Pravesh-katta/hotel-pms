# Logging, Monitoring & Security Config

---

## 1. Logging Strategy

```text
Three layers of logging:

┌──────────────────────────────────────────────────────────────┐
│  LAYER 1: APPLICATION LOGS (Cloud Logging)                    │
│                                                              │
│  Django → Python logging → stdout → Cloud Run → Cloud Logging│
│                                                              │
│  What gets logged:                                           │
│   - Every HTTP request (method, path, status, response time) │
│   - Every error/exception (full traceback)                   │
│   - Payment events (created, completed, failed, refunded)    │
│   - OTA sync events (start, success, failure, conflict)      │
│   - Night audit events (start, charges posted, completion)   │
│   - Authentication events (login, logout, failed login)      │
│   - Notification delivery (sent, failed, retried)            │
│                                                              │
│  Log levels:                                                 │
│   ERROR   — exceptions, payment failures, OTA sync errors    │
│   WARNING — slow queries (>500ms), failed logins, retries    │
│   INFO    — request/response, business events                │
│   DEBUG   — detailed trace (local dev only, not production)  │
│                                                              │
│  Format (structured JSON for Cloud Logging):                 │
│   {                                                          │
│     "timestamp": "2026-04-11T10:30:00Z",                     │
│     "severity": "ERROR",                                     │
│     "message": "Razorpay webhook verification failed",       │
│     "hotel_id": "uuid-xxx",                                  │
│     "user_id": 42,                                           │
│     "path": "/api/webhooks/razorpay/",                       │
│     "trace_id": "abc123"                                     │
│   }                                                          │
│                                                              │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│  LAYER 2: AUDIT LOGS (Database — AuditLog model)             │
│                                                              │
│  What: Every data change by a user                           │
│  Stored in: PostgreSQL (queryable, reportable)               │
│  Retention: Forever (legal/compliance requirement)           │
│                                                              │
│  Tracked automatically via Django signals:                   │
│   - Reservation created/modified/cancelled                   │
│   - Payment received/refunded                                │
│   - Room status changed                                      │
│   - Guest info modified                                      │
│   - Rate plan changed                                        │
│   - Staff added/removed/role changed                         │
│   - Folio charges added/voided                               │
│                                                              │
│  Each entry stores: who, what, when, before/after values     │
│                                                              │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│  LAYER 3: ERROR TRACKING (Sentry)                            │
│                                                              │
│  Sentry captures:                                            │
│   - Unhandled exceptions with full context                   │
│   - Performance traces (slow endpoints)                      │
│   - User context (which staff member, which hotel)           │
│   - Release tracking (which deploy introduced the bug)       │
│                                                              │
│  Why Sentry (not just Cloud Logging):                        │
│   - Groups duplicate errors automatically                    │
│   - Alerts on new errors (not repeated ones)                 │
│   - Shows error frequency trends                             │
│   - Links errors to git commits                              │
│   - Free tier: 5K errors/month (more than enough)            │
│                                                              │
│  Integration:                                                │
│   pip install sentry-sdk                                     │
│   SENTRY_DSN stored in Secret Manager                        │
│   Initialized in settings/production.py                      │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

---

## 2. Monitoring & Alerts

```text
┌──────────────────────────────────────────────────────────────┐
│  MONITORING STACK                                             │
│                                                              │
│  Cloud Run built-in metrics (free):                          │
│   - Request count, latency, error rate                       │
│   - Instance count (scaling behavior)                        │
│   - Memory/CPU usage                                         │
│   - Container startup time                                   │
│                                                              │
│  Cloud SQL built-in metrics (free):                          │
│   - Active connections                                       │
│   - CPU utilization                                          │
│   - Disk usage                                               │
│   - Query latency                                            │
│                                                              │
│  Sentry:                                                     │
│   - Error rate per release                                   │
│   - Slowest endpoints                                        │
│   - Error grouping and trends                                │
│                                                              │
│  Custom health endpoint: GET /health/                        │
│   Returns:                                                   │
│    {                                                         │
│      "status": "ok",                                         │
│      "database": "ok",                                       │
│      "timestamp": "2026-04-11T10:30:00Z"                     │
│    }                                                         │
│   Cloud Run pings this for health checks.                    │
│                                                              │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│  ALERT RULES (Cloud Monitoring)                               │
│                                                              │
│  Alert                     │ Condition          │ Notify     │
│  ──────────────────────────┼────────────────────┼──────────  │
│  App down                  │ Health check fails │ WhatsApp   │
│                            │ for 3 minutes      │ super admin│
│  High error rate           │ > 10 errors/min    │ WhatsApp   │
│  Database near capacity    │ Connections > 20/25 │ Email      │
│  Disk 80% full             │ Cloud SQL storage   │ Email      │
│  Night audit failed        │ Audit status=failed │ WhatsApp   │
│  OTA sync failing          │ No sync > 1 hour   │ In-app     │
│  Payment webhook failing   │ > 3 failures/hour  │ WhatsApp   │
│                                                              │
│  Critical alerts → WhatsApp to super_admin (immediate)       │
│  Warning alerts → Email to super_admin (batched)             │
│  Info alerts → In-app notification only                      │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

---

## 3. Session & Authentication Security

```text
┌──────────────────────────────────────────────────────────────┐
│  SESSION CONFIGURATION                                        │
│                                                              │
│  Django settings:                                            │
│   SESSION_COOKIE_AGE = 28800         # 8 hours (one shift)   │
│   SESSION_EXPIRE_AT_BROWSER_CLOSE = True                     │
│   SESSION_COOKIE_SECURE = True       # HTTPS only            │
│   SESSION_COOKIE_HTTPONLY = True      # No JS access          │
│   SESSION_COOKIE_SAMESITE = 'Lax'                            │
│   SESSION_ENGINE = 'django.contrib.sessions.backends.db'     │
│                                                              │
│  Why 8 hours:                                                │
│   - Hotel staff work in shifts (typically 8 hours)           │
│   - Session expires when shift ends                          │
│   - Forces re-login for next shift (security)               │
│   - Browser close also kills session                         │
│                                                              │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│  AUTHENTICATION RULES                                         │
│                                                              │
│  Password policy:                                            │
│   - Minimum 8 characters                                     │
│   - Django built-in validators (common password check,       │
│     numeric-only check, similarity check)                    │
│   - No forced rotation (NIST guidelines — rotation           │
│     causes weaker passwords)                                 │
│                                                              │
│  Login protection:                                           │
│   - 5 failed attempts → account locked for 15 minutes        │
│   - Implemented via django-axes (pip install django-axes)    │
│   - Failed login → AuditLog entry with IP address            │
│   - Locked account → WhatsApp alert to hotel admin           │
│                                                              │
│  CSRF protection:                                            │
│   - Enabled on ALL form submissions (Django default)         │
│   - DISABLED on webhook endpoints (Razorpay, OTA)            │
│     — these use signature verification instead               │
│                                                              │
│  Webhook security:                                           │
│   /api/webhooks/razorpay/                                    │
│     → Verify Razorpay signature (HMAC-SHA256)                │
│     → Reject if signature invalid                            │
│     → Rate limit: 100 requests/minute                        │
│                                                              │
│   /api/tasks/night-audit/ (Cloud Scheduler)                  │
│     → Verify OIDC token from Cloud Scheduler                 │
│     → Reject if token invalid or expired                     │
│     → Only accessible from GCP internal                      │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

---

## 4. Data Protection

```text
┌──────────────────────────────────────────────────────────────┐
│  SENSITIVE DATA HANDLING                                      │
│                                                              │
│  Stored in database (encrypted at rest by Cloud SQL):        │
│   - Guest name, phone, email, address                        │
│   - Guest ID number (Aadhar, passport)                       │
│   - Reservation details                                      │
│   - Payment amounts and transaction IDs                      │
│                                                              │
│  Stored in Cloud Storage (encrypted at rest):                │
│   - Guest ID document photos (Aadhar front/back, passport)  │
│   - Invoices (PDF)                                           │
│   - Accessed via signed URLs (expire after 15 minutes)       │
│                                                              │
│  Stored in Secret Manager (never in code or DB):             │
│   - Razorpay key secrets (per-hotel)                         │
│   - Razorpay webhook secret                                  │
│   - Django SECRET_KEY                                        │
│   - DATABASE_URL                                             │
│   - MSG91 API key                                            │
│   - Sentry DSN                                               │
│   - OTA API credentials                                      │
│                                                              │
│  NEVER stored anywhere:                                      │
│   - Credit card numbers (Razorpay handles PCI compliance)    │
│   - UPI PINs                                                 │
│   - Raw passwords (Django stores hashed only)                │
│                                                              │
│  Access control:                                             │
│   - Guest ID photos: only accessible by same-hotel staff     │
│   - Cloud Storage URLs: signed, time-limited                 │
│   - Database: no public IP, IAM auth from Cloud Run only     │
│   - Audit logs: immutable, cannot be deleted by any user     │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

---

## 5. Backup & Recovery

```text
┌──────────────────────────────────────────────────────────────┐
│  BACKUP STRATEGY                                              │
│                                                              │
│  Database (Cloud SQL):                                       │
│   - Automated daily backups (enabled by default)             │
│   - Retention: 30 days (not 7 — extended for audits)         │
│   - Point-in-time recovery: enabled (recover to any second)  │
│   - Backup window: 02:00 - 06:00 IST (low activity)         │
│                                                              │
│  Cloud Storage (documents, invoices, photos):                │
│   - Object versioning enabled (recover deleted files)        │
│   - Lifecycle rule: move to Nearline after 90 days           │
│                                                              │
│  Recovery targets:                                           │
│   RTO (Recovery Time Objective): 30 minutes                  │
│     → Cloud SQL restore takes ~10-15 minutes                 │
│     → Cloud Run redeploy takes ~5 minutes                    │
│                                                              │
│   RPO (Recovery Point Objective): 1 minute                   │
│     → Point-in-time recovery from transaction logs           │
│     → Max 1 minute of data loss in worst case                │
│                                                              │
│  Quarterly restore test:                                     │
│   - Every quarter, restore backup to a test instance         │
│   - Verify data integrity                                    │
│   - Document results                                         │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

---

## 6. Python Packages for All of This

```text
Logging & monitoring:
  sentry-sdk          # Error tracking
  django-axes         # Login brute-force protection
  # Cloud Logging is automatic in Cloud Run (stdout → Cloud Logging)

Security:
  django-cors-headers # CORS for API endpoints
  # CSRF, session security are Django built-in

No additional packages needed for:
  - Cloud Logging (auto from stdout)
  - Cloud Monitoring (auto from Cloud Run metrics)
  - Backup (Cloud SQL managed feature)
```
