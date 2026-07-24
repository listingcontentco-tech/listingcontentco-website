# Tally Intake Form Setup Guide
**Purpose:** Post-purchase form where clients submit their store details and product CSV
**Make Webhook URL:** `https://hook.us2.make.com/6475jqwcfnhyxpb4y3an3ahb9ooyf4nh`
**Make Scenario:** `5749860` — ListingContent - Tally Intake → Zero Touch Fulfillment

---

## STEP 1 — Create Your Tally Account
1. Go to **tally.so** and sign up free
2. Click **New form**
3. Name it: `ListingContent Co — Catalog Submission`

---

## STEP 2 — Build the Form Fields (EXACT ORDER MATTERS)

Add these fields in this exact order — Make maps them by position:

| # | Field Type | Label | Required |
|---|---|---|---|
| 1 | Hidden field | `order_id` | Yes |
| 2 | Email | `Email Address` | Yes |
| 3 | Short text | `Your Name` | Yes |
| 4 | Short text | `Store / Company Name` | Yes |
| 5 | File upload | `Upload Your Product CSV` | Yes |
| 6 | Dropdown | `Your Platform` | Yes |

**Dropdown options for field 6:**
- Shopify
- WooCommerce
- BigCommerce
- Magento
- Other

**Optional additional fields (add after field 6):**
- Short text: `Your Store URL`
- Long text: `Any special instructions or priority products?`

---

## STEP 3 — Set the Hidden Order ID Field
1. Click the `order_id` hidden field
2. Set default value to: `tally_{{submissionId}}`
   *(Tally auto-fills submissionId with a unique ID per submission)*

---

## STEP 4 — Configure the Thank You Page
1. Go to form Settings → After submission
2. Set message to:
   > "Thanks! We've received your catalog and will begin optimization immediately. You'll receive your optimized CSV via email within 48 hours."

---

## STEP 5 — Connect the Make Webhook
1. In your Tally form, go to **Integrations**
2. Click **Webhooks**
3. Click **Add endpoint**
4. Paste this URL:
   ```
   https://hook.us2.make.com/6475jqwcfnhyxpb4y3an3ahb9ooyf4nh
   ```
5. Select trigger: **New submission**
6. Click **Save**

---

## STEP 6 — Connect Tally to Stripe (Post-Purchase Redirect)
In your Stripe Payment Link settings:
1. Go to Stripe → Payment Links → your $497 link → Edit
2. Under **After payment** → set to **Redirect to URL**
3. Set URL to your Tally form URL:
   `https://tally.so/r/YOUR_FORM_ID`

---

## HOW THE DATA FLOWS

```
Client pays $497 on Stripe
    ↓
Redirected to Tally form
    ↓
Client fills form + uploads CSV
    ↓
Tally fires webhook to Make
    ↓
Make scenario 5749860 receives payload
    ↓
HTTP POST to Render /process endpoint
    ↓
Claude optimizes all products
    ↓
Delivery email sent to client automatically
```

---

## TALLY PAYLOAD STRUCTURE (for reference)

When Tally fires the webhook, Make receives this JSON:
```json
{
  "data": {
    "fields": [
      { "label": "order_id", "value": "tally_abc123" },
      { "label": "Email Address", "value": "client@store.com" },
      { "label": "Your Name", "value": "Jane Smith" },
      { "label": "Store / Company Name", "value": "Jane's Store" },
      { "label": "Upload Your Product CSV", "value": [{"url": "https://..."}] },
      { "label": "Your Platform", "value": "Shopify" }
    ]
  }
}
```

---
*Last updated: July 24, 2026*
*Make Webhook ID: 2613610*
*Make Scenario ID: 5749860*
