# Zero-Touch Automated Fulfillment Blueprint
**ListingContent Co — End-to-End Pipeline Documentation**
**Version:** 1.0 · July 22, 2026

---

## PIPELINE OVERVIEW

```
[Stripe Checkout] → [Tally Intake Form] → [Make.com] → [process_catalog.py] → [Google Drive] → [Gmail Delivery]
```

Every step after the client clicks "Buy" is fully automated. Zero manual intervention required.

---

## STAGE 1 — STRIPE PAYMENT SUCCESS

**What happens:** Client completes $497 checkout at `buy.stripe.com/5kQ7sM8Rt3lE7GLabHfrW05`

**Configuration in Stripe:**
1. Go to Stripe Dashboard → Payment Links → your $497 link
2. Click **Edit**
3. Under **After payment** → set **Confirmation page** to **Redirect to URL**
4. Set redirect URL to: `https://listingcontentco.com/thank-you.html?session={CHECKOUT_SESSION_ID}`

**Data captured at this stage:**
- Customer email
- Customer name
- Stripe session ID
- Payment confirmation

**Stripe Webhook to configure:**
- Event: `payment_intent.succeeded` or `checkout.session.completed`
- Endpoint URL: *(Make.com webhook — see Stage 2)*
- Secret: stored in `STRIPE_WEBHOOK_SECRET` env variable

---

## STAGE 2 — TALLY INTAKE FORM

**Purpose:** Collect the client's store URL and product CSV after payment

**Setup:**
1. Create a free form at tally.so
2. Form fields:
   - **Name** (pre-fill from Stripe if possible)
   - **Email** (pre-fill from Stripe)
   - **Shopify Store URL**
   - **Platform** (dropdown: Shopify / WooCommerce / BigCommerce / Other)
   - **Product CSV Upload** (file upload field)
   - **Top Priority Products** (optional text — "focus on these SKUs first")
   - **Brand Notes** (optional — keywords, competitors, tone)
3. On submission → Tally fires a webhook to Make.com

**Tally Webhook Configuration:**
- Go to Tally form → Integrations → Webhooks
- Add webhook URL: *(your Make.com scenario webhook URL)*
- Select trigger: **New submission**

**Onboarding email trigger:**
- Also set up: Stripe webhook → Make.com → Gmail sends `client-onboarding-template.md` email immediately on payment
- This happens BEFORE the Tally form, prompting the client to fill it out

---

## STAGE 3 — MAKE.COM ORCHESTRATION SCENARIO

**Scenario name:** `ListingContent - Zero Touch Fulfillment`

**Modules in order:**

```
[1] Webhooks: Custom Webhook
    ↓ Receives Tally form submission
    ↓ Payload: name, email, store_url, platform, csv_file_url, notes

[2] HTTP: GET Request
    ↓ Downloads the CSV file from Tally's file URL
    ↓ Stores as binary data

[3] Google Drive: Upload File
    ↓ Saves raw CSV to: 03_Prospect_CSVs_Incoming/{email}_{timestamp}_raw.csv
    ↓ Returns: file_id, file_url

[4] HTTP: POST to Processing Webhook
    ↓ Sends to your deployed process_catalog.py endpoint
    ↓ Body: { "csv_url": file_url, "email": email, "name": name }
    ↓ Returns: { "output_csv_url": "...", "products_optimized": 47 }

[5] Google Drive: Get File (optimized output)
    ↓ Retrieves the completed optimized CSV
    ↓ Stores in: 02_Optimized_Finished_CSVs/{email}_{timestamp}_optimized.csv

[6] Gmail: Send Email
    ↓ Uses fulfillment-delivery-template.md
    ↓ Attaches optimized CSV
    ↓ To: client email
    ↓ From: support@listingcontentco.com

[7] Google Sheets: Add Row (optional CRM logging)
    ↓ Logs: timestamp, client name, email, store URL, products optimized, delivery time
```

---

## STAGE 4 — PROCESS_CATALOG.PY DEPLOYMENT

**Option A — Render.com (Recommended, free tier available)**

1. Push `scripts/process_catalog.py` to GitHub (already done)
2. Create a new Web Service at render.com
3. Connect `listingcontentco-tech/listingcontentco-website` repo
4. Build command: `pip install anthropic`
5. Start command: `python scripts/webhook_server.py` *(see wrapper below)*
6. Add environment variable: `ANTHROPIC_API_KEY=your_key`
7. Render gives you a URL like `https://listingcontent-processor.onrender.com`

**webhook_server.py wrapper (to be built):**
```python
# Wraps process_catalog.py in a Flask HTTP endpoint
# POST /process with JSON body: { csv_url, email, name }
# Returns: { output_csv_url, products_optimized }
```

**Option B — AWS Lambda**
- Package `process_catalog.py` + `anthropic` library as a Lambda layer
- Trigger via API Gateway HTTP endpoint
- Store output in S3, return presigned URL to Make.com

**Option C — Make.com HTTP Module (Simplest, no server needed)**
- Use Make's built-in HTTP module to call Anthropic API directly
- Already proven working in our existing SEO Engine scenario (5718272)
- No deployment needed — runs entirely within Make.com
- Best for getting to zero-touch fastest

**Recommendation:** Start with Option C (Make HTTP → Anthropic API) since it's already working. Migrate to Render/Lambda when volume exceeds Make's operation limits.

---

## STAGE 5 — DELIVERY

**Gmail delivery:**
- Send from: `support@listingcontentco.com`
- Template: `docs/fulfillment-delivery-template.md`
- Attach: optimized CSV file
- CC: `listingcontentco@gmail.com` (your copy)

**Google Drive logging:**
- Raw CSV → `03_Prospect_CSVs_Incoming/`
- Optimized CSV → `02_Optimized_Finished_CSVs/`
- Order log → Google Sheet (future CRM)

---

## FULL DATA FLOW DIAGRAM

```
CLIENT                    STRIPE              MAKE.COM              CLAUDE API
  │                          │                    │                      │
  │──── Pays $497 ──────────>│                    │                      │
  │<─── Thank You Page ──────│                    │                      │
  │                          │──── Webhook ──────>│                      │
  │<─── Onboarding Email ────────────────────────│                      │
  │                          │                    │                      │
  │──── Fills Tally Form ─────────────────────── │                      │
  │  (uploads CSV)           │                    │                      │
  │                          │                    │──── API calls ──────>│
  │                          │                    │<─── Optimized JSON ──│
  │                          │                    │                      │
  │<─── Delivery Email ──────────────────────────│                      │
  │  (with optimized CSV)    │                    │                      │
```

---

## ESTIMATED PROCESSING TIMES

| Catalog Size | API Calls | Estimated Time | Cost |
|---|---|---|---|
| 10 products | 10 | ~1 minute | ~$0.15 |
| 50 products | 50 | ~5 minutes | ~$0.75 |
| 100 products | 100 | ~10 minutes | ~$1.50 |
| 500 products | 500 | ~50 minutes | ~$7.50 |

At $497/order, API costs are less than 2% of revenue even for large catalogs.

---

## NEXT BUILD STEPS (In Priority Order)

1. ✅ `process_catalog.py` — built and in GitHub
2. ☐ `scripts/webhook_server.py` — Flask wrapper for HTTP deployment
3. ☐ Tally form — create at tally.so, connect to Make webhook
4. ☐ Stripe webhook — configure `checkout.session.completed` → Make
5. ☐ Make fulfillment scenario — build the 7-module pipeline above
6. ☐ Deploy to Render.com — or use Make HTTP module for MVP
7. ☐ Google Sheets CRM log — order tracking dashboard
8. ☐ Test end-to-end with a $1 test Stripe product

---
*Blueprint version 1.0 — ListingContent Co*
*Last updated: July 22, 2026*
