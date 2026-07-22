# Post-Purchase Onboarding Email Template
**Trigger:** Immediately after Stripe $497 checkout completes
**From:** support@listingcontentco.com
**Subject:** Your catalog optimization is confirmed — here's what to do next

---

## EMAIL TEMPLATE

Hi {{first_name}},

Your order is confirmed and your catalog optimization is now in the queue. 🎉

**Order:** Full Catalog SEO Overhaul — $497
**Expected delivery:** Within 48 hours of receiving your product data

To get started, I just need your product catalog. Here are the export instructions for the most common platforms:

---

**📦 SHOPIFY**

1. Log into your Shopify admin at `yourstore.myshopify.com/admin`
2. Click **Products** in the left sidebar
3. Click **Export** (top right button)
4. Select **All products**
5. Select **CSV for Excel, Numbers, or other spreadsheet apps**
6. Click **Export products**
7. Shopify will email the CSV to your account email — download it from there

---

**🛒 WOOCOMMERCE**

1. Log into your WordPress admin dashboard
2. Go to **WooCommerce → Products**
3. Click **Export** at the top of the page
4. Leave all settings at default (exports all products)
5. Click **Generate CSV**
6. The file will download directly to your computer

---

**🏪 BIGCOMMERCE**

1. Log into your BigCommerce control panel
2. Go to **Products → Export**
3. Select **Default** as the export template
4. Click **Export**
5. Download the CSV file when it's ready

---

**📤 HOW TO SEND IT TO US**

Once you have the CSV file, simply:

**Option A — Reply to this email** and attach the CSV directly. *(Easiest)*

**Option B — Google Drive:** Upload it to any Google Drive folder and share the link by replying to this email.

**Option C — WeTransfer:** Go to wetransfer.com, upload your file, send to support@listingcontentco.com

---

**A few things that help us deliver the best results:**

- Include as many product fields as possible (title, description, price, category, SKU)
- If your store has more than 100 products, let us know which products are your top sellers or highest priority — we'll start there
- If you have any brand guidelines, target keywords, or competitor sites you admire, feel free to share those too

---

**What happens after you send it:**

✅ We confirm receipt within 1 hour
✅ Optimization begins immediately
✅ Your completed CSV lands in your inbox within 48 hours
✅ We include import instructions with the delivery

Questions? Just reply to this email — I check it throughout the day.

Talk soon,

Byron Thomas
ListingContent Co
support@listingcontentco.com
listingcontentco.com

---

## TEMPLATE VARIABLES
- `{{first_name}}` — buyer's first name from Stripe checkout
- `{{order_id}}` — Stripe order/payment ID (optional, for reference)

## SENDING NOTES
- Send immediately on payment confirmation (use Stripe webhook → Make → Gmail)
- BCC: listingcontentco@gmail.com for your own records
- Follow up manually if no CSV received within 24 hours
