# Operational Workflows

Step-by-step flows for every critical hotel operation.

---

## 1. Reservation Status — State Machine

A reservation can only move through these states in this order. No skipping.

```text
                    ┌─────────────┐
                    │   CREATED   │  (initial, just saved in DB)
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
              ┌─────│  CONFIRMED  │─────┐
              │     └──────┬──────┘     │
              │            │            │
       (guest doesn't     (guest       (guest or staff
        show up)          arrives)      cancels)
              │            │            │
       ┌──────▼──────┐ ┌──▼────────┐ ┌─▼───────────┐
       │   NO_SHOW   │ │ CHECKED_IN│ │  CANCELLED   │
       └─────────────┘ └──────┬────┘ └──────────────┘
                              │
                       (guest leaves)
                              │
                       ┌──────▼──────┐
                       │ CHECKED_OUT │
                       └─────────────┘

ALLOWED TRANSITIONS:
  confirmed   → checked_in     (check-in)
  confirmed   → cancelled      (cancel before arrival)
  confirmed   → no_show        (didn't arrive by cutoff)
  checked_in  → checked_out    (checkout)

NOT ALLOWED:
  checked_in  → cancelled      ✗ (already in room, must checkout first)
  checked_out → anything       ✗ (final state)
  cancelled   → anything       ✗ (final state)
  no_show     → confirmed      ✗ (must create new reservation)
```

---

## 2. Folio Status — State Machine

```text
  ┌──────────┐
  │   OPEN   │  Created when reservation is confirmed
  └────┬─────┘
       │
       ├── Charges added (room, GST, minibar, etc.)
       ├── Payments received (UPI, cash, card, etc.)
       │
       │  When balance = 0 AND guest checked out:
       │
  ┌────▼─────┐
  │ SETTLED  │  All paid, guest departed
  └──────────┘

  Special case:
  ┌──────────┐
  │   VOID   │  Reservation cancelled, no charges apply
  └──────────┘

RULES:
  - Folio opens automatically when reservation is confirmed
  - Folio stays OPEN as long as guest is staying (even if balance = 0)
  - Folio moves to SETTLED only after:
    1. Reservation status = checked_out
    2. Balance = 0 (all charges paid)
  - If reservation is cancelled with no charges → VOID
  - If reservation is cancelled with partial charges (late cancellation fee) → stays OPEN until paid, then SETTLED
  - Staff CANNOT manually close a folio with outstanding balance
```

---

## 3. Check-In Workflow

```text
URL: /dashboard/reservations/:id/check-in/

PRE-CONDITIONS:
  - Reservation status = confirmed
  - Check-in date = today (or earlier for early check-in)
  - Room assigned and available

STEP-BY-STEP:

┌──────────────────────────────────────────────────────────────┐
│  STEP 1: VERIFY GUEST IDENTITY                               │
│                                                              │
│  Front desk:                                                 │
│   1. Ask guest for ID (Aadhar / Passport / Driving License)  │
│   2. Match name with reservation                              │
│   3. Upload ID photo (front + back) → Cloud Storage           │
│   4. System saves to guest.id_document_front / _back          │
│                                                              │
│  If guest is FOREIGN (passport):                             │
│   5. System auto-flags: "Form C required within 24 hours"    │
│   6. Creates GuestVerification(form_type='form_c',           │
│      status='pending')                                       │
│                                                              │
│  For ALL guests:                                             │
│   7. Creates GuestVerification(form_type='form_a',           │
│      status='pending')                                       │
│                                                              │
└──────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────┐
│  STEP 2: CONFIRM ROOM                                        │
│                                                              │
│  System shows assigned room (from reservation).               │
│  Front desk can:                                              │
│   - Accept assigned room → continue                          │
│   - Change room → pick from available rooms of same type     │
│     (updates ReservationRoom.room FK)                        │
│   - Upgrade room → pick higher room type (rate adjustment)   │
│                                                              │
│  Room status changes: available → occupied                    │
│                                                              │
└──────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────┐
│  STEP 3: COLLECT ADVANCE PAYMENT (if required)               │
│                                                              │
│  If folio.balance > 0 and hotel requires advance:            │
│   - Show amount due                                          │
│   - Collect via UPI / Card / Cash (Razorpay or manual)       │
│   - Payment recorded in Payment model                         │
│                                                              │
│  If folio.balance = 0 (prepaid via OTA):                     │
│   - Skip this step                                           │
│                                                              │
└──────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────┐
│  STEP 4: COMPLETE CHECK-IN                                   │
│                                                              │
│  Front desk clicks "Complete Check-In"                        │
│                                                              │
│  System does:                                                 │
│   1. reservation.status = 'checked_in'                       │
│   2. reservation.actual_check_in_time = now()                │
│   3. room.status = 'occupied'                                │
│   4. Create GuestVerification records (Form A, Form C)       │
│   5. Create AuditLog entry                                    │
│   6. Send WhatsApp: "Welcome! Your room X is ready."          │
│   7. If foreign guest: alert staff "Form C due in 24 hours"  │
│                                                              │
└──────────────────────────────────────────────────────────────┘

TIME: ~2-3 minutes for regular guest, ~5 minutes for foreign guest
```

---

## 4. Check-Out Workflow

```text
URL: /dashboard/reservations/:id/check-out/

PRE-CONDITIONS:
  - Reservation status = checked_in
  - Check-out date = today (or allow late checkout)

STEP-BY-STEP:

┌──────────────────────────────────────────────────────────────┐
│  STEP 1: REVIEW FOLIO                                        │
│                                                              │
│  System shows complete folio:                                 │
│   - All room charges (per night with GST breakup)            │
│   - Any extra charges (minibar, laundry, etc.)               │
│   - All payments received                                     │
│   - Outstanding balance                                       │
│                                                              │
│  Front desk reviews with guest.                               │
│  Guest can dispute charges → staff adjusts if needed.         │
│                                                              │
└──────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────┐
│  STEP 2: COLLECT REMAINING PAYMENT                           │
│                                                              │
│  If balance > 0:                                             │
│   - Collect via UPI / Card / Cash                            │
│   - Wait for payment confirmation                             │
│   - Payment recorded in Payment model                         │
│                                                              │
│  If balance = 0:                                             │
│   - Skip to Step 3                                           │
│                                                              │
│  If balance < 0 (overpaid):                                  │
│   - Process refund via Razorpay or cash                      │
│   - Refund recorded as Payment(status='refunded')            │
│                                                              │
│  ⚠ CANNOT proceed to Step 3 with balance > 0                │
│    unless manager overrides (logged in AuditLog)             │
│                                                              │
└──────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────┐
│  STEP 3: COMPLETE CHECK-OUT                                  │
│                                                              │
│  Front desk clicks "Complete Check-Out"                       │
│                                                              │
│  System does:                                                 │
│   1. reservation.status = 'checked_out'                      │
│   2. reservation.actual_check_out_time = now()               │
│   3. room.status = 'available' (→ then 'dirty' for cleaning) │
│   4. folio.status = 'settled' (if balance = 0)               │
│   5. folio.closed_at = now()                                 │
│   6. Generate PDF invoice → store in Cloud Storage            │
│   7. Create HousekeepingTask(room, task_type='cleaning',     │
│      status='pending')                                       │
│   8. Create AuditLog entry                                    │
│   9. Send WhatsApp: checkout summary + invoice PDF            │
│                                                              │
└──────────────────────────────────────────────────────────────┘

TIME: ~3-5 minutes
```

---

## 5. Walk-In Booking Workflow

Guest shows up without reservation. This is the #1 daily front desk task.

```text
URL: /dashboard/reservations/walk-in/

┌──────────────────────────────────────────────────────────────┐
│  STEP 1: CHECK AVAILABILITY                                  │
│                                                              │
│  Front desk opens walk-in page:                               │
│   - Shows all rooms with LIVE status for today               │
│   - Green = available, Red = occupied, Grey = maintenance     │
│   - Filter by room type                                       │
│                                                              │
│  "Available now: 3 rooms"                                     │
│   101 (Standard) — ₹1,500/night                              │
│   104 (Deluxe)   — ₹2,500/night                              │
│   105 (Suite)    — ₹4,000/night                              │
│                                                              │
│  Staff selects room + number of nights.                       │
│                                                              │
└──────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────┐
│  STEP 2: CREATE GUEST (or find existing)                     │
│                                                              │
│  Search by phone number:                                      │
│   - Found → pre-fill guest details, show "Returning guest"   │
│   - Not found → quick guest form:                            │
│     Name, Phone, ID type, ID number, Nationality              │
│     (minimal — more details captured at check-in)            │
│                                                              │
└──────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────┐
│  STEP 3: RATE & BOOKING SUMMARY                              │
│                                                              │
│  System auto-calculates:                                      │
│   Rate plan: "Standard" (default for walk-in)                │
│   Rate: ₹2,500/night × 2 nights = ₹5,000                   │
│   GST 12%: ₹600 (₹300 CGST + ₹300 SGST)                    │
│   Total: ₹5,600                                              │
│                                                              │
│  Staff can override rate (with reason — logged).              │
│                                                              │
│  Staff clicks "Confirm Booking"                               │
│                                                              │
└──────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────┐
│  STEP 4: COLLECT PAYMENT + IMMEDIATE CHECK-IN                │
│                                                              │
│  For walk-ins, booking + check-in happen together:           │
│                                                              │
│  System creates:                                              │
│   1. Guest record (or links existing)                        │
│   2. Reservation (status = 'confirmed' → immediately         │
│      transitions to 'checked_in')                            │
│   3. ReservationRoom + RoomNightRate entries                  │
│   4. Folio (status = 'open')                                 │
│   5. Room charges + GST as FolioCharge entries                │
│   6. Payment collection (advance or full)                     │
│   7. GuestVerification records (Form A, Form C if foreign)   │
│   8. Room.status = 'occupied'                                │
│   9. AuditLog entry                                           │
│  10. WhatsApp confirmation to guest                           │
│                                                              │
│  Total time: ~3-5 minutes (one screen, no page switches)     │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

---

## 6. No-Show Workflow

```text
A no-show = guest has a confirmed reservation but doesn't arrive.

TRIGGER: Automatic — runs during Night Audit at 00:30 IST

┌──────────────────────────────────────────────────────────────┐
│  NIGHT AUDIT checks all reservations where:                  │
│   - status = 'confirmed'                                     │
│   - check_in_date = today (now yesterday, since it's 00:30)  │
│   - NOT checked in                                           │
│                                                              │
│  For each no-show reservation:                               │
│                                                              │
│  1. reservation.status = 'no_show'                           │
│                                                              │
│  2. Check cancellation policy on the rate plan:              │
│     - non_refundable → charge full booking amount             │
│     - strict → charge cancellation_charge_percent of total   │
│     - moderate → charge first night                           │
│     - free → no charge                                        │
│                                                              │
│  3. Post no-show charge as FolioCharge                        │
│     (charge_type = 'no_show_fee')                            │
│                                                              │
│  4. If advance payment was collected:                        │
│     - Deduct no-show fee from advance                        │
│     - Refund remainder (if any) via Razorpay                 │
│                                                              │
│  5. Release the room → room.status = 'available'             │
│                                                              │
│  6. Create AuditLog entry                                     │
│                                                              │
│  7. Notify hotel admin (in-app + WhatsApp if urgent)         │
│                                                              │
│  8. Send guest notification:                                 │
│     "Your reservation #BK-XXXX was marked as no-show.         │
│      A fee of ₹X,XXX has been charged per cancellation        │
│      policy."                                                │
│                                                              │
│  MANUAL OVERRIDE:                                            │
│   Manager can undo no-show → set back to 'confirmed'         │
│   if guest calls and says they're arriving late.             │
│   Must be done before night audit or manually after.         │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

---

## 7. Night Audit Workflow

Runs automatically every night at 00:30 IST via Cloud Scheduler.

```text
URL triggered: /api/tasks/night-audit/
Time: 00:30 IST daily

┌──────────────────────────────────────────────────────────────┐
│                     NIGHT AUDIT                               │
│                  Runs for EACH hotel                          │
│                                                              │
│  Step 1: POST ROOM CHARGES                                   │
│  ─────────────────────────────                               │
│  For every reservation where:                                │
│   - status = 'checked_in'                                    │
│   - today falls within check_in_date..check_out_date         │
│                                                              │
│  Create FolioCharge entries:                                  │
│   a. Room charge for tonight                                  │
│      amount = RoomNightRate.rate for today's date            │
│      charge_type = 'room_charge'                             │
│                                                              │
│   b. GST charges (auto-calculated from room rate):           │
│      If rate ≤ ₹7,500:  12% → 6% CGST + 6% SGST            │
│      If rate > ₹7,500:  18% → 9% CGST + 9% SGST            │
│      charge_type = 'cgst' and 'sgst'                         │
│                                                              │
│   c. Skip if charge already posted for tonight               │
│      (idempotent — safe to re-run)                           │
│                                                              │
│  Step 2: HANDLE NO-SHOWS                                     │
│  ─────────────────────────                                   │
│  (See No-Show Workflow above — Section 6)                    │
│                                                              │
│  Step 3: FLAG OVERDUE CHECKOUTS                              │
│  ──────────────────────────────                              │
│  For reservations where:                                     │
│   - status = 'checked_in'                                    │
│   - check_out_date = today (they should have left today)     │
│   - NOT checked out                                          │
│                                                              │
│  → Flag as overdue (shown on dashboard next morning)         │
│  → Optional: post extra night charge if policy allows        │
│                                                              │
│  Step 4: UPDATE FOLIO TOTALS                                 │
│  ───────────────────────────                                 │
│  For every open folio:                                        │
│   total_charges  = SUM(FolioCharge.amount)                   │
│   total_payments = SUM(Payment.amount WHERE completed)       │
│   balance        = total_charges - total_payments            │
│                                                              │
│  Step 5: GENERATE DAILY SNAPSHOT                             │
│  ───────────────────────────────                             │
│  Save daily numbers (used for morning report):               │
│   - Occupancy: X / Y rooms (Z%)                             │
│   - Revenue posted tonight: ₹XX,XXX                         │
│   - Total outstanding: ₹XX,XXX                              │
│   - No-shows: N                                              │
│   - Arrivals tomorrow: N                                     │
│   - Departures tomorrow: N                                   │
│                                                              │
│  Step 6: LOG COMPLETION                                      │
│  ──────────────────────                                      │
│  Create AuditLog:                                             │
│   action = 'night_audit.completed'                           │
│   changes = {rooms_charged, noshow_count, revenue_posted}    │
│                                                              │
│  Step 7: SEND MORNING SUMMARY (at 6:00 AM IST separately)   │
│  ─────────────────────────────                               │
│  WhatsApp to hotel admin / manager:                          │
│   "🌅 Good morning! Mumbai Seaside daily summary:             │
│    Occupancy: 12/15 (80%)                                    │
│    Revenue: ₹28,400                                          │
│    Outstanding: ₹4,200                                       │
│    Arrivals today: 3 | Departures: 2                         │
│    No-shows: 0"                                              │
│                                                              │
└──────────────────────────────────────────────────────────────┘

PERFORMANCE:
  20 hotels × 13 rooms = ~260 folio charges to post
  Total time: under 2 seconds
  Runs as single Cloud Scheduler HTTP request

FAILURE HANDLING:
  - If audit fails for one hotel, continue with others
  - Log error, retry once automatically
  - If retry fails → WhatsApp alert to super_admin
  - Failed hotel's audit can be re-triggered manually from admin panel
```

---

## 8. Night Audit Database Model

```text
New model: DailyAuditSnapshot

| Column             | Type              | Notes                          |
|--------------------|-------------------|--------------------------------|
| id                 | PK                |                                |
| hotel              | FK → Hotel        |                                |
| audit_date         | date              | Which night was audited         |
| total_rooms        | int               |                                |
| occupied_rooms     | int               |                                |
| occupancy_percent  | decimal(5,2)      |                                |
| revenue_posted     | decimal(12,2)     | Room charges + GST posted tonight |
| total_outstanding  | decimal(12,2)     | Sum of all open folio balances  |
| noshow_count       | int               |                                |
| arrivals_tomorrow  | int               |                                |
| departures_tomorrow| int               |                                |
| audit_status       | enum              | completed, partial, failed      |
| error_message      | text null         |                                |
| completed_at       | datetime          |                                |

Unique constraint: (hotel, audit_date)

This table powers:
  - Morning summary WhatsApp message
  - Night audit report page: /dashboard/reports/night-audit/:date/
  - Historical occupancy trends in reports
```

---

## 9. Cancellation Workflow

```text
URL: /dashboard/reservations/:id/cancel/

PRE-CONDITIONS:
  - Reservation status = 'confirmed' (not checked in)

┌──────────────────────────────────────────────────────────────┐
│  STEP 1: CALCULATE CANCELLATION FEE                          │
│                                                              │
│  System reads the RatePlan's cancellation policy:            │
│                                                              │
│  Policy: free                                                │
│   → Fee: ₹0                                                 │
│                                                              │
│  Policy: moderate                                            │
│   → If cancelled > 24h before check-in: ₹0                  │
│   → If cancelled < 24h before check-in: 100% of first night │
│                                                              │
│  Policy: strict                                              │
│   → If cancelled > 24h before check-in: ₹0                  │
│   → If cancelled < 24h before check-in: X% of total booking │
│                                                              │
│  Policy: non_refundable                                      │
│   → Fee: 100% of total booking (no refund)                   │
│                                                              │
│  Show fee to staff before confirming.                         │
│                                                              │
└──────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────┐
│  STEP 2: PROCESS                                             │
│                                                              │
│  Staff clicks "Confirm Cancellation"                          │
│                                                              │
│  System does:                                                 │
│   1. reservation.status = 'cancelled'                        │
│   2. If cancellation fee > 0:                                │
│      → Post FolioCharge(charge_type='cancellation_fee')      │
│   3. Calculate refund = payments_received - cancellation_fee │
│   4. If refund > 0:                                          │
│      → Process refund via Razorpay (original payment method) │
│      → Or record cash refund                                  │
│   5. If folio has no charges → folio.status = 'void'         │
│      If folio has charges → keep 'open' until paid/refunded  │
│   6. Release room → room.status = 'available'                │
│   7. AuditLog entry                                           │
│   8. WhatsApp to guest: "Booking cancelled. Refund of ₹X,XXX │
│      will be processed within 5-7 business days."            │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

---

## 10. Room Status Transitions

```text
Room.status follows this flow:

  ┌───────────┐
  │ AVAILABLE │ ← Room is clean and ready
  └─────┬─────┘
        │ (guest checks in)
  ┌─────▼─────┐
  │ OCCUPIED  │ ← Guest is staying
  └─────┬─────┘
        │ (guest checks out)
  ┌─────▼─────┐
  │   DIRTY   │ ← Needs cleaning (auto-created after checkout)
  └─────┬─────┘
        │ (housekeeping completes cleaning)
  ┌─────▼─────┐
  │ AVAILABLE │ ← Ready for next guest
  └───────────┘

  Special states:
  ┌─────────────┐
  │ MAINTENANCE │ ← AC broken, plumbing issue, etc.
  └─────────────┘   Set manually by hotel admin.
                     Cannot be booked until cleared.

  ┌─────────────┐
  │   BLOCKED   │ ← Intentionally blocked (renovation, owner use, etc.)
  └─────────────┘   Set manually by hotel admin.

Note: 'dirty' is a new status (added to the enum).
Previously we only had: available, occupied, maintenance, blocked.
Now: available, occupied, dirty, maintenance, blocked.
```

---

## 11. Housekeeping Workflow (Post-Checkout)

```text
Guest checks out
      │
      ▼
System auto-creates HousekeepingTask:
  room = checkout room
  task_type = 'cleaning'
  status = 'pending'
  priority = 'normal' (or 'urgent' if next guest arriving today)
      │
      ▼
Room.status = 'dirty'
      │
      ▼
Housekeeping staff sees task on their board:
  /dashboard/housekeeping/
      │
      ▼
Staff clicks "Start Cleaning" → task.status = 'in_progress'
      │
      ▼
Staff finishes, clicks "Mark Clean" → task.status = 'completed'
      │
      ▼
Room.status = 'available'
      │
      ▼
Room appears as available on calendar for next booking
```

---

## 12. Payment Status Transitions

```text
ONLINE PAYMENT (Razorpay):
  Staff clicks "Collect Payment"
    → Payment created (status = 'pending')
    → Razorpay order created
    → Guest pays via UPI/card/etc.
    → Razorpay webhook received
    → Payment.status = 'completed'
    → Folio balance recalculated

  If payment fails:
    → Razorpay webhook with failure
    → Payment.status = 'failed'
    → Guest retries or pays cash

CASH PAYMENT:
  Staff clicks "Record Cash Payment"
    → Payment created (status = 'completed' immediately)
    → No Razorpay involved
    → Folio balance recalculated

REFUND:
  Manager clicks "Refund"
    → New Payment record created (amount = negative)
    → For online: Razorpay refund API called
      → status = 'pending' until Razorpay confirms
      → status = 'refunded' after webhook
    → For cash: status = 'refunded' immediately
    → original_payment FK links to the payment being refunded
    → Folio balance recalculated
```

### Updated Payment Model — Add Refund Link

```text
Add to Payment model:
  | original_payment | FK → Payment (null) | Links refund to original payment |
  | refund_reason    | varchar(200) null   | Why refund was issued             |
```
