# Database Schema Design

Constraints: 20+ hotels, 11-15 rooms per hotel (~250-300 rooms total), single PostgreSQL database, shared schema with `hotel_id` FK.

---

## Entity Relationship Overview

```text
Hotel
 ├── Room (status: available/occupied/dirty/maintenance/blocked)
 ├── RoomType
 ├── RatePlan
 │    ├── RatePlanRate
 │    │    └── SeasonalRate
 ├── Staff (User + StaffProfile)
 ├── Guest
 │    ├── GuestVerification (Form A, Form C, police intimation)
 │    └── ID document photos (Cloud Storage)
 ├── Reservation (confirmed → checked_in → checked_out | cancelled | no_show)
 │    ├── ReservationRoom
 │    │    └── RoomNightRate (per-night rate snapshot)
 │    └── Folio (open → settled | void)
 │         ├── FolioCharge (room, GST, misc, cancellation_fee, no_show_fee)
 │         └── Payment (Razorpay/cash/UPI — with refund linking)
 ├── HotelPaymentConfig (Razorpay public key, GSTIN, GST rate)
 ├── NotificationPreference
 ├── Notification
 ├── HousekeepingTask
 ├── DailyAuditSnapshot (night audit results)
 ├── OTAConnection
 └── AuditLog

Total: 22 tables
```

---

## 1. Hotel (Core Tenant)

Every hotel-scoped model links back here.

| Column         | Type         | Notes                          |
|----------------|--------------|--------------------------------|
| id             | UUID / PK    | Primary key                    |
| name           | varchar(200) |                                |
| code           | varchar(10)  | Short code, unique (e.g. "MUM01") |
| address        | text         |                                |
| city           | varchar(100) |                                |
| state          | varchar(100) |                                |
| country        | varchar(100) |                                |
| phone          | varchar(20)  |                                |
| email          | email        |                                |
| currency       | varchar(3)   | Default: INR (all hotels in India) |
| timezone       | varchar(50)  | e.g. "Asia/Kolkata"            |
| max_rooms      | int          | Cap at 15                      |
| is_active      | bool         | Soft enable/disable             |
| created_at     | datetime     |                                |
| updated_at     | datetime     |                                |

---

## 2. RoomType

Shared per hotel — e.g. "Deluxe", "Suite", "Standard".

| Column         | Type         | Notes                          |
|----------------|--------------|--------------------------------|
| id             | PK           |                                |
| hotel          | FK → Hotel   |                                |
| name           | varchar(100) | e.g. "Deluxe Double"           |
| description    | text         |                                |
| base_rate      | decimal(10,2)| Default nightly rate            |
| max_occupancy  | int          |                                |
| created_at     | datetime     |                                |

**Unique constraint:** `(hotel, name)`

---

## 3. Room

| Column         | Type             | Notes                          |
|----------------|------------------|--------------------------------|
| id             | PK               |                                |
| hotel          | FK → Hotel       |                                |
| room_type      | FK → RoomType    |                                |
| room_number    | varchar(10)      | e.g. "101", "A-12"             |
| floor          | varchar(10)      |                                |
| status         | enum             | available, occupied, dirty, maintenance, blocked |
| is_active      | bool             |                                |
| created_at     | datetime         |                                |

**Unique constraint:** `(hotel, room_number)`

---

## 4. Guest

| Column           | Type           | Notes                          |
|------------------|----------------|--------------------------------|
| id               | PK             |                                |
| hotel            | FK → Hotel     | Guest belongs to hotel that created them |
| first_name       | varchar(100)   |                                |
| last_name        | varchar(100)   |                                |
| email            | email (nullable)|                               |
| phone            | varchar(20)    | At least one of phone/email required (app-level) |
| id_type          | enum           | passport, aadhar, driving_license, voter_id, other |
| id_number        | varchar(50)    |                                |
| id_document_front| varchar(500) null | Cloud Storage path to front photo |
| id_document_back | varchar(500) null | Cloud Storage path to back photo  |
| nationality      | varchar(100)   | "Indian" or country name        |
| is_foreign       | bool default false | Auto-set from nationality. Triggers Form C requirement. |
| date_of_birth    | date (nullable)|                                |
| gender           | enum (nullable)| male, female, other             |
| address          | text           |                                |
| city             | varchar(100) null |                              |
| state            | varchar(100) null |                              |
| country          | varchar(100) null |                              |
| pincode          | varchar(10) null  |                              |
| notes            | text           | Internal notes                  |
| created_at       | datetime       |                                |

---

## 4a. GuestVerification (Police / Form C)

Tracks police verification and Form C filing for every check-in. Mandatory in India.

| Column              | Type              | Notes                          |
|---------------------|-------------------|--------------------------------|
| id                  | PK                |                                |
| guest               | FK → Guest        |                                |
| reservation         | FK → Reservation  | Which stay this verification is for |
| hotel               | FK → Hotel        |                                |
| form_type           | enum              | form_a, form_c, police_intimation |
| status              | enum              | pending, submitted, verified, rejected |
| submission_date     | date (nullable)   | When submitted to authorities   |
| reference_number    | varchar(100) null | Police report / FRRO reference  |
| submitted_by        | FK → User (null)  | Staff who submitted             |
| verified_date       | date (nullable)   | When authorities confirmed      |
| notes               | text null         |                                |
| created_at          | datetime          |                                |

```text
Rules:
  - Form A: Required for ALL guests at check-in (basic registration)
  - Form C: Required for ALL foreign guests within 24 hours of check-in
  - Police intimation: Required in some states for all guests

  Auto-created:
    When reservation.status changes to 'checked_in':
      → If guest.is_foreign = true → create GuestVerification(form_type='form_c', status='pending')
      → Always create GuestVerification(form_type='form_a', status='pending')

  Dashboard alert:
    Show pending verifications prominently on staff dashboard.
    "⚠ 2 Form C submissions pending (overdue > 24 hours)"
```

---

## 5. Reservation

| Column              | Type              | Notes                          |
|---------------------|-------------------|--------------------------------|
| id                  | PK                |                                |
| hotel               | FK → Hotel        |                                |
| confirmation_number | varchar(20)       | Auto-generated, unique per hotel |
| guest               | FK → Guest        |                                |
| check_in_date       | date              |                                |
| check_out_date      | date              |                                |
| status              | enum              | confirmed, checked_in, checked_out, cancelled, no_show |
| source              | enum              | walk_in, phone, website, airbnb, booking_com, ota_other |
| external_booking_id | varchar(100) null | OTA reference ID (for dedup)    |
| num_adults          | int               |                                |
| num_children        | int               | default 0                       |
| special_requests    | text              |                                |
| created_by          | FK → User (nullable) | Staff who created it         |
| created_at          | datetime          |                                |
| updated_at          | datetime          |                                |

**Unique constraint:** `(hotel, confirmation_number)`
**Unique constraint:** `(hotel, external_booking_id)` — prevents OTA double-booking

---

## 6. ReservationRoom

Links reservations to specific rooms (a reservation can have multiple rooms).

| Column         | Type              | Notes                          |
|----------------|-------------------|--------------------------------|
| id             | PK                |                                |
| reservation    | FK → Reservation  |                                |
| room           | FK → Room         |                                |
| room_type      | FK → RoomType     | What was booked (in case room changes) |
| rate_plan      | FK → RatePlan (null) | Which rate plan was applied   |
| check_in_date  | date              | Can differ from reservation dates |
| check_out_date | date              |                                |

**Note:** Per-night rates are stored in **RoomNightRate** (see 10c), NOT on this table.
Each night can have a different rate (seasonal pricing, mid-stay rate changes).

**Unique constraint:** `(room, check_in_date, check_out_date)` — prevents double-booking at DB level

**PostgreSQL exclusion constraint (stronger double-booking prevention):**
```sql
EXCLUDE USING gist (
  room_id WITH =,
  daterange(check_in_date, check_out_date) WITH &&
) WHERE (reservation.status IN ('confirmed', 'checked_in'))
```
This makes double-booking physically impossible even under concurrent writes.

---

## 7. Folio (Invoice per Reservation)

Each reservation gets one folio. This is what the guest pays.

| Column         | Type              | Notes                          |
|----------------|-------------------|--------------------------------|
| id             | PK                |                                |
| hotel          | FK → Hotel        |                                |
| reservation    | FK → Reservation (OneToOne) |                       |
| folio_number   | varchar(20)       | Auto-generated                  |
| total_charges  | decimal(12,2)     | SUM of FolioCharge amounts      |
| total_payments | decimal(12,2)     | SUM of Payment amounts (completed) |
| balance        | decimal(12,2)     | total_charges - total_payments  |
| status         | enum              | open, settled, void             |
| created_at     | datetime          |                                |
| closed_at      | datetime (nullable)|                               |

---

## 8. FolioCharge

Individual charge line items on a folio. Payments are tracked separately (see Payment model).

| Column         | Type              | Notes                          |
|----------------|-------------------|--------------------------------|
| id             | PK                |                                |
| folio          | FK → Folio        |                                |
| charge_type    | enum              | room_charge, cgst, sgst, igst, food_beverage, laundry, minibar, misc, discount, cancellation_fee, no_show_fee |
| description    | varchar(200)      |                                |
| amount         | decimal(10,2)     | Positive = charge, negative = discount |
| charge_date    | date              | Which night/day this applies to |
| created_by     | FK → User (nullable) |                              |
| created_at     | datetime          |                                |

Note: GST is posted as separate FolioCharge entries (cgst + sgst or igst)
so the invoice shows the legal breakup.

---

## 8a. Payment

Tracks all payments against a folio — both online (Razorpay) and offline (cash/bank transfer).

| Column              | Type              | Notes                          |
|---------------------|-------------------|--------------------------------|
| id                  | PK                |                                |
| hotel               | FK → Hotel        |                                |
| folio               | FK → Folio        |                                |
| amount              | decimal(10,2)     | In INR (rupees)                |
| method              | enum              | upi, credit_card, debit_card, net_banking, wallet, cash, bank_transfer, corporate |
| status              | enum              | pending, completed, failed, refunded |
| razorpay_order_id   | varchar(50) null  | Razorpay order ID (null for cash/manual) |
| razorpay_payment_id | varchar(50) null  | Razorpay payment ID            |
| razorpay_signature  | varchar(200) null | For verification                |
| reference_number    | varchar(100) null | For manual payments (receipt #, UTR, etc.) |
| original_payment    | FK → Payment (null) | Links refund to original payment |
| refund_reason       | varchar(200) null | Why refund was issued           |
| notes               | text null         | E.g. "Cash paid at check-in"   |
| received_by         | FK → User (null)  | Staff who processed it         |
| created_at          | datetime          |                                |

---

## 8b. HotelPaymentConfig

Per-hotel payment and GST settings.

| Column                   | Type              | Notes                          |
|--------------------------|-------------------|--------------------------------|
| id                       | PK                |                                |
| hotel                    | OneToOne → Hotel  |                                |
| razorpay_key_id          | varchar(50)       | Public key (safe to store in DB) |
| razorpay_account_id      | varchar(50) null  | For Razorpay Route (sub-merchant) |
| gst_number               | varchar(20)       | Hotel's GSTIN                  |
| gst_rate                 | decimal(4,2)      | Default GST % (12.00 or 18.00) |
| sac_code                 | varchar(10) default '9963' | HSN/SAC code for hotel accommodation |
| accepts_online_payment   | bool              | Enable/disable Razorpay        |
| created_at               | datetime          |                                |

```text
SECRET STORAGE RULES:
  razorpay_key_id     → stored in DB (it's a public key, safe)
  razorpay_key_secret → NEVER in DB. Stored in GCP Secret Manager only.
                        Fetched at runtime: secretmanager.access("razorpay_secret_{hotel_id}")
  razorpay_webhook_secret → NEVER in DB. Stored in GCP Secret Manager.

  Why: DB backups, developer access, and SQL injection could expose secrets.
  Secret Manager provides encryption, access control, and audit logging.
```

---

## 9. Staff / User Model

Extends Django's built-in User.

| Column         | Type              | Notes                          |
|----------------|-------------------|--------------------------------|
| id             | PK                |                                |
| user           | OneToOne → Django User |                             |
| hotel          | FK → Hotel (nullable) | null = super admin (sees all hotels) |
| role           | enum              | super_admin, hotel_admin, front_desk, housekeeping, manager |
| phone          | varchar(20)       |                                |
| is_active      | bool              |                                |

**Access rules:**
- `super_admin` — sees all hotels, sees sales across all hotels
- `hotel_admin` — sees only their hotel, sees their hotel's sales
- `front_desk` — reservations, check-in/out, guest management
- `housekeeping` — room status updates only
- `manager` — everything for their hotel including reports

---

## 10. RatePlan

See [rate-management.md](rate-management.md) for full pricing logic.

| Column                        | Type              | Notes                          |
|-------------------------------|-------------------|--------------------------------|
| id                            | PK                |                                |
| hotel                         | FK → Hotel        |                                |
| name                          | varchar(100)      | e.g. "Standard", "Airbnb Rate" |
| plan_type                     | enum              | standard, ota, corporate, promotional, long_stay |
| source                        | enum (nullable)   | walk_in, airbnb, booking_com, etc. |
| is_default                    | bool              | One default per hotel           |
| is_active                     | bool              |                                |
| priority                      | int               | Higher wins if multiple match   |
| min_stay_nights               | int default 1     |                                |
| cancellation_policy           | enum              | free, moderate, strict, non_refundable |
| cancellation_hours            | int default 24    |                                |
| cancellation_charge_percent   | decimal(4,2) default 0 |                            |
| created_at                    | datetime          |                                |

## 10a. RatePlanRate

| Column           | Type              | Notes                          |
|------------------|-------------------|--------------------------------|
| id               | PK                |                                |
| rate_plan        | FK → RatePlan     |                                |
| room_type        | FK → RoomType     |                                |
| base_rate        | decimal(10,2)     | INR per night                  |
| extra_adult_rate | decimal(10,2) default 0 |                            |
| extra_child_rate | decimal(10,2) default 0 |                            |

**Unique constraint:** `(rate_plan, room_type)`

## 10b. SeasonalRate

| Column           | Type              | Notes                          |
|------------------|-------------------|--------------------------------|
| id               | PK                |                                |
| rate_plan_rate   | FK → RatePlanRate |                                |
| name             | varchar(100)      | e.g. "Diwali Peak"            |
| start_date       | date              |                                |
| end_date         | date              |                                |
| rate             | decimal(10,2)     | Overrides base_rate            |

## 10c. RoomNightRate

Per-night rate snapshot locked at booking time.

| Column            | Type              | Notes                          |
|-------------------|-------------------|--------------------------------|
| id                | PK                |                                |
| reservation_room  | FK → ReservationRoom |                             |
| date              | date              | Specific night                 |
| rate              | decimal(10,2)     | Rate for this night in INR     |

**Unique constraint:** `(reservation_room, date)`

---

## 10d. Notification

See [notifications.md](notifications.md) for full notification system.

| Column         | Type              | Notes                          |
|----------------|-------------------|--------------------------------|
| id             | PK                |                                |
| hotel          | FK → Hotel (null) |                                |
| recipient_type | enum              | guest, staff, admin             |
| recipient_phone| varchar(15) null  |                                |
| recipient_email| email null        |                                |
| channel        | enum              | whatsapp, sms, email, in_app   |
| template_name  | varchar(100)      | e.g. "booking_confirmation"    |
| context_data   | jsonb             | Template variables              |
| status         | enum              | queued, sent, delivered, failed |
| external_id    | varchar(100) null | MSG91 message ID                |
| error_message  | text null         |                                |
| related_model  | varchar(50) null  |                                |
| related_id     | varchar(50) null  |                                |
| created_at     | datetime          |                                |
| sent_at        | datetime null     |                                |

## 10e. NotificationPreference

| Column                 | Type              | Notes                   |
|------------------------|-------------------|-------------------------|
| id                     | PK                |                         |
| hotel                  | OneToOne → Hotel  |                         |
| whatsapp_enabled       | bool default true |                         |
| sms_enabled            | bool default true |                         |
| email_enabled          | bool default true |                         |
| send_booking_confirm   | bool default true |                         |
| send_checkin_reminder  | bool default true |                         |
| send_payment_receipt   | bool default true |                         |
| send_checkout_summary  | bool default true |                         |

---

## 11. HousekeepingTask

| Column         | Type              | Notes                          |
|----------------|-------------------|--------------------------------|
| id             | PK                |                                |
| hotel          | FK → Hotel        |                                |
| room           | FK → Room         |                                |
| task_type      | enum              | cleaning, inspection, maintenance |
| status         | enum              | pending, in_progress, completed |
| assigned_to    | FK → User (nullable) |                              |
| notes          | text              |                                |
| created_at     | datetime          |                                |
| completed_at   | datetime (nullable)|                               |

---

## 11. AuditLog

| Column         | Type              | Notes                          |
|----------------|-------------------|--------------------------------|
| id             | PK                |                                |
| hotel          | FK → Hotel (nullable) | null for system-level actions |
| user           | FK → User (nullable)  |                              |
| action         | varchar(50)       | e.g. "reservation.created", "room.status_changed" |
| model_name     | varchar(100)      | e.g. "Reservation"              |
| object_id      | varchar(50)       | PK of the affected record       |
| changes        | jsonb             | Before/after snapshot           |
| ip_address     | inet (nullable)   |                                |
| created_at     | datetime          |                                |

---

## 12. DailyAuditSnapshot

Stores night audit results. One row per hotel per night.

| Column              | Type              | Notes                          |
|---------------------|-------------------|--------------------------------|
| id                  | PK                |                                |
| hotel               | FK → Hotel        |                                |
| audit_date          | date              | Which night was audited         |
| total_rooms         | int               |                                |
| occupied_rooms      | int               |                                |
| occupancy_percent   | decimal(5,2)      |                                |
| revenue_posted      | decimal(12,2)     | Room charges + GST posted tonight |
| total_outstanding   | decimal(12,2)     | Sum of all open folio balances  |
| noshow_count        | int               |                                |
| arrivals_tomorrow   | int               |                                |
| departures_tomorrow | int               |                                |
| audit_status        | enum              | completed, partial, failed      |
| error_message       | text null         |                                |
| completed_at        | datetime          |                                |

**Unique constraint:** `(hotel, audit_date)`

---

## 13. OTAConnection

Tracks which hotels connect to which OTAs. Admin enters all details via admin panel.

| Column              | Type              | Notes                          |
|---------------------|-------------------|--------------------------------|
| id                  | PK                |                                |
| hotel               | FK → Hotel        |                                |
| channel             | enum              | airbnb, booking_com, goibibo, makemytrip, agoda, expedia, other |
| connection_type     | enum              | direct_api, channel_manager, ical |
| channel_manager_name| varchar(100) null | e.g. "ChannelEx", "SiteMinder" (if using channel manager) |
| external_property_id| varchar(100)      | Property ID on the OTA          |
| api_key_id          | varchar(200) null | Public API key (stored in DB)   |
| ical_url            | varchar(500) null | iCal feed URL (for iCal sync)  |
| webhook_url         | varchar(500) null | Our webhook URL (shown to admin for OTA config) |
| sync_bookings       | bool default true | Sync reservations from this OTA |
| sync_rates          | bool default false| Push rates to this OTA          |
| sync_availability   | bool default true | Push availability to this OTA   |
| rate_plan           | FK → RatePlan null| Which rate plan to use for this OTA |
| is_active           | bool              |                                |
| last_sync_at        | datetime (null)   |                                |
| last_sync_error     | text null         | Last error message for debugging |
| sync_status         | enum              | ok, error, never_synced         |
| notes               | text null         | Admin notes about this connection |
| created_by          | FK → User         | Who set it up                   |
| created_at          | datetime          |                                |
| updated_at          | datetime          |                                |

```text
SECRET STORAGE:
  api_key_id       → safe to store in DB (public key)
  api_key_secret   → NEVER in DB. Stored in Secret Manager: "ota_secret_{hotel_id}_{channel}"
  Fetched at runtime when sync runs.

Admin provides these details in:
  Super Admin: /superadmin/ → OTA Connections
  Hotel Admin: /dashboard/settings/ota/

Admin panel shows:
  - Connection status (green/red indicator)
  - Last sync time
  - Last error (if any)
  - "Test Connection" button
  - "Sync Now" button (manual trigger)
```

---

## Key Indexes

```text
Room:                (hotel, status)              — dashboard room availability
Reservation:         (hotel, status)              — active reservations list
Reservation:         (hotel, check_in_date)       — calendar view
Reservation:         (hotel, external_booking_id) — OTA dedup lookup
ReservationRoom:     (room, check_in_date, check_out_date) — double-booking prevention
FolioCharge:         (folio, charge_date)         — nightly audit
Folio:               (hotel, status)              — open folios
Payment:             (hotel, status)              — pending payments
Payment:             (folio)                      — payments per folio
GuestVerification:   (hotel, status)              — pending Form C alerts
DailyAuditSnapshot:  (hotel, audit_date)          — night audit history
Notification:        (hotel, status)              — queued notifications
AuditLog:            (hotel, created_at)          — recent activity
```

---

## Sales Aggregation (Admin Dashboard)

Charges and payments are now in separate tables for cleaner queries.

```text
Revenue per hotel (charges):
  SELECT hotel_id, SUM(amount)
  FROM folio_charge
  JOIN folio ON folio.id = folio_charge.folio_id
  WHERE charge_type NOT IN ('discount')
    AND charge_date BETWEEN [date_range]
  GROUP BY hotel_id

GST collected per hotel:
  SELECT hotel_id, SUM(amount)
  FROM folio_charge
  JOIN folio ON folio.id = folio_charge.folio_id
  WHERE charge_type IN ('cgst', 'sgst', 'igst')
    AND charge_date BETWEEN [date_range]
  GROUP BY hotel_id

Collections per hotel (payments):
  SELECT hotel_id, SUM(amount)
  FROM payment
  WHERE status = 'completed'
    AND created_at BETWEEN [date_range]
  GROUP BY hotel_id

Collections by payment method:
  SELECT method, SUM(amount)
  FROM payment
  WHERE status = 'completed'
    AND created_at BETWEEN [date_range]
  GROUP BY method

Outstanding per hotel:
  Revenue - Collections
```

This is fast enough for 20 hotels × 13 rooms (~95K charges/year) without materialized views.
No need for a separate sales table — compute on the fly.
