# Hotel PMS

Starter architecture for a hotel PMS project.

## Chosen Stack

Best choice for this project: `Django + PostgreSQL`

Why this is the best fit:

- PMS software is mostly forms, tables, staff workflows, billing, and role-based access
- Django already gives us admin, authentication, permissions, ORM, and a mature project structure
- It keeps the first version simpler than maintaining both Next.js and a separate backend
- It still deploys cleanly to GCP

## Full Component Diagram

```text
Hotel Staff
(Front Desk, Admin, Housekeeping, Manager)
                |
                v
        Web Browser / Tablet
                |
                v
      Django Web App
  (Templates + Views + APIs)
                |
    +-----------+------------+------------+-------------+--------------+
    |           |            |            |             |              |
    v           v            v            v             v              v
 Auth/Roles  Reservations  Front Desk   Rooms      Billing/Folio    Reports
                            Check-in    Guests
                            Check-out   Housekeeping
                |
                v
          Business Logic
                |
    +-----------+------------+-------------+--------------+-------------+
    |           |            |             |              |             |
    v           v            v             v              v             v
 PostgreSQL   Redis      File Storage   Background Jobs  Notifications  Audit Logs
 (main DB)    (cache)    (docs/images)  (night audit,   (email/SMS)    (activity)
                                      reports, tasks)
```

## Airbnb Booking Flow

```text
Airbnb
  |
  v
Official Software Connection
or Channel Manager Bridge
  |
  v
OTA Integration Layer
  |
  v
Booking Sync Worker
  |
  v
Reservations Module
  |
  v
PostgreSQL
  |
  v
Django Dashboard / Calendar / Reservation List
```

Notes:

- We should not scrape Airbnb
- Best production path: official Airbnb-connected software flow
- Fastest launch path for a new PMS: connect through an approved channel manager
- Basic `iCal` calendar sync can be used only as a fallback for availability blocking, not full PMS-grade reservation management

## GCP Deployment Diagram

```text
Users
  |
  v
Internet / Domain
  |
  v
Cloud Load Balancer
  |
  v
Cloud Run - Django App
(Web + API)
  |
  +-------------------+-------------------+-------------------+-------------------+
  |                   |                   |                   |                   |
  v                   v                   v                   v                   v
Cloud SQL         Memorystore         Cloud Storage      Secret Manager      Cloud Tasks
PostgreSQL        Redis               Files/Invoices     Env vars/keys       Background jobs
  |
  v
Backups

Cloud Scheduler
  |
  v
Night Audit / Daily Reports

Airbnb / OTA Channel
  |
  v
Integration Endpoint
  |
  v
Cloud Tasks
```

## Folder Diagram

```text
hotel-pms/
├── hotel_pms/             # Django project config
├── apps/                  # Django apps: reservations, billing, rooms, guests
├── database/              # schema, migrations, seed data
├── templates/             # Django HTML templates
├── static/                # CSS, JS, images
├── docs/                  # architecture and project docs
├── docker-compose.yml     # local development services
└── README.md
```

## Main Components We Will Use

- Web App: Django
- API Layer: Django REST Framework
- Database: PostgreSQL
- Cache: Redis
- Storage: Google Cloud Storage
- Jobs: Cloud Tasks, Cloud Scheduler
- Deployment: Cloud Run
- Secrets: Secret Manager
- CI/CD: Cloud Build
- OTA Integration: Airbnb official software connection or approved channel manager

## Detailed Architecture

See [docs/architecture.md](/Users/praveshkatta/Desktop/hotels%20pms/docs/architecture.md).
