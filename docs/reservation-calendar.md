# Reservation Calendar Architecture

The calendar is the most-used screen for front desk staff. They look at it 50+ times a day.

---

## 1. Calendar Types

```text
Two calendar views needed:

  1. ROOM GRID CALENDAR (primary — used most)
     Rows = rooms, Columns = dates
     Shows which room is booked when, by whom
     This is what front desk lives on

  2. MONTHLY OVERVIEW (secondary)
     Traditional month calendar
     Shows occupancy % per day, arrival/departure counts
     Used by managers for planning
```

---

## 2. Room Grid Calendar (Primary View)

This is a horizontal timeline grid. Industry standard for hotel PMS.

```text
URL: /dashboard/calendar/

┌──────────────────────────────────────────────────────────────────────────┐
│  ROOM CALENDAR            ◀ Apr 2026 ▶       [Today] [Week] [2 Weeks]  │
│  Hotel: Mumbai Seaside                        [Filter by Room Type ▾]   │
├────────┬──────┬──────┬──────┬──────┬──────┬──────┬──────┬──────┬────────┤
│  Room  │ Apr 7│ Apr 8│ Apr 9│Apr 10│Apr 11│Apr 12│Apr 13│Apr 14│ ...    │
│        │ Mon  │ Tue  │ Wed  │ Thu  │ Fri  │ Sat  │ Sun  │ Mon  │        │
├────────┼──────┴──────┴──────┼──────┴──────┴──────┴──────┼──────┼────────┤
│        │                    │                            │      │        │
│ 101    │ ████ Rajesh K. ████│ ░░░░░░░░░░░░░░░░░░░░░░░░ │      │        │
│ Std    │ (Airbnb) #BK-1042 │         (Available)        │      │        │
│        │                    │                            │      │        │
├────────┼──────┬─────────────┴────────────────────────────┴──────┤────────┤
│        │      │                                                  │        │
│ 102    │(avl) │ ████████ Priya M. ████████████████████████████  │        │
│ Std    │      │ (Walk-in) #BK-1045    Check-out: Apr 15         │        │
│        │      │                                                  │        │
├────────┼──────┴──────┬──────┬────────────────────────────┬──────┤────────┤
│        │             │      │                            │      │        │
│ 103    │ ██ Amit S. ██│(avl) │ ████ John D. (Booking.com) │      │        │
│ Dlx    │ #BK-1039    │      │ #BK-1048  Foreign guest    │      │        │
│        │             │      │                            │      │        │
├────────┼─────────────┴──────┴──────┬─────────────────────┴──────┤────────┤
│        │                           │                            │        │
│ 104    │ ░░░░░ MAINTENANCE ░░░░░░░ │ ████ Sneha R. ████████████│        │
│ Dlx    │ (Blocked - AC repair)     │ (Phone) #BK-1050          │        │
│        │                           │                            │        │
├────────┼───────────────────────────┴────────────────────────────┤────────┤
│        │                                                        │        │
│ 105    │ ████████████████ Group: Wedding Party ████████████████ │        │
│ Suite  │ #BK-1035  (8 nights)  ₹32,000 total                   │        │
│        │                                                        │        │
└────────┴────────────────────────────────────────────────────────┴────────┘

Legend:
  ████  = Occupied (reservation bar — color-coded by status)
  ░░░░  = Blocked / Maintenance
  (avl) = Available (empty cell)

Color coding:
  🟦 Blue    = Confirmed (not yet checked in)
  🟩 Green   = Checked In
  🟨 Yellow  = Due for checkout today
  🟥 Red     = Overdue checkout / No-show
  ⬜ Grey    = Blocked / Maintenance
  🟪 Purple  = OTA booking (Airbnb, Booking.com)
```

### Interactions

```text
Click on a reservation bar:
  → Opens reservation detail sidebar/modal
  → Shows: guest name, dates, rate, balance, status
  → Quick actions: check-in, check-out, edit, cancel

Click on an empty cell:
  → Opens "New Reservation" form
  → Room + date pre-filled from where they clicked
  → Fast walk-in booking flow

Drag a reservation bar:
  → Move to different room (room change)
  → Extend/shorten stay (modify dates)
  → Confirmation dialog before saving

Hover on a reservation bar:
  → Tooltip with key details (guest phone, source, amount)
```

---

## 3. Monthly Overview Calendar

```text
URL: /dashboard/calendar/monthly/

┌──────────────────────────────────────────────────────────┐
│  APRIL 2026                              ◀ Month ▶      │
├────────┬────────┬────────┬────────┬────────┬────────┬────┤
│  Mon   │  Tue   │  Wed   │  Thu   │  Fri   │  Sat   │Sun │
├────────┼────────┼────────┼────────┼────────┼────────┼────┤
│        │        │   1    │   2    │   3    │   4    │  5 │
│        │        │ 9/15   │ 10/15  │ 11/15  │ 14/15  │15/15│
│        │        │  60%   │  67%   │  73%   │  93%   │100%│
│        │        │ ▲3 ▼2  │ ▲2 ▼1  │ ▲4 ▼3  │ ▲5 ▼1  │▲2▼0│
├────────┼────────┼────────┼────────┼────────┼────────┼────┤
│   6    │   7    │   8    │   9    │  10    │  11    │ 12 │
│ 13/15  │ 10/15  │ 10/15  │ 11/15  │ 12/15  │ 14/15  │15/15│
│  87%   │  67%   │  67%   │  73%   │  80%   │  93%   │100%│
│ ▲1 ▼3  │ ▲0 ▼3  │ ▲2 ▼2  │ ▲3 ▼2  │ ▲3 ▼2  │ ▲4 ▼2  │▲3▼2│
├────────┼────────┼────────┼────────┼────────┼────────┼────┤
│  ...                                                      │
└──────────────────────────────────────────────────────────┘

Each cell shows:
  - Date
  - Occupied / Total rooms (e.g., 9/15)
  - Occupancy % (color-coded: green > 80%, yellow 50-80%, red < 50%)
  - ▲ Arrivals  ▼ Departures count

Click on a date → switches to Room Grid Calendar for that date
```

---

## 4. Availability Query Logic

```text
How the calendar computes availability:

Room is AVAILABLE on a date if:
  1. Room.status != 'maintenance' AND Room.status != 'blocked'
  2. No ReservationRoom exists where:
     - reservation.status IN ('confirmed', 'checked_in')
     - AND date >= reservation_room.check_in_date
     - AND date < reservation_room.check_out_date
     (check_out_date is exclusive — room is free on checkout day after checkout)

Room is OCCUPIED on a date if:
  A ReservationRoom exists where:
  - reservation.status IN ('confirmed', 'checked_in')
  - AND date >= reservation_room.check_in_date
  - AND date < reservation_room.check_out_date
```

### Query for Calendar View

```text
To render the grid for Hotel X, 14-day view starting from Apr 7:

  Step 1: Get all rooms for hotel
    SELECT * FROM room WHERE hotel_id = X AND is_active = true
    ORDER BY room_number

  Step 2: Get all reservations overlapping with date range
    SELECT rr.*, r.guest_id, r.status, r.confirmation_number, r.source,
           g.first_name, g.last_name
    FROM reservation_room rr
    JOIN reservation r ON r.id = rr.reservation_id
    JOIN guest g ON g.id = r.guest_id
    WHERE r.hotel_id = X
      AND r.status IN ('confirmed', 'checked_in')
      AND rr.check_in_date < '2026-04-21'   -- end of view
      AND rr.check_out_date > '2026-04-07'  -- start of view

  Step 3: In Python, build the grid
    For each room:
      For each date in range:
        Find matching reservation (if any)
        Mark cell as occupied/available

Performance for 15 rooms × 14 days:
  210 cells to fill, typically 20-40 active reservations
  One query for rooms, one query for reservations
  Total: 2 queries, < 10ms
  No caching needed.
```

---

## 5. Conflict Prevention

```text
What prevents double-booking on the calendar?

  Layer 1: Visual
    Calendar shows occupied cells — staff won't book an occupied room

  Layer 2: Application
    Before creating ReservationRoom, check:
      SELECT COUNT(*) FROM reservation_room rr
      JOIN reservation r ON r.id = rr.reservation_id
      WHERE rr.room_id = :room_id
        AND r.status IN ('confirmed', 'checked_in')
        AND rr.check_in_date < :new_checkout
        AND rr.check_out_date > :new_checkin
    If count > 0 → reject with error "Room already booked for these dates"

  Layer 3: Database
    Unique constraint on availability (handled via exclusion constraint):
      PostgreSQL range exclusion:
        EXCLUDE USING gist (
          room_id WITH =,
          daterange(check_in_date, check_out_date) WITH &&
        )
      This makes double-booking IMPOSSIBLE at the database level,
      even if two staff click "book" at the exact same millisecond.

  All three layers work together. Database constraint is the final safety net.
```

---

## 6. Calendar Tech Stack

```text
Frontend rendering:
  NOT a JS calendar library (FullCalendar etc.)
  Custom HTML table rendered by Django template.

  Why:
  - Hotel grid calendar is a specialized layout (rooms × dates)
  - Standard calendar libraries are designed for events-on-days, not room grids
  - Custom HTML table + CSS gives full control over layout
  - HTMX for interactions (no full-page reloads)

  Interactions powered by:
  - HTMX: Click cell → load reservation form in sidebar (no page reload)
  - HTMX: Navigate dates → swap table body only
  - Minimal JS: Drag-to-move reservations (optional, Phase 2)
  - CSS: Color coding, hover tooltips

  No React, no Vue, no heavyweight JS needed.
```

---

## 7. Calendar URL Parameters

```text
/dashboard/calendar/
  ?start=2026-04-07          ← Start date (default: today)
  &days=14                   ← Number of days to show (7, 14, 30)
  &room_type=deluxe          ← Filter by room type (optional)
  &status=available          ← Filter: available, occupied, all

/dashboard/calendar/monthly/
  ?month=2026-04              ← Month to show (default: current)
```

---

## 8. Today's Dashboard Widgets (from Calendar Data)

The staff dashboard home uses the same availability data:

```text
/dashboard/ (home page)

┌──────────────────────────────────────────────────────────────┐
│  TODAY: April 11, 2026 (Friday)          Mumbai Seaside      │
├──────────────┬──────────────┬──────────────┬─────────────────┤
│  🏠 Occupied │  ✅ Available │  ▲ Arrivals  │  ▼ Departures  │
│   12 / 15    │    3 rooms   │   4 today    │   2 today      │
│    (80%)     │              │              │                 │
├──────────────┴──────────────┴──────────────┴─────────────────┤
│                                                              │
│  TODAY'S ARRIVALS (4)                                        │
│  ┌────────────────────────────────────────────────────────┐  │
│  │ #BK-1048  John D.       Dlx 103   Booking.com  2:00PM│  │
│  │ #BK-1049  Meera P.      Std 101   Walk-in      -----  │  │
│  │ #BK-1050  Sneha R.      Dlx 104   Phone        3:30PM│  │
│  │ #BK-1051  Vikram S.     Std 102   Airbnb       -----  │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                              │
│  TODAY'S DEPARTURES (2)                                      │
│  ┌────────────────────────────────────────────────────────┐  │
│  │ #BK-1039  Amit S.       Dlx 103   ₹800 balance  ⚠️    │  │
│  │ #BK-1042  Rajesh K.     Std 101   ₹0 balance    ✅    │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                              │
│  HOUSEKEEPING                                                │
│  ┌────────────────────────────────────────────────────────┐  │
│  │ 🟢 Clean: 101, 102, 105                                │  │
│  │ 🟡 In Progress: 103                                     │  │
│  │ 🔴 Dirty: 104 (checkout expected)                       │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                              │
│  PENDING PAYMENTS                                            │
│  ┌────────────────────────────────────────────────────────┐  │
│  │ #BK-1039  Amit S.       ₹800    [Collect Payment]      │  │
│  │ #BK-1045  Priya M.      ₹2,400  [Collect Payment]      │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```
