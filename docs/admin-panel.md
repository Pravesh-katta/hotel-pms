# Admin Panel & Sales Dashboard Architecture

---

## 1. Two-Tier Admin Design

We use **Django's built-in admin** as the super-admin backend, and a **custom dashboard** for hotel-level staff.

```text
┌─────────────────────────────────────────────────────┐
│                  SUPER ADMIN PANEL                    │
│            (Django Admin - /superadmin/)               │
│                                                       │
│  Who: super_admin role only                           │
│  What they see:                                       │
│   - All hotels and their settings                     │
│   - Sales across ALL hotels (aggregated + per-hotel)  │
│   - Staff management across all properties            │
│   - OTA connection status for all hotels              │
│   - System-wide audit logs                            │
│   - Revenue dashboard with date range filters         │
│                                                       │
│  This is the ONLY place that shows cross-hotel sales  │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│               HOTEL STAFF DASHBOARD                   │
│              (Custom Django views - /dashboard/)       │
│                                                       │
│  Who: hotel_admin, manager, front_desk, housekeeping  │
│  What they see:                                       │
│   - Only their own hotel's data                       │
│   - Role-based feature access (see below)             │
│   - hotel_admin/manager can see their hotel's sales   │
│   - front_desk sees reservations, check-in/out        │
│   - housekeeping sees room status only                │
│                                                       │
│  Data is ALWAYS filtered by request.user.hotel        │
└─────────────────────────────────────────────────────┘
```

---

## 2. Role → Feature Access Matrix

| Feature                  | super_admin | hotel_admin | manager | front_desk | housekeeping |
|--------------------------|:-----------:|:-----------:|:-------:|:----------:|:------------:|
| View ALL hotels' sales   | Yes         | No          | No      | No         | No           |
| View own hotel sales     | Yes         | Yes         | Yes     | No         | No           |
| Manage hotels            | Yes         | No          | No      | No         | No           |
| Manage staff             | Yes         | Yes (own)   | No      | No         | No           |
| Reservations (CRUD)      | Yes         | Yes         | Yes     | Yes        | No           |
| Check-in / Check-out     | Yes         | Yes         | Yes     | Yes        | No           |
| Guest management         | Yes         | Yes         | Yes     | Yes        | No           |
| Billing / Folios         | Yes         | Yes         | Yes     | View only  | No           |
| Room management          | Yes         | Yes         | Yes     | View only  | No           |
| Housekeeping tasks       | Yes         | Yes         | Yes     | No         | Yes          |
| Reports                  | Yes         | Yes         | Yes     | No         | No           |
| OTA connections          | Yes         | Yes         | No      | No         | No           |
| Audit logs               | Yes         | Yes         | Yes     | No         | No           |

---

## 3. Super Admin Sales Dashboard

This is the key screen only super_admin sees — shows sales across all hotels.

### Layout

```text
┌──────────────────────────────────────────────────────────────┐
│  SALES OVERVIEW                    [Date Range Picker]       │
│                                    [Today | Week | Month | Custom] │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐    │
│  │ Total    │  │ Total    │  │ GST      │  │ Occupancy │    │
│  │ Revenue  │  │ Collected│  │ Collected│  │ Rate (%)  │    │
│  │₹18,90,000│  │₹16,50,000│  │₹2,26,800│  │  78%      │    │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘    │
│                                                              │
│  ┌──────────┐  ┌──────────┐                                 │
│  │ Outstand.│  │ Total    │                                  │
│  │ Balance  │  │ Bookings │                                  │
│  │₹2,40,000 │  │  342     │                                  │
│  └──────────┘  └──────────┘                                 │
│                                                              │
├──────────────────────────────────────────────────────────────┤
│  SALES BY HOTEL                                              │
│                                                              │
│  Hotel Name       │ Rooms │ Occ. │ Revenue   │ Collected │ GST       │
│  ─────────────────┼───────┼──────┼───────────┼───────────┼─────────  │
│  Mumbai Seaside   │  15   │  12  │ ₹4,20,000 │ ₹3,80,000│ ₹50,400  │
│  Goa Beach Resort │  12   │  11  │ ₹3,50,000 │ ₹3,50,000│ ₹42,000  │
│  Delhi Central    │  14   │  10  │ ₹3,10,000 │ ₹2,80,000│ ₹37,200  │
│  Jaipur Heritage  │  11   │   9  │ ₹2,80,000 │ ₹2,60,000│ ₹33,600  │
│  ... (all 20+ hotels)                                        │
│                                                              │
│  TOTAL            │  260  │  203 │₹18,90,000 │₹16,50,000│₹2,26,800 │
│                                                              │
├──────────────────────────────────────────────────────────────┤
│  COLLECTIONS BY PAYMENT METHOD                               │
│                                                              │
│  UPI:          ₹8,50,000 (45%)  ████████████████             │
│  Cash:         ₹4,20,000 (22%)  █████████                    │
│  Credit Card:  ₹3,10,000 (16%)  ███████                      │
│  Debit Card:   ₹1,80,000 (10%)  ████                         │
│  Net Banking:  ₹90,000   (5%)   ██                           │
│  Wallet:       ₹40,000   (2%)   █                            │
│                                                              │
├──────────────────────────────────────────────────────────────┤
│  BOOKING SOURCES                                             │
│                                                              │
│  Walk-in: 35%  │  Airbnb: 25%  │  Booking.com: 20%         │
│  Phone: 10%    │  Website: 7%  │  Other OTA: 3%            │
│                                                              │
└──────────────────────────────────────────────────────────────┘

All amounts in ₹ (INR), Indian number format (₹1,00,000).
```

### Sales Query Strategy

```text
Charges and payments are in separate tables.

Revenue per hotel (from FolioCharge):
  SELECT hotel_id, SUM(amount)
  FROM folio_charge
  JOIN folio ON folio.id = folio_charge.folio_id
  WHERE charge_type NOT IN ('discount', 'cgst', 'sgst', 'igst')
    AND charge_date BETWEEN :start AND :end
  GROUP BY hotel_id

GST collected per hotel:
  SELECT hotel_id, SUM(amount)
  FROM folio_charge
  JOIN folio ON folio.id = folio_charge.folio_id
  WHERE charge_type IN ('cgst', 'sgst', 'igst')
    AND charge_date BETWEEN :start AND :end
  GROUP BY hotel_id

Collections per hotel (from Payment):
  SELECT hotel_id, SUM(amount)
  FROM payment
  WHERE status = 'completed'
    AND created_at BETWEEN :start AND :end
  GROUP BY hotel_id

Collections by payment method:
  SELECT method, SUM(amount)
  FROM payment
  WHERE status = 'completed'
    AND created_at BETWEEN :start AND :end
  GROUP BY method

Occupancy per hotel:
  SELECT hotel_id,
         COUNT(DISTINCT room_id) as occupied_rooms
  FROM reservation_room
  JOIN reservation ON reservation.id = reservation_room.reservation_id
  WHERE reservation.status IN ('checked_in', 'confirmed')
    AND :today BETWEEN reservation_room.check_in_date AND reservation_room.check_out_date
  GROUP BY hotel_id

Performance note:
  20 hotels × 13 rooms × 365 days = ~95,000 folio charges/year
  Trivial for PostgreSQL. No caching or materialized views needed.
```

---

## 4. Hotel Staff Dashboard Pages

For non-super-admin staff, the custom dashboard shows:

```text
/dashboard/                     → Overview (today's arrivals, departures, occupancy)
/dashboard/reservations/        → List, create, edit reservations
/dashboard/reservations/:id/    → Single reservation detail
/dashboard/calendar/            → Room availability calendar view
/dashboard/check-in/            → Today's check-ins
/dashboard/check-out/           → Today's check-outs
/dashboard/rooms/               → Room list with status
/dashboard/guests/              → Guest list and profiles
/dashboard/billing/             → Open folios, charges
/dashboard/billing/:id/         → Single folio detail
/dashboard/housekeeping/        → Room cleaning status board
/dashboard/reports/             → Hotel-level reports (manager+ only)
/dashboard/reports/sales/       → Hotel's own sales (manager+ only)
/dashboard/staff/               → Staff management (hotel_admin only)
/dashboard/settings/            → Hotel settings (hotel_admin only)
```

---

## 5. Data Isolation Enforcement

Every view and API endpoint follows this pattern:

```text
1. Middleware extracts hotel from request.user.staffprofile.hotel
2. All querysets filter by hotel automatically
3. super_admin (hotel=null) bypasses hotel filter
4. Object-level checks on create/update/delete

Flow:
  Request → Auth middleware → Hotel middleware → View → Hotel-scoped queryset → Response
```

This means:
- Front desk at Hotel A can NEVER see Hotel B's reservations
- Hotel admin at Hotel A can NEVER see Hotel B's sales
- Only super_admin sees the cross-hotel sales dashboard

---

## 6. Technology for Admin Panel

```text
Super Admin Panel:
  - Django Admin (built-in) with custom admin classes
  - Custom admin dashboard view for sales (registered in Django admin)
  - Uses Django admin's built-in auth and permission system

Hotel Staff Dashboard:
  - Custom Django views + templates
  - Django templates with HTMX for interactive updates (no SPA needed)
  - Bootstrap 5 or Tailwind for styling
  - DataTables for sortable/searchable tables
  - Chart.js for sales charts (manager+ only)

Why not a SPA:
  - Staff-facing tool, not consumer-facing
  - Django templates are faster to build
  - HTMX gives interactivity without JS framework overhead
  - Simpler deployment (no separate frontend build)
```
