# Rate Management Architecture

Hotels don't charge the same rate every day. Rates change by season, day of week, booking source, and guest type.

---

## 1. How Hotel Pricing Actually Works

```text
A "Deluxe Room" at ₹2,000/night is just the base rate.
The actual rate a guest pays depends on:

  1. WHEN they stay       → Season (peak/off-peak), weekday vs weekend
  2. WHERE they booked    → Walk-in, Airbnb, Booking.com, phone
  3. WHO they are         → Regular guest, corporate, group, long-stay
  4. HOW far in advance   → Last-minute rates, early bird discounts

The system needs to handle all of these without the staff
doing manual math every time.
```

---

## 2. Database Models

### RatePlan

A rate plan is a named pricing strategy. Each hotel can have multiple.

| Column           | Type              | Notes                          |
|------------------|-------------------|--------------------------------|
| id               | PK                |                                |
| hotel            | FK → Hotel        |                                |
| name             | varchar(100)      | e.g. "Standard", "Airbnb", "Corporate - TCS" |
| plan_type        | enum              | standard, ota, corporate, promotional, long_stay |
| source           | enum (nullable)   | walk_in, airbnb, booking_com, website, phone, null (if not source-specific) |
| is_default       | bool              | One default plan per hotel (used for walk-ins) |
| is_active        | bool              |                                |
| priority         | int               | Higher priority plan wins if multiple match |
| min_stay_nights  | int (default 1)   | Minimum nights for this plan to apply |
| advance_days     | int (nullable)    | Must book X days ahead (for early bird) |
| cancellation_policy | enum           | free, moderate, strict, non_refundable |
| cancellation_hours  | int (default 24)| Free cancel until X hours before check-in |
| cancellation_charge_percent | decimal(4,2) default 0 | % charged if cancelled late |
| created_at       | datetime          |                                |

**Examples of rate plans per hotel:**

```text
Hotel "Mumbai Seaside" has these rate plans:

  1. Standard (default)      — walk-in, phone bookings
  2. Airbnb Rate             — source=airbnb, slightly higher (to cover commission)
  3. Booking.com Rate        — source=booking_com
  4. Corporate - Infosys     — special negotiated rate
  5. Long Stay (7+ nights)   — min_stay_nights=7, discounted
  6. Weekend Special         — promotional, Fri-Sun only
```

### RatePlanRate

Actual prices per room type within a rate plan. This is where the money numbers live.

| Column           | Type              | Notes                          |
|------------------|-------------------|--------------------------------|
| id               | PK                |                                |
| rate_plan        | FK → RatePlan     |                                |
| room_type        | FK → RoomType     |                                |
| base_rate        | decimal(10,2)     | Default nightly rate in INR    |
| extra_adult_rate | decimal(10,2) default 0 | Charge per extra adult   |
| extra_child_rate | decimal(10,2) default 0 | Charge per extra child   |
| created_at       | datetime          |                                |

**Unique constraint:** `(rate_plan, room_type)`

**Example:**

```text
Rate Plan: "Standard" at Mumbai Seaside

  Room Type          │ Base Rate │ Extra Adult │ Extra Child
  ───────────────────┼───────────┼─────────────┼────────────
  Standard Single    │ ₹1,500   │ ₹500        │ ₹300
  Deluxe Double      │ ₹2,500   │ ₹600        │ ₹300
  Suite              │ ₹4,000   │ ₹800        │ ₹500

Rate Plan: "Airbnb Rate" at Mumbai Seaside (10% higher)

  Standard Single    │ ₹1,650   │ ₹500        │ ₹300
  Deluxe Double      │ ₹2,750   │ ₹600        │ ₹300
  Suite              │ ₹4,400   │ ₹800        │ ₹500
```

### SeasonalRate (Override)

Override base rates for specific date ranges (peak season, festivals, etc.)

| Column           | Type              | Notes                          |
|------------------|-------------------|--------------------------------|
| id               | PK                |                                |
| rate_plan_rate   | FK → RatePlanRate |                                |
| name             | varchar(100)      | e.g. "Diwali Peak", "Summer Off-Peak" |
| start_date       | date              |                                |
| end_date         | date              |                                |
| rate             | decimal(10,2)     | Overrides base_rate for these dates |
| created_at       | datetime          |                                |

**Example:**

```text
Deluxe Double under "Standard" plan:
  Base rate:                    ₹2,500/night
  Diwali (Oct 28 - Nov 5):     ₹4,000/night  ← SeasonalRate override
  Christmas (Dec 20 - Jan 5):  ₹3,500/night
  Monsoon (Jun 15 - Sep 15):   ₹1,800/night  ← off-peak discount
```

### DayOfWeekRate (Optional Override)

Different rates for weekends vs weekdays.

| Column           | Type              | Notes                          |
|------------------|-------------------|--------------------------------|
| id               | PK                |                                |
| rate_plan_rate   | FK → RatePlanRate |                                |
| day_of_week      | int               | 0=Monday, 6=Sunday             |
| rate             | decimal(10,2)     |                                |

**Example:**

```text
Deluxe Double under "Standard" plan:
  Mon-Thu:  ₹2,500  (base rate, no override needed)
  Fri:      ₹2,800
  Sat:      ₹3,200
  Sun:      ₹2,800
```

---

## 3. Rate Resolution Logic

When creating a reservation, the system picks the right rate automatically.

```text
Guest books Deluxe Double for Oct 30 (Diwali) at Mumbai Seaside via Airbnb.

Step 1: Find matching rate plans for this hotel
  → "Airbnb Rate" matches (source=airbnb)
  → "Standard" also matches (default)
  → Pick "Airbnb Rate" (higher priority for source match)

Step 2: Get RatePlanRate for Deluxe Double under "Airbnb Rate"
  → Base rate: ₹2,750/night

Step 3: Check SeasonalRate override for Oct 30
  → Diwali override exists: ₹4,400/night
  → Use ₹4,400

Step 4: Check DayOfWeekRate override for Oct 30 (Wednesday)
  → No weekday override
  → Stay with ₹4,400

Step 5: Final rate = ₹4,400/night

Priority order (highest wins):
  SeasonalRate > DayOfWeekRate > RatePlanRate.base_rate
```

### Rate Resolution Function

```text
get_rate(hotel, room_type, date, source=None):

  1. Find best matching RatePlan:
     - If source provided → find plan with matching source
     - If no source match → use default plan
     - If multiple matches → use highest priority

  2. Get RatePlanRate for (plan, room_type)

  3. Check SeasonalRate for this date
     - If exists → return seasonal rate

  4. Check DayOfWeekRate for this day
     - If exists → return day-of-week rate

  5. Return base_rate
```

---

## 4. How Rates Connect to Reservations

```text
When a reservation is created:

  1. System runs get_rate() for each night of the stay
  2. Rate per night is LOCKED into ReservationRoom.rate_per_night
     (already exists in schema — this is the per-night snapshot)
  3. If stay spans multiple rate periods, each night can have a different rate

  Example: Guest stays Oct 27 - Nov 2 (6 nights)
    Oct 27: ₹2,750 (normal Airbnb rate)
    Oct 28: ₹4,400 (Diwali peak starts)
    Oct 29: ₹4,400
    Oct 30: ₹4,400
    Oct 31: ₹4,400
    Nov 1:  ₹4,400
    Total:  ₹24,750

  These rates are saved at booking time.
  If rates change later, existing bookings are NOT affected.
```

### Schema Update: ReservationRoom

```text
Current: rate_per_night (single value for entire stay)
Problem: Rate can differ per night (seasonal change mid-stay)

Solution: Add RoomNightRate table OR store as JSON

Option A — RoomNightRate table (cleaner):

  | Column         | Type              | Notes                    |
  |----------------|-------------------|--------------------------|
  | id             | PK                |                          |
  | reservation_room| FK → ReservationRoom |                       |
  | date           | date              | Specific night           |
  | rate           | decimal(10,2)     | Rate for this night      |

  Unique constraint: (reservation_room, date)

Option B — JSON field on ReservationRoom (simpler):

  nightly_rates = {"2025-10-27": 2750, "2025-10-28": 4400, ...}

Recommendation: Option A for 11-15 room hotels.
  Small data, proper querying, cleaner aggregation.
```

---

## 5. Staff Workflow for Rate Management

```text
Hotel Admin / Manager can:

  /dashboard/rates/                    → List all rate plans
  /dashboard/rates/create/             → Create new rate plan
  /dashboard/rates/:id/                → Edit rate plan + set room prices
  /dashboard/rates/:id/seasonal/       → Add seasonal overrides
  /dashboard/rates/:id/day-of-week/    → Set weekend pricing

Front Desk sees:
  When creating a reservation:
    - System auto-suggests rate based on source + dates
    - Staff can override rate manually (with reason logged)
    - Rate breakdown shown before confirming

  "Deluxe Double × 3 nights
   Oct 28: ₹4,400 (Diwali Peak)
   Oct 29: ₹4,400 (Diwali Peak)
   Oct 30: ₹4,400 (Diwali Peak)
   Subtotal: ₹13,200
   GST 12%:  ₹1,584
   Total:    ₹14,784"
```

---

## 6. Cancellation Policy

Defined per rate plan, enforced at cancellation time.

```text
Policy types:

  free:
    - Full refund anytime before check-in
    - Used for: corporate plans, loyalty guests

  moderate:
    - Free cancel until cancellation_hours before check-in
    - After that: cancellation_charge_percent of first night
    - Used for: standard bookings

  strict:
    - Free cancel until cancellation_hours before check-in
    - After that: cancellation_charge_percent of total booking
    - Used for: peak season, festival dates

  non_refundable:
    - No refund once booked
    - Used for: deeply discounted / promotional rates

Example:
  Rate Plan "Standard" → moderate, 24 hours, 100% of first night
  Guest cancels 12 hours before check-in
  → Charge: ₹2,500 (one night) as cancellation fee
  → Refund the rest via Razorpay
```
