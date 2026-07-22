# Webhook Server Setup Guide
**File:** `scripts/webhook_server.py`
**Purpose:** HTTP endpoint that receives Make.com order payloads, runs catalog optimization, and returns the output CSV URL.

---

## QUICK START (Local Testing)

```bash
# 1. Clone the repo
git clone https://github.com/listingcontentco-tech/listingcontentco-website.git
cd listingcontentco-website

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set environment variables
cp .env.example .env
# Edit .env and fill in ANTHROPIC_API_KEY at minimum

# 4. Run the server
python scripts/webhook_server.py

# Server starts at http://localhost:8000
```

---

## ENVIRONMENT VARIABLES

| Variable | Required | Description |
|---|---|---|
| `ANTHROPIC_API_KEY` | ✅ Yes | Your Anthropic API key |
| `GDRIVE_OPTIMIZED_FOLDER_ID` | Recommended | Google Drive folder for output CSVs |
| `WEBHOOK_SECRET` | Recommended | Shared secret to validate Make.com requests |
| `GOOGLE_SERVICE_ACCOUNT_JSON` | Optional | JSON string of Google service account for Drive upload |
| `MAX_PRODUCTS` | Optional | Max products per order (default: 100) |
| `PORT` | Optional | Server port (default: 8000) |

---

## API REFERENCE

### POST /process
Accepts a JSON payload and returns the optimized catalog URL.

**Request:**
```json
{
  "order_id": "cs_stripe_abc123",
  "client_email": "jane@examplestore.com",
  "client_name": "Jane Smith",
  "company_name": "Example Store",
  "csv_url": "https://drive.google.com/uc?id=FILE_ID&export=download",
  "platform": "shopify",
  "limit": 100
}
```

**Success Response (200):**
```json
{
  "status": "success",
  "order_id": "cs_stripe_abc123",
  "products_optimized": 47,
  "products_failed": 0,
  "output_filename": "optimized_ExampleStore_2026-07-22_143022.csv",
  "output_csv_url": "https://drive.google.com/file/d/.../view",
  "processing_time_seconds": 142.3,
  "message": "Successfully optimized 47 products in 142.3s"
}
```

**Error Response (400/500):**
```json
{
  "status": "error",
  "message": "Missing required fields: csv_url"
}
```

### GET /health
Returns server status and config check.

### GET /
Returns API documentation.

---

## DEPLOYMENT — RENDER.COM (Recommended)

1. Go to [render.com](https://render.com) → New → Web Service
2. Connect your GitHub repo: `listingcontentco-tech/listingcontentco-website`
3. Configure:
   - **Name:** `listingcontent-processor`
   - **Root Directory:** *(leave blank)*
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn scripts.webhook_server:app --bind 0.0.0.0:$PORT --workers 2 --timeout 300`
   - **Instance Type:** Free (or Starter for production)
4. Add Environment Variables:
   - `ANTHROPIC_API_KEY` = your key
   - `GDRIVE_OPTIMIZED_FOLDER_ID` = `1GZvimTRVyAGsScbPM3Kcf-j0Uqma635y`
   - `WEBHOOK_SECRET` = any random string (copy this for Make.com)
5. Click **Deploy**
6. Your webhook URL will be: `https://listingcontent-processor.onrender.com/process`

---

## MAKE.COM INTEGRATION

Once deployed, add an HTTP module to your Make.com fulfillment scenario:

**Module:** HTTP → Make a Request
**URL:** `https://listingcontent-processor.onrender.com/process`
**Method:** POST
**Headers:**
- `Content-Type: application/json`
- `X-Webhook-Secret: your_secret_here`

**Body (JSON):**
```json
{
  "order_id": "{{stripe_session_id}}",
  "client_email": "{{client_email}}",
  "client_name": "{{client_name}}",
  "company_name": "{{company_name}}",
  "csv_url": "{{tally_csv_upload_url}}",
  "platform": "{{platform}}"
}
```

**Parse Response:** Map `output_csv_url` for the next module (Gmail delivery).

---

## TIMEOUT CONSIDERATIONS

Processing 100 products takes ~10 minutes. Configure:
- Render: Set timeout to 600 seconds in service settings
- Make.com: HTTP module timeout to 300+ seconds
- Gunicorn: `--timeout 300` (already in start command above)

For large catalogs (100+ products), consider:
1. Using Make's built-in Anthropic module (no server needed, proven working)
2. Processing in batches of 25 and aggregating results
3. Upgrading Render to a paid instance for longer timeouts

---

## SECURITY

- Always set `WEBHOOK_SECRET` in production
- Never commit `.env` to GitHub (protected by `.gitignore`)
- Rotate `ANTHROPIC_API_KEY` if ever exposed
- Validate `csv_url` domain if locking down to specific sources

---
*Last updated: July 22, 2026*
*ListingContent Co — support@listingcontentco.com*
