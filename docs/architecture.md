# Hotel PMS Architecture

## 1. Product Component Diagram

```mermaid
flowchart TD
    A[Hotel Staff<br/>Front Desk / Admin / Housekeeping / Manager] --> B[Browser or Tablet]
    B --> C[Django Web App<br/>Templates + Views + APIs]
    S[Airbnb / OTA Channels] --> T[OTA Integration Layer]
    T --> U[Booking Sync Worker]
    U --> E

    C --> D[Authentication + RBAC]
    C --> E[Reservations Module]
    C --> F[Front Desk Module]
    C --> G[Rooms + Housekeeping Module]
    C --> H[Guest Management Module]
    C --> I[Billing / Folio Module]
    C --> J[Reports Module]
    C --> K[Django Admin]

    E --> L[(PostgreSQL)]
    F --> L
    G --> L
    H --> L
    I --> L
    J --> L
    K --> L

    C --> M[(Redis Cache)]
    C --> N[Cloud Storage<br/>Invoices / Documents / Room Images]
    C --> O[Background Jobs]
    O --> P[Email / SMS Notifications]
    O --> Q[Nightly Audit / Scheduled Reports]
    C --> R[Audit Logs]
```

## 2. GCP Deployment Diagram

```mermaid
flowchart TD
    A[Users] --> B[Internet / Domain]
    B --> C[Cloud Load Balancer]
    C --> D[Cloud Run<br/>Django App]
    N[Airbnb / OTA] --> O[Integration Endpoint]
    O --> I

    D --> E[(Cloud SQL PostgreSQL)]
    D --> F[(Memorystore Redis)]
    D --> G[Cloud Storage]
    D --> H[Secret Manager]
    D --> I[Cloud Tasks]
    J[Cloud Scheduler] --> I
    E --> K[Automated Backups]
    L[Cloud Build] --> M[Artifact Registry]
    M --> D
```

## 3. Recommended PMS Modules

```text
Dashboard
Reservations
Check-in / Check-out
Room Management
Housekeeping
Guest Management
Billing / Folio
Reports
Staff / Roles
Audit / Activity Logs
Admin Console
```

## 4. Recommended Tech Stack

```text
Web App       : Django
API           : Django REST Framework
Database      : PostgreSQL
Cache         : Redis
File Storage  : Google Cloud Storage
Jobs          : Cloud Tasks + Cloud Scheduler
Deploy        : Cloud Run
CI/CD         : Cloud Build + Artifact Registry
Secrets       : Secret Manager
```

## 5. MVP Scope

For the first version, keep it as:

```text
1 Django web application
1 PostgreSQL database
1 Redis cache
1 File storage bucket
1 OTA integration layer
```

This is enough for a strong hotel PMS MVP and is much easier to build than starting with microservices.

## 6. Why Django Is The Best Choice Here

```text
Internal staff-facing PMS apps benefit from:
- built-in admin
- built-in authentication and permissions
- strong CRUD and form handling
- mature ORM with PostgreSQL
- faster MVP delivery
```

## 7. Airbnb Integration Strategy

```text
Preferred production path:
Airbnb -> official software-connected integration -> our PMS

Fastest practical path for a new PMS:
Airbnb -> approved channel manager -> our PMS

Fallback only:
Airbnb iCal sync -> block availability dates
```

## 8. Booking Import Flow

```text
1. Booking arrives on Airbnb
2. Airbnb-connected software sends or exposes the reservation data
3. Our OTA integration layer receives it
4. A sync worker validates and normalizes the booking
5. The reservation is saved in PostgreSQL
6. Django shows it in the dashboard, calendar, and reservation screens
```
