# Payments Architecture — India

All hotels are in India. Must support all Indian payment methods.

---

## 1. Payment Gateway — Razorpay

```text
Why Razorpay (over PayU, Cashfree, etc.):
  - Best Django/Python SDK
  - Supports ALL Indian payment methods in one integration
  - Auto-settlement to hotel bank accounts
  - Dashboard for finance team
  - Reasonable pricing: 2% per transaction (negotiable at volume)
  - Good webhook reliability
  - Supports multi-account (each hotel can have its own Razorpay sub-account)
```

---

## 2. Supported Payment Methods

All handled by Razorpay — single integration covers everything.

```text
┌──────────────────────────────────────────────────────────────┐
│                 PAYMENT METHODS SUPPORTED                      │
│                                                              │
│  UPI                                                         │
│  ├── Google Pay                                              │
│  ├── PhonePe                                                 │
│  ├── Paytm UPI                                               │
│  ├── BHIM                                                    │
│  ├── Any UPI app (UPI ID / QR code)                          │
│  └── UPI Intent (opens app directly on mobile)               │
│                                                              │
│  Cards                                                       │
│  ├── Visa / Mastercard / RuPay (debit + credit)              │
│  ├── American Express                                        │
│  ├── Diners Club                                             │
│  └── EMI on credit cards (3/6/9/12 months)                   │
│                                                              │
│  Net Banking                                                 │
│  ├── All major banks (SBI, HDFC, ICICI, Axis, etc.)          │
│  └── 50+ banks supported                                     │
│                                                              │
│  Wallets                                                     │
│  ├── Paytm Wallet                                            │
│  ├── Amazon Pay                                              │
│  ├── Freecharge                                              │
│  └── MobiKwik                                                │
│                                                              │
│  Other                                                       │
│  ├── Cash (recorded manually at front desk — no gateway)     │
│  ├── Bank transfer / NEFT / RTGS (recorded manually)         │
│  └── Corporate billing (direct invoice, no gateway)          │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

---

## 3. Payment Flow

### Online Payment (UPI / Card / Net Banking / Wallet)

```text
Guest checks out or makes advance payment
        │
        ▼
Front desk clicks "Collect Payment" on folio
        │
        ▼
Django creates Razorpay Order (amount in INR, paise)
        │
        ▼
Razorpay Checkout opens (embedded in our page)
  - Guest selects payment method (UPI, card, etc.)
  - Pays on their phone / enters card details
        │
        ▼
Razorpay processes payment
        │
        ├── Success → Razorpay sends webhook to our server
        │              Django verifies signature
        │              FolioCharge (type=payment) created
        │              Folio balance updated
        │              Receipt generated
        │
        └── Failure → Guest retries or pays cash
                       No charge recorded
```

### Cash / Bank Transfer (Manual)

```text
Guest pays cash at front desk
        │
        ▼
Staff clicks "Record Cash Payment" on folio
        │
        ▼
FolioCharge (type=payment, method=cash) created
        │
        ▼
Folio balance updated
No Razorpay involved.
```

---

## 4. Multi-Hotel Payment Setup

```text
Two options:

OPTION A: Single Razorpay Account (simpler)
  - One Razorpay account for all hotels
  - All payments land in one bank account
  - Admin distributes to hotels manually
  - Good for: same owner runs all hotels

OPTION B: Razorpay Route — Split Payments (recommended for different owners)
  - One main Razorpay account
  - Each hotel is a "linked account" (sub-merchant)
  - Payments auto-settle to each hotel's bank account
  - Commission/platform fee deducted automatically
  - Good for: hotels with different owners/bank accounts

For now: Start with Option A (single account).
Add Route later if hotels have different bank accounts.
```

---

## 5. Database Changes

### New: Payment Model

| Column              | Type              | Notes                          |
|---------------------|-------------------|--------------------------------|
| id                  | PK                |                                |
| hotel               | FK → Hotel        |                                |
| folio               | FK → Folio        |                                |
| amount              | decimal(10,2)     | In INR (rupees, not paise)     |
| method              | enum              | upi, credit_card, debit_card, net_banking, wallet, cash, bank_transfer, corporate |
| status              | enum              | pending, completed, failed, refunded |
| razorpay_order_id   | varchar(50) null  | Razorpay order ID (null for cash) |
| razorpay_payment_id | varchar(50) null  | Razorpay payment ID            |
| razorpay_signature  | varchar(200) null | For verification                |
| reference_number    | varchar(100) null | For manual payments (receipt #, UTR, etc.) |
| notes               | text null         | E.g. "Cash paid at check-in"   |
| received_by         | FK → User (null)  | Staff who processed it         |
| created_at          | datetime          |                                |

### Updated: FolioCharge

```text
FolioCharge.charge_type now includes:
  room_charge, tax, food_beverage, laundry, minibar, misc, discount

Payment is NO longer a FolioCharge type.
Payments are tracked in the separate Payment model for:
  - Razorpay integration fields
  - Payment method tracking
  - Refund handling
  - Better reporting (sales vs collections)
```

### Updated: Folio

```text
Folio now computes:
  total_charges  = SUM(FolioCharge.amount)  — all charges
  total_payments = SUM(Payment.amount WHERE status=completed)
  balance        = total_charges - total_payments
```

### New: Hotel Payment Config

Added to Hotel model or separate table:

| Column                   | Type          | Notes                          |
|--------------------------|---------------|--------------------------------|
| id                       | PK            |                                |
| hotel                    | OneToOne → Hotel |                             |
| razorpay_key_id          | varchar(50)   | Per-hotel or shared Razorpay key |
| razorpay_key_secret      | varchar(100)  | Encrypted / from Secret Manager |
| razorpay_account_id      | varchar(50) null | For Route (sub-merchant)    |
| gst_number               | varchar(20)   | Hotel's GSTIN                  |
| gst_rate                 | decimal(4,2)  | Default GST % (e.g. 12.00)    |
| accepts_online_payment   | bool          | Enable/disable online payments |
| created_at               | datetime      |                                |

---

## 6. GST Handling

Hotels in India must charge GST on room tariff. Rates depend on room price.

```text
┌──────────────────────────────────────────────────────────┐
│  GST RATES FOR HOTEL ROOMS (as per current Indian law)    │
│                                                          │
│  Room tariff per night       │  GST Rate                 │
│  ───────────────────────────┼──────────────────────────  │
│  Up to ₹1,000               │  12%                      │
│  ₹1,001 to ₹7,500           │  12%                      │
│  Above ₹7,500               │  18%                      │
│                                                          │
│  GST is split:                                           │
│    CGST (Central) = half the rate                        │
│    SGST (State)   = half the rate                        │
│    Example: 12% GST = 6% CGST + 6% SGST                 │
│                                                          │
│  For inter-state guests:                                 │
│    IGST = full rate (instead of CGST + SGST)             │
│                                                          │
└──────────────────────────────────────────────────────────┘

Implementation:
  - Room charge posted → GST auto-calculated based on rate
  - FolioCharge entries created:
      1. Room charge: ₹2,000
      2. CGST 6%:     ₹120
      3. SGST 6%:     ₹120
      Total:          ₹2,240

  - GST rate can be overridden per hotel in HotelPaymentConfig
  - Invoice/receipt shows GST breakup (required by law)
```

---

## 7. Invoice / Receipt Generation

```text
Indian law requires:
  - Hotel GSTIN on every invoice
  - Guest name and address
  - HSN/SAC code (9963 for hotel accommodation)
  - CGST + SGST (or IGST) breakup
  - Invoice number (sequential per hotel)

Implementation:
  - Generate PDF invoice on checkout / payment
  - Store in Cloud Storage
  - Downloadable from folio detail page
  - Uses Django template → HTML → PDF (weasyprint or xhtml2pdf)
```

---

## 8. Refund Flow

```text
Guest requests refund (cancellation, overcharge, etc.)
        │
        ▼
Manager/admin initiates refund from folio
        │
        ├── Online payment → Razorpay refund API
        │   - Full or partial refund
        │   - Refund goes back to original payment method
        │   - Razorpay handles UPI/card/wallet refund automatically
        │   - Takes 5-7 business days
        │
        └── Cash payment → Record cash refund manually
            - Staff hands back cash
            - Payment record updated to status=refunded
        │
        ▼
Folio balance recalculated
Audit log entry created
```

---

## 9. Sales Dashboard — Updated for Payments

The admin sales view now tracks payment methods:

```text
SUPER ADMIN SALES DASHBOARD
┌──────────────────────────────────────────────────────────────┐
│  COLLECTIONS BY PAYMENT METHOD          [This Month]         │
│                                                              │
│  UPI:            ₹8,50,000  (45%)   ████████████████         │
│  Cash:           ₹4,20,000  (22%)   █████████                │
│  Credit Card:    ₹3,10,000  (16%)   ███████                  │
│  Debit Card:     ₹1,80,000  (10%)   ████                     │
│  Net Banking:    ₹90,000    (5%)    ██                        │
│  Wallet:         ₹40,000    (2%)    █                         │
│                                                              │
│  TOTAL COLLECTED: ₹18,90,000                                 │
│  GST COLLECTED:   ₹2,26,800                                  │
│  PENDING:         ₹1,40,000                                  │
└──────────────────────────────────────────────────────────────┘
```

---

## 10. Razorpay Integration Checklist

```text
What we need from Razorpay:
  1. ✓ Razorpay account (sign up at razorpay.com)
  2. ✓ KYC verification (PAN, bank account, business docs)
  3. ✓ API Key ID + Secret (from Razorpay dashboard)
  4. ✓ Webhook secret (for payment verification)

What we build:
  1. Create Razorpay order when staff clicks "Collect Payment"
  2. Embed Razorpay Checkout.js in payment page
  3. Webhook endpoint to receive payment confirmation
  4. Signature verification (security)
  5. Payment → FolioCharge linkage
  6. Refund API integration
  7. GST calculation on room charges

Python package:
  razorpay (official Python SDK)
  pip install razorpay
```

---

## 11. Currency

```text
All amounts stored in INR (Indian Rupees).
Razorpay expects amounts in paise (₹100 = 10000 paise).

Database: stores in rupees as decimal(10,2)
Razorpay API: multiply by 100 before sending
Display: ₹ symbol, Indian number formatting (₹1,00,000 not ₹100,000)
```
