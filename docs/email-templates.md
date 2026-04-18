# Email Templates

All emails share a common layout. Content changes per template.
Sent via SendGrid / Amazon SES. Also sent as WhatsApp (shorter version).

---

## 1. Base Email Layout

Every email wraps in this structure:

```text
┌──────────────────────────────────────────────────────────────┐
│                                                              │
│              ┌──────────────────────┐                        │
│              │    [Hotel Logo]       │                        │
│              │    Hotel Name         │                        │
│              └──────────────────────┘                        │
│                                                              │
│  ────────────────────────────────────────────────────────    │
│                                                              │
│              [ EMAIL CONTENT HERE ]                           │
│                                                              │
│  ────────────────────────────────────────────────────────    │
│                                                              │
│  {{hotel_name}}                                              │
│  {{hotel_address}}                                           │
│  📞 {{hotel_phone}}  |  ✉ {{hotel_email}}                   │
│                                                              │
│  ────────────────────────────────────────────────────────    │
│  This is an automated email. Please do not reply.            │
│  For queries, contact the hotel directly.                    │
│                                                              │
└──────────────────────────────────────────────────────────────┘

Implementation:
  templates/emails/base_email.html — Django template
  All email templates extend this base.
  Hotel logo, name, address, phone loaded from Hotel model.
```

---

## 2. Booking Confirmation Email

```text
Template: templates/emails/booking_confirmation.html
Trigger:  Reservation created (status = confirmed)
To:       Guest email
Subject:  Booking Confirmed — {{hotel_name}} | {{confirmation_number}}

┌──────────────────────────────────────────────────────────────┐
│                                                              │
│              [Hotel Logo]                                     │
│              Mumbai Seaside Hotel                             │
│                                                              │
│  ────────────────────────────────────────────────────────    │
│                                                              │
│  Dear {{guest_name}},                                        │
│                                                              │
│  Your booking has been confirmed! Here are your details:     │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  BOOKING DETAILS                                       │  │
│  │                                                        │  │
│  │  Confirmation #:  {{confirmation_number}}               │  │
│  │  Hotel:           {{hotel_name}}                        │  │
│  │  Room Type:       {{room_type}}                         │  │
│  │  Check-in:        {{check_in_date}} (12:00 PM onwards)  │  │
│  │  Check-out:       {{check_out_date}} (11:00 AM)         │  │
│  │  Guests:          {{num_adults}} Adults, {{num_children}} Children │
│  │  Nights:          {{num_nights}}                        │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  RATE SUMMARY                                          │  │
│  │                                                        │  │
│  │  Room charges:    ₹{{room_total}}                       │  │
│  │  GST ({{gst_percent}}%):       ₹{{gst_amount}}         │  │
│  │  ──────────────────────────────────                    │  │
│  │  Total:           ₹{{total_amount}}                     │  │
│  │  Paid:            ₹{{paid_amount}}                      │  │
│  │  Balance due:     ₹{{balance}}                          │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                              │
│  📍 HOTEL ADDRESS                                            │
│  {{hotel_address}}                                           │
│  {{hotel_city}}, {{hotel_state}} — {{hotel_pincode}}         │
│  📍 View on Google Maps: {{map_link}}                        │
│                                                              │
│  📋 THINGS TO BRING                                          │
│  • Valid photo ID (Aadhar Card / Passport / Driving License) │
│  • Foreign nationals: Please carry your Passport and Visa    │
│                                                              │
│  {{#if special_requests}}                                    │
│  📝 YOUR SPECIAL REQUESTS                                    │
│  {{special_requests}}                                        │
│  We'll do our best to accommodate these.                     │
│  {{/if}}                                                     │
│                                                              │
│  ────────────────────────────────────────────────────────    │
│  Need to modify or cancel? Contact us at {{hotel_phone}}     │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

---

## 3. Check-In Reminder Email (1 Day Before)

```text
Template: templates/emails/checkin_reminder.html
Trigger:  Cloud Scheduler — 1 day before check_in_date, 9:00 AM IST
To:       Guest email
Subject:  Arriving Tomorrow — {{hotel_name}} | {{confirmation_number}}

┌──────────────────────────────────────────────────────────────┐
│                                                              │
│              [Hotel Logo]                                     │
│              Mumbai Seaside Hotel                             │
│                                                              │
│  ────────────────────────────────────────────────────────    │
│                                                              │
│  Dear {{guest_name}},                                        │
│                                                              │
│  We're looking forward to welcoming you tomorrow!            │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  YOUR STAY                                             │  │
│  │                                                        │  │
│  │  Confirmation #:  {{confirmation_number}}               │  │
│  │  Check-in:        {{check_in_date}} (12:00 PM onwards)  │  │
│  │  Check-out:       {{check_out_date}} (11:00 AM)         │  │
│  │  Room Type:       {{room_type}}                         │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                              │
│  📍 HOW TO REACH US                                          │
│  {{hotel_address}}                                           │
│  📍 Google Maps: {{map_link}}                                │
│  📞 Contact: {{hotel_phone}}                                 │
│                                                              │
│  📋 REMINDERS                                                │
│  • Check-in time: 12:00 PM onwards                           │
│  • Please carry a valid photo ID                             │
│  • Foreign nationals: Passport required                      │
│                                                              │
│  See you tomorrow!                                           │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

---

## 4. Payment Receipt Email

```text
Template: templates/emails/payment_receipt.html
Trigger:  Payment completed (status = completed)
To:       Guest email
Subject:  Payment Received — ₹{{amount}} | {{hotel_name}}

┌──────────────────────────────────────────────────────────────┐
│                                                              │
│              [Hotel Logo]                                     │
│              Mumbai Seaside Hotel                             │
│                                                              │
│  ────────────────────────────────────────────────────────    │
│                                                              │
│  Dear {{guest_name}},                                        │
│                                                              │
│  We've received your payment. Here's your receipt:           │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  PAYMENT DETAILS                                       │  │
│  │                                                        │  │
│  │  Amount:          ₹{{amount}}                           │  │
│  │  Method:          {{payment_method}}                     │  │
│  │  Transaction ID:  {{transaction_id}}                    │  │
│  │  Date:            {{payment_date}}                      │  │
│  │  Booking #:       {{confirmation_number}}               │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  BALANCE SUMMARY                                       │  │
│  │                                                        │  │
│  │  Total charges:   ₹{{total_charges}}                    │  │
│  │  Total paid:      ₹{{total_paid}}                       │  │
│  │  Balance due:     ₹{{balance}}                          │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                              │
│  Thank you for your payment!                                 │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

---

## 5. Checkout Summary + Invoice Email

```text
Template: templates/emails/checkout_summary.html
Trigger:  Reservation checked out (status = checked_out)
To:       Guest email
Subject:  Thank You for Staying — {{hotel_name}} | Invoice {{folio_number}}
Attachment: Invoice PDF

┌──────────────────────────────────────────────────────────────┐
│                                                              │
│              [Hotel Logo]                                     │
│              Mumbai Seaside Hotel                             │
│                                                              │
│  ────────────────────────────────────────────────────────    │
│                                                              │
│  Dear {{guest_name}},                                        │
│                                                              │
│  Thank you for staying with us! We hope you had a            │
│  wonderful experience.                                       │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  STAY SUMMARY                                          │  │
│  │                                                        │  │
│  │  Booking #:       {{confirmation_number}}               │  │
│  │  Invoice #:       {{folio_number}}                      │  │
│  │  Room:            {{room_number}} ({{room_type}})        │  │
│  │  Check-in:        {{check_in_date}}                     │  │
│  │  Check-out:       {{check_out_date}}                    │  │
│  │  Nights:          {{num_nights}}                        │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  INVOICE BREAKDOWN                                     │  │
│  │                                                        │  │
│  │  Date       │ Description          │ Amount             │  │
│  │  ───────────┼──────────────────────┼──────────────────  │  │
│  │  {{date_1}} │ Room charge          │ ₹{{rate_1}}        │  │
│  │  {{date_1}} │ CGST (6%)            │ ₹{{cgst_1}}        │  │
│  │  {{date_1}} │ SGST (6%)            │ ₹{{sgst_1}}        │  │
│  │  {{date_2}} │ Room charge          │ ₹{{rate_2}}        │  │
│  │  {{date_2}} │ CGST (6%)            │ ₹{{cgst_2}}        │  │
│  │  {{date_2}} │ SGST (6%)            │ ₹{{sgst_2}}        │  │
│  │  {{date_3}} │ Minibar              │ ₹{{minibar}}       │  │
│  │  ───────────┼──────────────────────┼──────────────────  │  │
│  │             │ Total Charges        │ ₹{{total_charges}} │  │
│  │             │ Total GST            │ ₹{{total_gst}}     │  │
│  │             │ Total Paid           │ ₹{{total_paid}}    │  │
│  │             │ Balance              │ ₹{{balance}}        │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  HOTEL TAX DETAILS                                     │  │
│  │                                                        │  │
│  │  GSTIN:           {{hotel_gst_number}}                  │  │
│  │  SAC Code:        9963                                  │  │
│  │  PAN:             {{hotel_pan}}                          │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                              │
│  📎 Your detailed invoice is attached as a PDF.              │
│                                                              │
│  We hope to see you again soon!                              │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

---

## 6. Cancellation Confirmation Email

```text
Template: templates/emails/cancellation.html
Trigger:  Reservation cancelled (status = cancelled)
To:       Guest email
Subject:  Booking Cancelled — {{hotel_name}} | {{confirmation_number}}

┌──────────────────────────────────────────────────────────────┐
│                                                              │
│              [Hotel Logo]                                     │
│              Mumbai Seaside Hotel                             │
│                                                              │
│  ────────────────────────────────────────────────────────    │
│                                                              │
│  Dear {{guest_name}},                                        │
│                                                              │
│  Your booking has been cancelled as requested.               │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  CANCELLED BOOKING                                     │  │
│  │                                                        │  │
│  │  Confirmation #:  {{confirmation_number}}               │  │
│  │  Room Type:       {{room_type}}                         │  │
│  │  Check-in:        {{check_in_date}}                     │  │
│  │  Check-out:       {{check_out_date}}                    │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                              │
│  {{#if cancellation_fee > 0}}                                │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  CANCELLATION CHARGES                                  │  │
│  │                                                        │  │
│  │  Cancellation fee:     ₹{{cancellation_fee}}            │  │
│  │  Previously paid:      ₹{{paid_amount}}                 │  │
│  │  Refund amount:        ₹{{refund_amount}}               │  │
│  │                                                        │  │
│  │  Refund will be processed to your original payment      │  │
│  │  method within 5-7 business days.                       │  │
│  └────────────────────────────────────────────────────────┘  │
│  {{/if}}                                                     │
│                                                              │
│  {{#if cancellation_fee == 0}}                               │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  No cancellation charges apply.                        │  │
│  │                                                        │  │
│  │  {{#if paid_amount > 0}}                               │  │
│  │  Full refund of ₹{{paid_amount}} will be processed     │  │
│  │  within 5-7 business days.                              │  │
│  │  {{/if}}                                               │  │
│  └────────────────────────────────────────────────────────┘  │
│  {{/if}}                                                     │
│                                                              │
│  We hope to welcome you in the future.                       │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

---

## 7. Refund Processed Email

```text
Template: templates/emails/refund_processed.html
Trigger:  Refund completed (Payment.status = refunded via Razorpay webhook)
To:       Guest email
Subject:  Refund Processed — ₹{{refund_amount}} | {{hotel_name}}

┌──────────────────────────────────────────────────────────────┐
│                                                              │
│              [Hotel Logo]                                     │
│              Mumbai Seaside Hotel                             │
│                                                              │
│  ────────────────────────────────────────────────────────    │
│                                                              │
│  Dear {{guest_name}},                                        │
│                                                              │
│  Your refund has been processed.                             │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  REFUND DETAILS                                        │  │
│  │                                                        │  │
│  │  Refund amount:   ₹{{refund_amount}}                    │  │
│  │  Refund to:       {{original_payment_method}}            │  │
│  │  Reason:          {{refund_reason}}                      │  │
│  │  Booking #:       {{confirmation_number}}               │  │
│  │                                                        │  │
│  │  The refund will reflect in your account within         │  │
│  │  5-7 business days depending on your bank.              │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                              │
│  If you have any queries, contact us at {{hotel_phone}}.     │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

---

## 8. Admin — Daily Sales Summary Email

```text
Template: templates/emails/daily_sales_summary.html
Trigger:  Cloud Scheduler — Monday 9:00 AM IST (weekly report)
To:       Super admin email
Subject:  Weekly Revenue Report — All Hotels | {{week_range}}

┌──────────────────────────────────────────────────────────────┐
│                                                              │
│  WEEKLY REVENUE REPORT                                       │
│  {{week_start}} to {{week_end}}                              │
│                                                              │
│  ────────────────────────────────────────────────────────    │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  TOTALS (All Hotels)                                   │  │
│  │                                                        │  │
│  │  Total Revenue:     ₹{{total_revenue}}                  │  │
│  │  Total Collected:   ₹{{total_collected}}                │  │
│  │  Total Outstanding: ₹{{total_outstanding}}              │  │
│  │  GST Collected:     ₹{{total_gst}}                      │  │
│  │  Avg Occupancy:     {{avg_occupancy}}%                   │  │
│  │  Total Bookings:    {{total_bookings}}                   │  │
│  │  Cancellations:     {{total_cancellations}}              │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  PER HOTEL                                             │  │
│  │                                                        │  │
│  │  Hotel            │ Occ%  │ Revenue    │ Collected     │  │
│  │  ─────────────────┼───────┼────────────┼─────────────  │  │
│  │  Mumbai Seaside   │  82%  │ ₹3,20,000  │ ₹2,95,000    │  │
│  │  Goa Beach Resort │  91%  │ ₹2,80,000  │ ₹2,80,000    │  │
│  │  Delhi Central    │  74%  │ ₹2,40,000  │ ₹2,10,000    │  │
│  │  Jaipur Heritage  │  68%  │ ₹1,90,000  │ ₹1,75,000    │  │
│  │  ...              │       │            │               │  │
│  │  ─────────────────┼───────┼────────────┼─────────────  │  │
│  │  TOTAL            │  79%  │₹18,50,000  │₹16,20,000    │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  COLLECTIONS BY METHOD                                 │  │
│  │                                                        │  │
│  │  UPI:          ₹7,80,000  (48%)                        │  │
│  │  Cash:         ₹3,40,000  (21%)                        │  │
│  │  Credit Card:  ₹2,60,000  (16%)                        │  │
│  │  Debit Card:   ₹1,50,000  (9%)                         │  │
│  │  Net Banking:  ₹60,000    (4%)                         │  │
│  │  Wallet:       ₹30,000    (2%)                         │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                              │
│  Login to dashboard for full details:                        │
│  {{dashboard_url}}                                           │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

---

## 9. Template File Structure

```text
templates/
├── emails/
│   ├── base_email.html              ← Base layout (logo, footer, styles)
│   ├── booking_confirmation.html
│   ├── checkin_reminder.html
│   ├── payment_receipt.html
│   ├── checkout_summary.html
│   ├── cancellation.html
│   ├── refund_processed.html
│   └── admin_weekly_report.html

Implementation:
  - Django templates with inline CSS (email clients don't support external CSS)
  - Responsive design (mobile-friendly — most guests read email on phone)
  - All amounts in ₹ with Indian number formatting (₹1,00,000)
  - Hotel logo loaded from Cloud Storage (or fallback to text)
  - PDF invoice generated separately using weasyprint / xhtml2pdf
  - Sent via SendGrid API (free tier: 100 emails/day = enough)
```

---

## 10. Invoice PDF Template

Attached to checkout summary email and available for download from folio detail page.

```text
┌──────────────────────────────────────────────────────────────┐
│                                                              │
│  {{hotel_name}}                               TAX INVOICE    │
│  {{hotel_address}}                                           │
│  GSTIN: {{hotel_gst_number}}                                 │
│  PAN: {{hotel_pan}}                                          │
│  Phone: {{hotel_phone}}                                      │
│                                                              │
│  ────────────────────────────────────────────────────────    │
│                                                              │
│  Invoice #:  {{folio_number}}          Date: {{invoice_date}} │
│  Booking #:  {{confirmation_number}}                         │
│                                                              │
│  BILL TO:                                                    │
│  {{guest_name}}                                              │
│  {{guest_address}}                                           │
│  {{guest_city}}, {{guest_state}} — {{guest_pincode}}         │
│                                                              │
│  ────────────────────────────────────────────────────────    │
│                                                              │
│  Room: {{room_number}} ({{room_type}})                       │
│  Check-in: {{check_in_date}}  |  Check-out: {{check_out_date}}│
│  Nights: {{num_nights}}                                      │
│                                                              │
│  ────────────────────────────────────────────────────────    │
│                                                              │
│  # │ Date       │ Description        │ SAC   │ Amount (₹)   │
│  ──┼────────────┼────────────────────┼───────┼────────────── │
│  1 │ 2026-04-07 │ Room Charge        │ 9963  │    2,500.00  │
│  2 │ 2026-04-07 │ CGST @ 6%          │ 9963  │      150.00  │
│  3 │ 2026-04-07 │ SGST @ 6%          │ 9963  │      150.00  │
│  4 │ 2026-04-08 │ Room Charge        │ 9963  │    2,500.00  │
│  5 │ 2026-04-08 │ CGST @ 6%          │ 9963  │      150.00  │
│  6 │ 2026-04-08 │ SGST @ 6%          │ 9963  │      150.00  │
│  7 │ 2026-04-08 │ Minibar            │ 9963  │      350.00  │
│  ──┼────────────┼────────────────────┼───────┼────────────── │
│    │            │ Subtotal           │       │    5,350.00  │
│    │            │ CGST Total         │       │      300.00  │
│    │            │ SGST Total         │       │      300.00  │
│    │            │ Grand Total        │       │    5,950.00  │
│  ──┼────────────┼────────────────────┼───────┼────────────── │
│    │            │ Paid               │       │    5,950.00  │
│    │            │ Balance Due        │       │        0.00  │
│                                                              │
│  ────────────────────────────────────────────────────────    │
│                                                              │
│  PAYMENT DETAILS:                                            │
│  {{payment_date}} — ₹5,950.00 via UPI (Txn: {{txn_id}})     │
│                                                              │
│  ────────────────────────────────────────────────────────    │
│                                                              │
│  Amount in words: Rupees Five Thousand Nine Hundred and      │
│  Fifty Only                                                  │
│                                                              │
│  ────────────────────────────────────────────────────────    │
│                                                              │
│  This is a computer-generated invoice.                       │
│  No signature required.                                      │
│                                                              │
│  HSN/SAC: 9963 — Hotel Accommodation Services               │
│                                                              │
└──────────────────────────────────────────────────────────────┘

Implementation:
  templates/invoices/invoice.html → rendered with weasyprint → PDF
  Stored in Cloud Storage: invoices/{hotel_id}/{folio_number}.pdf
  Downloadable from:
    /dashboard/billing/:id/invoice/  (staff)
    Attached to checkout email (guest)
```
