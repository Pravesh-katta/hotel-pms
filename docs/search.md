# Search Architecture

Search is the front desk's most used feature. They search 50+ times per shift.

---

## 1. Global Search Bar

Always visible in the top navbar on every page.

```text
┌──────────────────────────────────────────────────────────────┐
│  🔍 [Search guests, bookings, rooms...        ]  [Enter]     │
│                                                              │
│  Searches across:                                            │
│   - Guest name (first + last)                                │
│   - Guest phone number                                       │
│   - Guest email                                              │
│   - Booking confirmation number (#BK-XXXX)                   │
│   - Room number (101, 102, etc.)                             │
│   - External booking ID (Airbnb/OTA reference)               │
│                                                              │
│  Results appear as dropdown while typing (after 2 chars):    │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  GUESTS                                                │  │
│  │  👤 Rajesh Kumar — +91 98765 43210 — Room 103          │  │
│  │  👤 Rajesh Sharma — +91 87654 32100 — Checked out      │  │
│  │                                                        │  │
│  │  RESERVATIONS                                          │  │
│  │  📋 #BK-1042 — Rajesh Kumar — Apr 7-10 — Checked In   │  │
│  │  📋 #BK-1089 — Rajesh Sharma — Apr 15-17 — Confirmed  │  │
│  │                                                        │  │
│  │  ROOMS                                                 │  │
│  │  🚪 Room 103 — Deluxe — Occupied (Rajesh Kumar)        │  │
│  │                                                        │  │
│  │  [View all results →]                                   │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                              │
│  Click any result → navigate to that detail page.            │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

---

## 2. How It Works (HTMX Live Search)

```text
User types in search bar
      │
      ▼ (after 2 characters, debounce 300ms)
HTMX sends GET /dashboard/search/?q=rajesh
      │
      ▼
Django view runs:

  def search(request):
      q = request.GET['q']
      hotel = request.hotel  # from middleware

      guests = Guest.objects.filter(
          hotel=hotel
      ).filter(
          Q(first_name__icontains=q) |
          Q(last_name__icontains=q) |
          Q(phone__icontains=q) |
          Q(email__icontains=q)
      )[:5]

      reservations = Reservation.objects.filter(
          hotel=hotel
      ).filter(
          Q(confirmation_number__icontains=q) |
          Q(external_booking_id__icontains=q) |
          Q(guest__first_name__icontains=q) |
          Q(guest__last_name__icontains=q) |
          Q(guest__phone__icontains=q)
      ).select_related('guest')[:5]

      rooms = Room.objects.filter(
          hotel=hotel,
          room_number__icontains=q
      )[:5]

      return render(request, 'dashboard/components/search_results.html', {
          'guests': guests,
          'reservations': reservations,
          'rooms': rooms,
      })

      │
      ▼
HTMX swaps the dropdown with results (no full page reload)
```

---

## 3. Page-Level Search & Filters

Each list page has its own filters in addition to global search.

### Reservation List Filters

```text
/dashboard/reservations/

┌──────────────────────────────────────────────────────────────┐
│  RESERVATIONS                                                │
│                                                              │
│  [Search by name/phone/booking#...   ]                       │
│                                                              │
│  Status: [All ▾] [Confirmed] [Checked In] [Checked Out]     │
│  Source: [All ▾] [Walk-in] [Airbnb] [Booking.com] [Phone]   │
│  Dates:  [Check-in from] [to]   [Check-out from] [to]       │
│                                                              │
│  ┌──────┬──────────┬──────────┬────────┬────────┬─────────┐ │
│  │ #    │ Guest    │ Room     │ Dates  │ Source │ Status  │ │
│  ├──────┼──────────┼──────────┼────────┼────────┼─────────┤ │
│  │ 1042 │ Rajesh K.│ 103 Dlx  │ Apr 7-10│Airbnb │✅ In    │ │
│  │ 1043 │ Priya M. │ 101 Std  │ Apr 8-12│Walk-in│✅ In    │ │
│  │ 1044 │ John D.  │ 104 Dlx  │ Apr 10-13│B.com │🔵 Conf │ │
│  └──────┴──────────┴──────────┴────────┴────────┴─────────┘ │
│                                                              │
│  Showing 1-20 of 45    [◀ Prev] [1] [2] [3] [Next ▶]        │
│                                                              │
│  [📥 Export CSV]                                              │
└──────────────────────────────────────────────────────────────┘
```

### Guest List Filters

```text
/dashboard/guests/

  [Search by name/phone/email/ID...   ]

  Nationality: [All ▾] [Indian] [Foreign]
  Status:      [Currently staying] [All guests]

  + [📥 Export CSV]  [📥 Export for Police Report]
```

### Billing / Folio Filters

```text
/dashboard/billing/

  [Search by folio#/guest name/booking#...   ]

  Status:  [All ▾] [Open] [Settled] [Void]
  Balance: [All ▾] [Has outstanding balance] [Fully paid]

  + [📥 Export CSV]
```

### Room List Filters

```text
/dashboard/rooms/

  Status: [All ▾] [Available] [Occupied] [Dirty] [Maintenance]
  Type:   [All ▾] [Standard] [Deluxe] [Suite]
  Floor:  [All ▾] [1st] [2nd] [3rd]
```

---

## 4. Search Performance

```text
At our scale (20 hotels × 15 rooms):

  Guest table:     ~15,000 rows/year → ~75,000 in 5 years
  Reservation:     ~15,000 rows/year → ~75,000 in 5 years
  Room:            ~300 rows (static)

  Search query hits:
    - Hotel filter (hotel_id = X) narrows to ~3,750 guests per hotel in 5 years
    - icontains on indexed columns: < 10ms
    - No full-text search engine needed (no Elasticsearch, no pg_trgm)

  Indexes needed:
    Guest:       (hotel, phone)         — phone lookup is most common
    Guest:       (hotel, last_name)     — name search
    Reservation: (hotel, confirmation_number) — booking ID lookup

  Plain Django ORM with icontains is fast enough.
  PostgreSQL LIKE with B-tree index handles this at our scale.
```

---

## 5. CSV Export

```text
Every list page has an "Export CSV" button.

How it works:
  1. Staff clicks [📥 Export CSV]
  2. Django view runs the same filtered query
  3. Returns CSV file as download (Content-Type: text/csv)
  4. Browser downloads immediately

  At our scale (max ~1,000 rows per export):
    Generates in < 1 second
    No background job needed
    Synchronous response

Export formats:
  - Guest list CSV (for police reporting)
  - Reservation list CSV
  - Sales report CSV (for accountant / GST filing)
  - Folio list CSV (open balances)
  - Payment list CSV (collections report)
  - Night audit report CSV
  - GST report CSV (CGST + SGST breakup per invoice — for CA)

All exports are filtered by hotel (staff sees only their hotel).
Super admin can export across all hotels.
```

---

## 6. URL Routes

```text
/dashboard/search/                    → Global search (HTMX endpoint, returns partial HTML)
/dashboard/search/full/?q=rajesh      → Full search results page (all categories)

Export endpoints (CSV download):
/dashboard/guests/export/             → Guest list CSV
/dashboard/reservations/export/       → Reservation list CSV
/dashboard/billing/export/            → Folio/payment CSV
/dashboard/reports/sales/export/      → Sales report CSV
/dashboard/reports/gst/export/        → GST report CSV
```
