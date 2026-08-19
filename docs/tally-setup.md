# LCC Fulfillment — Live Reference

**Last verified: August 19, 2026** — every value below was read from the live
system on this date, not from memory. If you change any of it, update this file
in the same sitting.

---

## THE THREE ADDRESSES YOU WILL ACTUALLY NEED

| What | Value |
|---|---|
| **Intake form (Tally)** | `https://tally.so/r/rjb8GR` |
| **Make webhook (LIVE)** | `https://hook.us2.make.com/c9ipfn52h53ow5j9maa4sjftn4pd58pi` |
| **Render endpoint** | `https://listingcontentco-website.onrender.com/process` |

The Tally form can be opened directly — you do NOT need to pay to reach it.
Stripe just redirects there after checkout.

### DEAD — do not use
`https://hook.us2.make.com/6475jqwcfnhyxpb4y3an3ahb9ooyf4nh` (hook 2613610,
"Tally Intake Form Trigger"). It has `scenarioId: null` — nothing listens to it.
Anything posted there vanishes silently. This URL was in the old version of this
doc and cost an hour on Aug 19 2026.

---

## IDs

- Make scenario: **5749860** — ListingContent - Tally Intake → Zero Touch Fulfillment
- Make hook: **2621348** — "LCC Tally Intake Hook v2"
- Store Qualifier scenario: **5757638**
- Prospect datastore: **122585**
- Stripe account: `acct_1TiINuK9ai1S2Ri8` (AI Automation Projects)
- Render health check: `GET /health` → returns `max_products`

### Stripe payment links redirecting to the intake form
All three point at `tally.so/r/rjb8GR?order_id={CHECKOUT_SESSION_ID}`:
- `buy.stripe.com/5kQ7sM8Rt3lE7GLabHfrW05` — $497, active, unlimited
- `buy.stripe.com/14AdRagjVcWe2mrfw1frW06` — active, limit 5 uses
- `buy.stripe.com/9B64gA3x91dw5yD3NjfrW08` — INACTIVE, was limit 1

---

## HOW TO RUN A TEST WITHOUT PAYING

1. Open `https://tally.so/r/rjb8GR` directly.
2. Email → your own address. Name / store → anything.
3. Upload a product CSV in Shopify export format.
4. Platform → Shopify. Submit.
5. Watch scenario 5749860 in Make. `EXECUTION_START` means Tally reached Make;
   the run sits open while Render works.
6. Success = delivery email with CSV attached and a product count in the summary.

A 500-product test catalog lives at:
`https://raw.githubusercontent.com/listingcontentco-tech/listingcontentco-website/main/tests/loadtest_catalog.csv`

`order_id` is normally filled by Stripe's redirect. Opening the form directly
leaves it blank — type anything if the form objects.

---

## CAPACITY — MEASURED, NOT ESTIMATED

### The hard ceiling is Make's HTTP timeout: 300 seconds.
Make caps that field at 300 (`validate.max`). It cannot be raised. Render must
finish the entire catalog and return the CSV inside that window, because the
call is fully synchronous — the CSV comes back as `csv_base64` in the response
body and Make attaches it to the email.

### Measured per-product cost
Every fulfillment run before Aug 19 2026 processed exactly **8 products**
(confirmed across 5 delivery emails, Jul 27 – Aug 7). Durations for those runs:
76s, 78s, 85s, 88s, 105s, 106s, 108s.

That works out to roughly **11.5 seconds per product**, sequential. Slower than
raw model speed would suggest — likely Render's shared CPU.

### Before parallelization (pre-Aug 19)
`process_catalog.py` looped one product at a time with a 0.5s sleep between each.
Real ceiling: **~26 products**. The advertised "up to 100" was never deliverable.

### After parallelization (Aug 19 2026)
32-worker `ThreadPoolExecutor`, sleep removed. `MAX_PRODUCTS` default 100 → 500.
Projected 500 products: **~180–200 seconds**. Inside the 300s limit but not
comfortably. A Render cold start (30–60s) can push it over.

**Watch the elapsed time in Make.** Above 250 seconds, drop the qualifier gate to
300 products or move to the async architecture.

### Rate limits are NOT a constraint
Anthropic org is on **Scale tier**: 10,000 requests/min on Sonnet 4.x, 10M input
tokens/min, 2M output tokens/min. A 500-product job uses ~330 req/min — about 3%.

---

## KNOWN LIMITATIONS

**Qualifier can't count past 250.** `products.json?limit=250` is Shopify's max
per page and there's no pagination, so `sku_count` tops out at 250. The gate is
set to 500, which therefore can never fire. A genuine 900-SKU store reads as 250,
passes qualification, then exceeds fulfillment capacity. Fixing this needs a
Repeater + Aggregator restructure of scenario 5757638.

**WooCommerce fetch caps at 100** (`per_page=100`, Woo's max).

**Outreach is off.** All five sending scenarios are deactivated after the
pipeline was found emailing ZeroBounce-flagged do_not_mail and role_based
addresses. Nothing reaches a prospect until that is resolved.

**Contaminated records.** Everything currently at QUALIFIED was scored when the
fetch was capped at 25 products. Those `sku_count` values are ceiling artifacts
and need re-running through the corrected qualifier before any outreach.

---

## MAKE GOTCHAS (hard-won, do not relearn)

- Blueprint pushes silently relocate 8 boolean HTTP params (`serializeUrl`,
  `shareCookies`, `rejectUnauthorized`, `followRedirect`, `useQuerystring`,
  `gzip`, `useMtls`, `followAllRedirects`) from `mapper` to `parameters`.
  Always re-read the blueprint after a push. `isinvalid: false` does not mean
  the scenario will execute.
- Tool-type scenarios cannot have their blueprint edited via API at all.
- Datastore `AddRecord` with `overwrite: true` **erases every field not in the
  payload**. This destroyed emails in scenario 5763542 until fixed Aug 19 2026 —
  always carry `email` and `first_name` through explicitly.
- `filterRows` returns column values as numeric indices, not header names.
- `updateCell` silently no-ops without `valueInputOption: "USER_ENTERED"`.
- Cloudinary calls need `rejectUnauthorized: false` or they throw a cert error.
