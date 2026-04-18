# Notification System Architecture

India-specific: SMS + WhatsApp are primary. Email is secondary.

---

## 1. Channels

```text
┌──────────────────────────────────────────────────────────────┐
│                   NOTIFICATION CHANNELS                       │
│                                                              │
│  ┌──────────────────────────────────────────────────┐        │
│  │  1. WhatsApp (Primary for guests)                │        │
│  │     Provider: WhatsApp Business API via           │        │
│  │               Interakt / Wati / Gupshup           │        │
│  │     Why: 95%+ of Indian hotel guests use WhatsApp │        │
│  │     Cost: ₹0.50 - ₹1.00 per message              │        │
│  └──────────────────────────────────────────────────┘        │
│                                                              │
│  ┌──────────────────────────────────────────────────┐        │
│  │  2. SMS (Fallback for guests without WhatsApp)    │        │
│  │     Provider: MSG91 or Twilio                     │        │
│  │     Why: Required for OTP, works without internet │        │
│  │     Cost: ₹0.15 - ₹0.25 per SMS                  │        │
│  │     Note: Needs DLT registration (TRAI mandate)   │        │
│  └──────────────────────────────────────────────────┘        │
│                                                              │
│  ┌──────────────────────────────────────────────────┐        │
│  │  3. Email (Secondary)                             │        │
│  │     Provider: SendGrid or Amazon SES              │        │
│  │     Why: Invoices, formal confirmations, receipts │        │
│  │     Cost: Minimal (free tier covers this scale)   │        │
│  └──────────────────────────────────────────────────┘        │
│                                                              │
│  ┌──────────────────────────────────────────────────┐        │
│  │  4. In-App (For staff)                            │        │
│  │     No external provider needed                   │        │
│  │     Dashboard notifications for new bookings,     │        │
│  │     OTA sync alerts, payment confirmations         │        │
│  └──────────────────────────────────────────────────┘        │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

---

## 2. Recommended Provider: MSG91

```text
Why MSG91 (over Twilio for India):

  - Indian company, servers in India (lower latency)
  - Handles both SMS + WhatsApp from one API
  - DLT registration support built-in (mandatory for Indian SMS)
  - Pre-approved templates for hospitality
  - Cheaper than Twilio for Indian numbers
  - Good Django/Python SDK
  - Pay-as-you-go pricing

Pricing:
  SMS:      ₹0.15 - ₹0.20 per message
  WhatsApp: ₹0.50 - ₹0.80 per message (conversation-based)

Monthly estimate (20 hotels × ~750 bookings/month):
  WhatsApp: ~2,250 messages × ₹0.70 = ~₹1,575/month
  SMS:      ~500 messages × ₹0.18   = ~₹90/month
  Total:    ~₹1,665/month (~$20)
```

---

## 3. What Triggers What

### Guest Notifications (WhatsApp + SMS fallback)

```text
Trigger                    │ Channel   │ Message
───────────────────────────┼───────────┼──────────────────────────────
Booking confirmed          │ WhatsApp  │ Confirmation + dates + hotel address + map link
Check-in reminder          │ WhatsApp  │ 1 day before: "Your room is ready tomorrow"
Payment received           │ WhatsApp  │ "₹X,XXX received. Balance: ₹X,XXX"
Invoice / Receipt          │ WhatsApp  │ PDF invoice attached
Check-out summary          │ WhatsApp  │ "Thank you for staying. Total: ₹X,XXX"
Cancellation confirmed     │ WhatsApp  │ "Booking cancelled. Refund of ₹X,XXX initiated"
Refund processed           │ WhatsApp  │ "Refund of ₹X,XXX will reflect in 5-7 days"

If WhatsApp delivery fails → auto-fallback to SMS (shorter message)
If no phone number         → send email only
```

### Staff Notifications (In-App + optional WhatsApp)

```text
Trigger                    │ Channel   │ Who receives
───────────────────────────┼───────────┼──────────────────────────────
New OTA booking arrives    │ In-App    │ Front desk staff
Booking cancelled          │ In-App    │ Front desk staff
Payment received           │ In-App    │ Front desk + manager
Payment failed             │ In-App    │ Front desk + manager
Night audit completed      │ In-App    │ Manager + hotel admin
Night audit failed         │ WhatsApp  │ Hotel admin (urgent)
OTA sync error             │ WhatsApp  │ Hotel admin (urgent)
Guest no-show              │ In-App    │ Front desk + manager
Low occupancy alert        │ In-App    │ Manager (< 30% occupancy)
```

### Admin Notifications (WhatsApp / Email)

```text
Trigger                    │ Channel   │ Who receives
───────────────────────────┼───────────┼──────────────────────────────
Daily sales summary        │ WhatsApp  │ Super admin (morning 7 AM)
Weekly revenue report      │ Email     │ Super admin (Monday 9 AM)
System error / downtime    │ WhatsApp  │ Super admin (immediate)
New hotel onboarded        │ Email     �� Super admin
```

---

## 4. Database Model

### Notification

| Column         | Type              | Notes                          |
|----------------|-------------------|--------------------------------|
| id             | PK                |                                |
| hotel          | FK → Hotel (null) | null for system-level           |
| recipient_type | enum              | guest, staff, admin             |
| recipient_phone| varchar(15) null  | Indian mobile (+91XXXXXXXXXX)  |
| recipient_email| email null        |                                |
| channel        | enum              | whatsapp, sms, email, in_app   |
| template_name  | varchar(100)      | e.g. "booking_confirmation"    |
| context_data   | jsonb             | Template variables (guest name, amount, dates, etc.) |
| status         | enum              | queued, sent, delivered, failed, read |
| external_id    | varchar(100) null | MSG91 message ID for tracking  |
| error_message  | text null         | If delivery failed              |
| related_model  | varchar(50) null  | e.g. "Reservation", "Payment"  |
| related_id     | varchar(50) null  | PK of related record            |
| created_at     | datetime          |                                |
| sent_at        | datetime null     |                                |
| delivered_at   | datetime null     |                                |

### NotificationPreference (per hotel)

| Column              | Type              | Notes                          |
|---------------------|-------------------|--------------------------------|
| id                  | PK                |                                |
| hotel               | OneToOne → Hotel  |                                |
| whatsapp_enabled    | bool default true |                                |
| sms_enabled         | bool default true |                                |
| email_enabled       | bool default true |                                |
| send_booking_confirm| bool default true |                                |
| send_checkin_reminder| bool default true|                                |
| send_payment_receipt| bool default true |                                |
| send_checkout_summary| bool default true|                                |
| staff_whatsapp_alerts| bool default false| WhatsApp alerts for staff     |
| daily_summary_enabled| bool default true | Morning summary to admin      |
| created_at          | datetime          |                                |

---

## 5. Message Templates

WhatsApp Business API requires pre-approved templates. These are registered with MSG91/Meta.

### Booking Confirmation

```text
Template name: booking_confirmation
Channel: WhatsApp

Message:
  🏨 *Booking Confirmed*

  Hello {{guest_name}},

  Your booking at *{{hotel_name}}* is confirmed.

  📅 Check-in: {{check_in_date}}
  📅 Check-out: {{check_out_date}}
  🛏️ Room: {{room_type}}
  💰 Total: ₹{{total_amount}}
  🔖 Booking ID: {{confirmation_number}}

  📍 {{hotel_address}}
  📞 {{hotel_phone}}

  For any queries, reply to this message.
```

### Payment Receipt

```text
Template name: payment_receipt
Channel: WhatsApp

Message:
  ✅ *Payment Received*

  Hello {{guest_name}},

  We've received your payment of *₹{{amount}}* via {{method}}.

  🔖 Booking: {{confirmation_number}}
  💰 Paid: ₹{{paid_amount}}
  💰 Balance: ₹{{balance}}

  Thank you!
  *{{hotel_name}}*
```

### Check-in Reminder

```text
Template name: checkin_reminder
Channel: WhatsApp

Message:
  👋 *Arriving Tomorrow!*

  Hello {{guest_name}},

  Your room at *{{hotel_name}}* is ready for tomorrow.

  📅 Check-in: {{check_in_date}}
  🕐 Check-in time: 12:00 PM onwards
  🛏️ Room: {{room_type}}

  📍 {{hotel_address}}
  📍 Google Maps: {{map_link}}

  Please carry a valid ID (Aadhar/Passport).

  See you tomorrow! 🙏
```

### Checkout Summary

```text
Template name: checkout_summary
Channel: WhatsApp

Message:
  🙏 *Thank You for Staying!*

  Hello {{guest_name}},

  Thank you for staying at *{{hotel_name}}*.

  📋 Invoice: {{folio_number}}
  💰 Total: ₹{{total_amount}}
  ✅ Paid: ₹{{paid_amount}}

  Your invoice is attached below.

  We hope to see you again! ⭐
```

---

## 6. SMS DLT Registration (Indian Regulatory Requirement)

```text
TRAI (Telecom Regulatory Authority of India) requires:

  1. Register as an enterprise on DLT platform
     (JioTrueCaller DLT / Vodafone DLT / Airtel DLT)

  2. Register sender ID (e.g., "HTLPMS")

  3. Register each SMS template with exact text
     Variables marked as {#var#}

  4. Get template ID for each message

  Without DLT registration, SMS will NOT be delivered in India.

  MSG91 helps with this process — they handle the DLT submission.
  Takes 3-7 days for approval.

  Example registered SMS template:
    "Your booking {#var#} at {#var#} is confirmed. Check-in: {#var#}. 
     Total: Rs.{#var#}. - HTLPMS"
```

---

## 7. Implementation Flow

```text
Booking is created
      │
      ▼
Django signal fires: reservation_confirmed
      │
      ▼
Notification service called:
  send_notification(
    hotel=hotel,
    template="booking_confirmation",
    recipient_phone=guest.phone,
    context={guest_name, hotel_name, dates, amount, ...}
  )
      │
      ▼
Create Notification record (status=queued)
      │
      ▼
Check NotificationPreference for this hotel
  - WhatsApp enabled? → Send via MSG91 WhatsApp API
  - SMS enabled?      → Queue as fallback
  - Email enabled?    → Send email via SendGrid
      │
      ▼
MSG91 API call (async, non-blocking)
      │
      ├── Success → Update status=sent, store external_id
      │              MSG91 webhook later updates → delivered/read
      │
      └── Failure → Update status=failed, store error
                     Retry once via SMS if WhatsApp failed
```

### Async Delivery

```text
Notifications are sent asynchronously so they don't slow down the UI.

For our scale (20 hotels, ~50-100 notifications/day):
  - Django signals trigger notification creation
  - Cloud Scheduler polls every 1 minute for queued notifications
  - Or: send inline (fast enough for this volume, simpler)

  No Celery needed. Either:
  a) Send inline in the view (adds ~200ms to response, acceptable)
  b) Cloud Scheduler polls /api/tasks/send-notifications/ every minute
```

---

## 8. Notification Settings in Admin Panel

```text
Hotel Admin can configure at:
  /dashboard/settings/notifications/

  ┌──────────────────────────────────────────┐
  │  NOTIFICATION SETTINGS                    │
  │                                          │
  │  Guest Notifications:                    │
  │  ☑ Booking confirmation (WhatsApp + SMS) │
  │  ☑ Check-in reminder (1 day before)      │
  │  ☑ Payment receipt                       │
  │  ☑ Checkout summary + invoice            │
  │  ☑ Cancellation confirmation             │
  │                                          │
  │  Staff Alerts:                           │
  │  ☑ New OTA booking (in-app)              │
  │  ☑ Payment received (in-app)             │
  │  ☐ Urgent alerts via WhatsApp            │
  │                                          │
  │  Admin Reports:                          │
  │  ☑ Daily sales summary (WhatsApp 7 AM)   │
  │  ☑ Weekly report (Email Monday 9 AM)     │
  │                                          │
  └──────────────────────────────────────────┘
```

---

## 9. Cost Estimate

```text
20 hotels × ~750 bookings/month = ~15,000 bookings/month

Notifications per booking: ~3 (confirmation + payment + checkout)
Total messages/month: ~45,000

WhatsApp (80%): 36,000 × ₹0.70  = ₹25,200
SMS (15%):       6,750 × ₹0.18  = ₹1,215
Email (5%):      2,250 × free   = ₹0

Total: ~₹26,415/month (~$32/month)

Note: This is across ALL 20+ hotels combined.
Per hotel: ~₹1,300/month (~$16/month)
```
