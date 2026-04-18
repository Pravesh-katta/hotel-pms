# Django Project Structure

---

## Full Folder Layout

```text
hotel-pms/
├── hotel_pms/                      # Django project config
│   ├── __init__.py
│   ├── settings/
│   │   ├── __init__.py
│   │   ├── base.py                 # Shared settings
│   │   ├── local.py                # Local dev overrides
│   │   └── production.py           # GCP production settings
│   ├── urls.py                     # Root URL config
│   ├── wsgi.py
│   └── asgi.py
│
├── apps/
│   ├── hotels/                     # Hotel (tenant) management
│   │   ├── models.py               # Hotel, OTAConnection
│   │   ├── admin.py                # Django admin registration
│   │   ├── views.py
│   │   ├── serializers.py          # DRF serializers
│   │   ├── urls.py
│   │   └── tests/
│   │
│   ├── accounts/                   # User, StaffProfile, auth
│   │   ├── models.py               # StaffProfile (extends User)
│   │   ├── admin.py
│   │   ├── middleware.py           # HotelMiddleware (sets request.hotel)
│   │   ├── mixins.py              # HotelScopedMixin for views
│   │   ├── decorators.py          # @role_required
│   │   ├── views.py               # Login, logout, profile
│   │   ├── urls.py
│   │   └── tests/
│   │
│   ├── rooms/                      # Room, RoomType, availability
│   │   ├── models.py               # RoomType, Room
│   │   ├── admin.py
│   │   ├── views.py
│   │   ├── availability.py         # Availability check logic (calendar uses this)
│   │   ├── serializers.py
│   │   ├── urls.py
│   │   └── tests/
│   │
│   ├── rates/                      # Rate plans, seasonal pricing
│   │   ├── models.py               # RatePlan, RatePlanRate, SeasonalRate, RoomNightRate
│   │   ├── admin.py
│   │   ├── views.py               # Rate plan CRUD for hotel admin
│   │   ├── services.py            # get_rate() — rate resolution logic
│   │   ├── urls.py
│   │   └── tests/
│   │
│   ├── guests/                     # Guest profiles + verification
│   │   ├── models.py               # Guest, GuestVerification
│   │   ├── admin.py
│   │   ├── views.py
│   │   ├── verification.py        # Form A/C generation, police report filing
│   │   ├── serializers.py
│   │   ├── urls.py
│   │   └── tests/
│   │
│   ├── reservations/               # Bookings, check-in/out
│   │   ├── models.py               # Reservation, ReservationRoom
│   │   ├── admin.py
│   │   ├── views.py
│   │   ├── services.py            # Booking logic, availability check, OTA dedup
│   │   ├── workflows.py           # Check-in, check-out, walk-in, cancellation flows
│   │   ├── state_machine.py       # Reservation status transitions (enforced)
│   │   ├── serializers.py
│   │   ├── urls.py
│   │   └── tests/
│   │
│   ├── billing/                    # Folios, charges, payments
│   │   ├── models.py               # Folio, FolioCharge
│   │   ├── admin.py
│   │   ├── views.py
│   │   ├── services.py            # Night audit, folio calculation
│   │   ├── serializers.py
│   │   ├── urls.py
│   │   └── tests/
│   │
│   ├── payments/                    # Razorpay integration, cash, refunds
│   │   ├── models.py               # Payment, HotelPaymentConfig
│   │   ├── admin.py
│   │   ├── views.py               # Payment page, webhook endpoint
│   │   ├── services.py            # Razorpay order creation, verification, refund
│   │   ├── webhooks.py            # Razorpay webhook handler
│   │   ├── gst.py                 # GST calculation logic
│   │   ├── invoice.py             # PDF invoice generation
│   │   ├── urls.py
│   │   └── tests/
│   │
│   ├── housekeeping/               # Room cleaning tasks
│   │   ├── models.py               # HousekeepingTask
│   │   ├── admin.py
│   │   ├── views.py
│   │   ├── urls.py
│   │   └── tests/
│   │
│   ├── reports/                    # Sales dashboard, reports, exports
│   │   ├── views.py               # Sales aggregation queries
│   │   ├── exports.py             # CSV export for all reports
│   │   ├── urls.py
│   │   └── tests/
│   │
│   ├── search/                     # Global search
│   │   ├── views.py               # Search across guests, reservations, rooms
│   │   └── urls.py
│   │
│   ├── notifications/              # WhatsApp, SMS, Email via MSG91
│   │   ├── models.py               # Notification, NotificationPreference
│   │   ├── services.py            # send_notification(), template rendering
│   │   ├── providers/
│   │   │   ├── msg91.py           # MSG91 API (WhatsApp + SMS)
│   │   │   └── email.py           # SendGrid / SES
│   │   ├── signals.py             # Auto-notify on booking, payment, checkout
│   │   ├── templates_msg/         # WhatsApp/SMS message templates
│   │   ├── views.py               # Notification settings page
│   │   ├── urls.py
│   │   └── tests/
│   │
│   ├── audit/                      # Audit logging
│   │   ├── models.py               # AuditLog
│   │   ├── signals.py             # Auto-log on model changes
│   │   ├── admin.py
│   │   └── tests/
│   │
│   └── tasks/                      # Background job endpoints
│       ├── views.py               # Night audit, OTA sync, cleanup
│       ├── urls.py
│       └── tests/
│
├── templates/
│   ├── base.html                   # Base layout (nav, sidebar, footer)
│   ├── registration/
│   │   ├── login.html
│   │   └── password_change.html
│   ├── dashboard/
│   │   ├── index.html              # Staff dashboard home
│   │   ├── components/
│   │   │   ├── sidebar.html
│   │   │   ├── navbar.html
│   │   │   ├── stats_cards.html
│   │   │   └── hotel_switcher.html  # For super_admin only
│   │   ├── reservations/
│   │   │   ├── list.html
│   │   │   ├── detail.html
│   │   │   ├── create.html
│   │   │   └── calendar.html
│   │   ├── rooms/
│   │   │   ├── list.html
│   │   │   └── status_board.html
│   │   ├── guests/
│   │   │   ├── list.html
│   │   │   └── detail.html
│   │   ├── billing/
│   │   │   ├── folio_list.html
│   │   │   └── folio_detail.html
│   │   ├── housekeeping/
│   │   │   └── board.html
│   │   ├── reports/
│   │   │   └── sales.html          # Hotel-level sales (manager+)
│   │   └── staff/
│   │       └── list.html
│   ├── emails/                     # Email templates
│   │   ├── base_email.html         # Base layout (logo, footer)
│   │   ├── booking_confirmation.html
│   │   ├── checkin_reminder.html
│   │   ├── payment_receipt.html
│   │   ├── checkout_summary.html
│   │   ├── cancellation.html
│   │   ├── refund_processed.html
│   │   └── admin_weekly_report.html
│   ├── invoices/
│   │   └── invoice.html            # PDF invoice template (weasyprint)
│   └── admin/                      # Django admin template overrides
│       └── sales_dashboard.html    # Super admin cross-hotel sales
│
├── static/
│   ├── css/
│   │   └── dashboard.css
│   ├── js/
│   │   ├── htmx.min.js            # HTMX for interactivity
│   │   └── charts.js              # Chart.js for sales graphs
│   └── images/
│       └── logo.png
│
├── docs/
│   ├── architecture.md
│   ├── database-schema.md
│   ├── admin-panel.md
│   ├── gcp-deployment.md
│   └── project-structure.md        # This file
│
├── infra/                          # Terraform — automated GCP setup
│   ├── main.tf                     # Provider, project config
│   ├── cloud_run.tf                # Cloud Run service, scaling, domain
│   ├── cloud_sql.tf                # PostgreSQL instance, DB, user
│   ├── storage.tf                  # Cloud Storage bucket
│   ├── secrets.tf                  # Secret Manager
│   ├── scheduler.tf                # Cloud Scheduler jobs
│   ├── artifact_registry.tf        # Docker image registry
│   ├── iam.tf                      # Service accounts, permissions
│   ├── github_wif.tf               # Workload Identity Federation
│   ├── variables.tf                # Input variables
│   ├── outputs.tf                  # Output values
│   └── terraform.tfvars            # Your values (gitignored)
│
├── .github/
│   └── workflows/
│       └── deploy.yml              # GitHub Actions CI/CD pipeline
│
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env.example
├── .gitignore
├── manage.py
└── README.md
```

---

## URL Routing Structure

```text
/                                → Redirect to /dashboard/ or /accounts/login/
/accounts/login/                 → Login page
/accounts/logout/                → Logout

/dashboard/                      → Staff dashboard home
/dashboard/reservations/         → Reservation list
/dashboard/reservations/create/  → New reservation (pre-booked)
/dashboard/reservations/walk-in/ → Walk-in quick booking (availability → guest → pay → check-in)
/dashboard/reservations/:id/     → Reservation detail
/dashboard/reservations/:id/check-in/  → Check-in flow
/dashboard/reservations/:id/check-out/ → Check-out flow
/dashboard/reservations/:id/cancel/    → Cancellation flow
/dashboard/calendar/             → Room availability calendar
/dashboard/rooms/                → Room list
/dashboard/guests/               → Guest list
/dashboard/billing/              → Billing / folios
/dashboard/billing/:id/pay/      → Collect payment (opens Razorpay checkout)
/dashboard/billing/:id/cash/     → Record cash/manual payment
/dashboard/billing/:id/refund/   → Process refund
/dashboard/billing/:id/invoice/  → Download PDF invoice
/dashboard/calendar/             → Room grid calendar (primary — rooms × dates)
/dashboard/calendar/monthly/     → Monthly overview (occupancy per day)
/dashboard/rates/                → Rate plans list (hotel_admin+)
/dashboard/rates/create/         → Create rate plan
/dashboard/rates/:id/            → Edit rate plan + room prices + seasonal
/dashboard/housekeeping/         → Housekeeping board
/dashboard/reports/              → Reports (manager+)
/dashboard/reports/sales/        → Sales report (manager+)
/dashboard/reports/night-audit/:date/ → Night audit results
/dashboard/reports/occupancy/    → Occupancy report
/dashboard/reports/gst/          → GST report (for filing)
/dashboard/staff/                → Staff management (hotel_admin+)
/dashboard/settings/             → Hotel settings (hotel_admin+)
/dashboard/settings/notifications/ → Notification preferences
/dashboard/settings/ota/         → OTA connections (add/edit/test Airbnb, Booking.com, etc.)
/dashboard/settings/ota/:id/test/→ Test OTA connection
/dashboard/settings/ota/:id/sync/→ Manual sync trigger

/api/v1/reservations/            → DRF API (for future mobile app / OTA integration)
/api/v1/rooms/
/api/v1/guests/
/api/v1/availability/

/api/webhooks/razorpay/          → Razorpay payment webhook (Razorpay calls this)

/api/tasks/night-audit/          → Cloud Scheduler endpoint (internal only)
/api/tasks/ota-sync/             → Cloud Scheduler endpoint (internal only)

/superadmin/                     → Django admin (super_admin only)
/health/                         → Health check for Cloud Run
```

---

## Key Design Decisions

```text
1. Split settings (base/local/production)
   - No environment conditionals in a single settings file
   - Local uses SQLite or Docker PostgreSQL, production uses Cloud SQL

2. Apps are self-contained
   - Each app has its own models, views, urls, tests
   - Cross-app logic lives in services.py (e.g., reservation + billing)

3. Templates over SPA
   - HTMX for partial page updates (search, filters, status toggles)
   - No React/Vue build step
   - Faster to build, simpler to deploy

4. DRF API exists alongside templates
   - /dashboard/ routes serve HTML (staff use)
   - /api/v1/ routes serve JSON (OTA integration, future mobile app)
   - Both use the same models and permission checks

5. Background tasks via Cloud Scheduler
   - No Celery, no RabbitMQ — too heavy for this scale
   - Cloud Scheduler calls Django endpoints directly via HTTP
   - Simpler infrastructure, lower cost

6. Fully automated infrastructure
   - Terraform creates all GCP resources (one command)
   - GitHub Actions handles CI/CD (lint → test → build → deploy)
   - No manual deploys, no clicking in GCP Console
   - Infrastructure changes are version-controlled in git

7. SSL & domain automated
   - GCP provides free managed SSL certificate
   - Custom domain mapped via Terraform
   - No IP addresses, no manual certificate management
```
