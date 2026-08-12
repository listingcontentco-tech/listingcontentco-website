#!/usr/bin/env python3
"""
ListingContent Co — Webhook Server
====================================
Flask HTTP server that receives order payloads from Make.com,
downloads the client's product CSV, runs it through process_catalog.py,
uploads the optimized CSV to Google Drive, and returns the result URL.

Endpoints:
    POST /process     — Main processing endpoint
    GET  /health      — Health check
    GET  /            — Status page

Environment Variables Required:
    ANTHROPIC_API_KEY       — Anthropic API key
    GDRIVE_OPTIMIZED_FOLDER_ID — Google Drive folder ID for output
    WEBHOOK_SECRET          — Optional shared secret for request validation
"""

import base64
import hashlib
import hmac
import json
import logging
import os
import sys
import tempfile
import time
import traceback
import urllib.request
from datetime import datetime
from pathlib import Path

from flask import Flask, jsonify, request
import requests

# ---------------------------------------------------------------------------
# SETUP
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
log = logging.getLogger(__name__)

app = Flask(__name__)

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
GDRIVE_FOLDER_ID = os.getenv("GDRIVE_OPTIMIZED_FOLDER_ID", "1GZvimTRVyAGsScbPM3Kcf-j0Uqma635y")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "")
PORT = int(os.getenv("PORT", 8000))
MAX_PRODUCTS = int(os.getenv("MAX_PRODUCTS", 100))

# Public /audit endpoint: no auth, so rate limit by IP.
AUDIT_HITS: dict[str, list[float]] = {}
AUDIT_LIMIT = int(os.getenv("AUDIT_LIMIT", 5))
AUDIT_WINDOW = 3600  # one hour

# Shopify sits behind Cloudflare, which blocks Python's default User-Agent.
BROWSER_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/122.0 Safari/537.36"
)

ALLOWED_ORIGINS = {
    "https://listingcontentco.com",
    "https://www.listingcontentco.com",
    "https://listingcontentco-website.pages.dev",
}


def _cors(resp):
    """Allow the public site to call /audit from the browser."""
    origin = request.headers.get("Origin", "")
    resp.headers["Access-Control-Allow-Origin"] = (
        origin if origin in ALLOWED_ORIGINS else "https://listingcontentco.com"
    )
    resp.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
    resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
    resp.headers["Access-Control-Max-Age"] = "86400"
    return resp

# ---------------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------------

def validate_secret(req) -> bool:
    """Validate optional shared webhook secret."""
    if not WEBHOOK_SECRET:
        return True
    incoming = req.headers.get("X-Webhook-Secret", "")
    return hmac.compare_digest(incoming, WEBHOOK_SECRET)


def download_csv(url: str, dest_path: str) -> bool:
    """Download a CSV from a URL to a local path.

    Uses requests with a browser User-Agent. Tally file URLs are served
    through Cloudflare, which rejects Python's default urllib User-Agent
    ("Python-urllib/3.x") with a 403. urlretrieve therefore always failed
    on Tally uploads even though the URL and access token were valid.
    """
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
        ),
        "Accept": "*/*",
    }
    try:
        log.info(f"Downloading CSV from: {url[:80]}...")
        resp = requests.get(url, headers=headers, timeout=60, allow_redirects=True)
        log.info(f"Download response: HTTP {resp.status_code}, "
                 f"content-type={resp.headers.get('content-type')}")
        if resp.status_code != 200:
            log.error(f"Download failed: HTTP {resp.status_code} — {resp.text[:200]}")
            return False
        with open(dest_path, "wb") as fh:
            fh.write(resp.content)
        size = Path(dest_path).stat().st_size
        log.info(f"Downloaded {size} bytes")
        return size > 0
    except Exception as e:
        log.error(f"Download failed: {e}")
        return False


def run_optimization(input_path: str, output_path: str, limit: int = None) -> dict:
    """Run process_catalog.py on the input CSV."""
    # Import inline to avoid circular deps and allow standalone server use
    sys.path.insert(0, str(Path(__file__).parent))
    try:
        from process_catalog import process_csv
        successful, failed = process_csv(input_path, output_path, limit)
        return {"successful": successful, "failed": failed, "error": None}
    except Exception as e:
        log.error(f"Optimization error: {traceback.format_exc()}")
        return {"successful": 0, "failed": 0, "error": str(e)}


def upload_to_drive(file_path: str, filename: str) -> str | None:
    """
    Upload optimized CSV to Google Drive using the Drive API.
    Returns the file's web view URL or None on failure.

    Note: Requires GOOGLE_SERVICE_ACCOUNT_JSON env var with service account credentials,
    OR uses the gdrive CLI if available. For MVP, returns a local path reference
    and logs instructions. Full Drive upload requires google-api-python-client.
    """
    try:
        # Try google-api-python-client if available
        from googleapiclient.discovery import build
        from googleapiclient.http import MediaFileUpload
        from google.oauth2 import service_account

        sa_json = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
        if not sa_json:
            log.warning("GOOGLE_SERVICE_ACCOUNT_JSON not set — skipping Drive upload")
            return None

        creds = service_account.Credentials.from_service_account_info(
            json.loads(sa_json),
            scopes=["https://www.googleapis.com/auth/drive.file"]
        )
        service = build("drive", "v3", credentials=creds)

        file_metadata = {
            "name": filename,
            "parents": [GDRIVE_FOLDER_ID]
        }
        media = MediaFileUpload(file_path, mimetype="text/csv")
        uploaded = service.files().create(
            body=file_metadata,
            media_body=media,
            fields="id,webViewLink"
        ).execute()

        url = uploaded.get("webViewLink", "")
        log.info(f"Uploaded to Drive: {url}")
        return url

    except ImportError:
        log.warning("google-api-python-client not installed — Drive upload skipped")
        return None
    except Exception as e:
        log.error(f"Drive upload failed: {e}")
        return None


# ---------------------------------------------------------------------------
# ROUTES
# ---------------------------------------------------------------------------

@app.route("/audit", methods=["POST", "OPTIONS"])
def audit():
    """
    Public free audit. Takes a store URL, fetches the public products
    endpoint, scores description quality and returns a sample rewrite.

    No auth: this is the lead magnet. Rate limited by IP.
    """
    if request.method == "OPTIONS":
        return _cors(jsonify({"ok": True}))

    ip = request.headers.get("X-Forwarded-For", request.remote_addr or "unknown").split(",")[0].strip()
    now = time.time()
    hits = [t for t in AUDIT_HITS.get(ip, []) if now - t < AUDIT_WINDOW]
    if len(hits) >= AUDIT_LIMIT:
        return _cors(jsonify({
            "status": "rate_limited",
            "message": "That's a few audits in a row. Try again in an hour, or email byron@listingcontentco.com and I'll run it for you."
        })), 429
    hits.append(now)
    AUDIT_HITS[ip] = hits

    payload = request.get_json(silent=True) or {}
    raw = (payload.get("url") or "").strip()
    if not raw:
        return _cors(jsonify({"status": "error", "message": "Enter a store URL to audit."})), 400

    domain = raw.lower().replace("https://", "").replace("http://", "").split("/")[0].replace("www.", "")
    if "." not in domain or " " in domain:
        return _cors(jsonify({"status": "error", "message": f"'{raw}' doesn't look like a store address. Try something like yourstore.com"})), 400

    try:
        r = requests.get(
            f"https://{domain}/products.json?limit=25",
            headers={"User-Agent": BROWSER_UA},
            timeout=15,
        )
        products = (r.json() or {}).get("products", []) if r.status_code == 200 else []
    except Exception as e:
        log.info("Audit fetch failed for %s: %s", domain, e)
        products = []

    if not products:
        return _cors(jsonify({
            "status": "not_supported",
            "domain": domain,
            "message": "Couldn't read a product catalog there. This works on Shopify stores with a public catalog — check the address, or email byron@listingcontentco.com and I'll take a look by hand."
        }))

    # Sample spread across the catalog so we don't grab three variants of one item
    idx = [i for i in (0, 4, 9) if i < len(products)] or [0]
    sample = [products[i] for i in idx]

    def strip_html(s):
        import re
        return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", s or "")).strip()

    scored = []
    for p in sample:
        body = strip_html(p.get("body_html", ""))
        scored.append({"title": p.get("title", ""), "description": body, "length": len(body)})

    thin = sum(1 for s in scored if s["length"] < 100)
    avg = round(sum(s["length"] for s in scored) / len(scored))

    rewrites = []
    if ANTHROPIC_API_KEY:
        listing = "\n".join(
            f"{i+1}. Title: {s['title']} | Description: {s['description'] or '(none)'}"
            for i, s in enumerate(scored)
        )
        prompt = f"""You are an e-commerce SEO copywriter reviewing product listings.

ACCURACY RULES — THESE OVERRIDE EVERYTHING ELSE:
You have NOT seen these products. You only have the text below. Never assert a
material, dimension, care instruction, certification, or performance claim
(waterproof, machine-washable, 100% cotton, hand-poured, fade-resistant) unless
those exact words appear in the supplied text. Subjective language (stylish,
versatile, classic) is fine. Never mention price.
If the description is empty, write only from the title. Short and accurate beats
long and invented.

For each product return JSON only, no preamble, no code fences:
{{"items":[{{"current_title":"","current_description":"","issue":"","suggested_title":"","suggested_description":"","keywords":["","","","","",""]}}]}}

"issue" = one plain sentence on what is costing them search traffic.
"suggested_title" under 80 chars. "suggested_description" 2 short sentences.

Products:
{listing}"""
        try:
            resp = requests.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": ANTHROPIC_API_KEY,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": "claude-sonnet-4-6",
                    "max_tokens": 2000,
                    "messages": [{"role": "user", "content": prompt}],
                },
                timeout=60,
            )
            txt = resp.json()["content"][0]["text"].strip()
            txt = txt.replace("```json", "").replace("```", "").strip()
            rewrites = json.loads(txt).get("items", [])
        except Exception as e:
            log.warning("Audit rewrite failed for %s: %s", domain, e)

    return _cors(jsonify({
        "status": "ok",
        "domain": domain,
        "products_found": len(products),
        "sampled": len(scored),
        "thin_count": thin,
        "avg_description_length": avg,
        "verdict": (
            "Most of these pages give Google almost nothing to index."
            if thin >= 2 else
            "Your descriptions are in reasonable shape — better than most stores we scan."
        ),
        "items": rewrites,
    }))


@app.route("/", methods=["GET"])
def index():
    return jsonify({
        "service": "ListingContent Co — Catalog SEO Webhook Server",
        "status": "running",
        "version": "1.0.0",
        "endpoints": {
            "POST /process": "Submit a catalog for SEO optimization",
            "GET /health": "Health check"
        }
    })


@app.route("/health", methods=["GET"])
def health():
    checks = {
        "server": "ok",
        "anthropic_key": "set" if ANTHROPIC_API_KEY else "MISSING",
        "drive_folder": GDRIVE_FOLDER_ID,
        "max_products": MAX_PRODUCTS
    }
    status = 200 if ANTHROPIC_API_KEY else 503
    return jsonify(checks), status


@app.route("/process", methods=["POST"])
def process():
    """
    Main endpoint. Accepts JSON payload:
    {
        "order_id": "stripe_xxx",           # required
        "client_email": "user@store.com",   # required
        "client_name": "Jane Smith",        # optional
        "company_name": "Jane's Store",     # optional
        "csv_url": "https://...",           # required: URL to download CSV from
        "platform": "shopify",              # optional: shopify/woocommerce/bigcommerce
        "notes": "Focus on top 20 SKUs",    # optional
        "limit": 50                         # optional: max products to process
    }

    Returns:
    {
        "status": "success" | "error",
        "order_id": "...",
        "products_optimized": 47,
        "products_failed": 0,
        "output_csv_url": "https://drive.google.com/...",
        "output_filename": "optimized_..._2026-07-22.csv",
        "processing_time_seconds": 142,
        "message": "..."
    }
    """
    start_time = time.time()

    # ── Auth ──
    if not validate_secret(request):
        log.warning("Rejected request: invalid webhook secret")
        return jsonify({"status": "error", "message": "Unauthorized"}), 401

    # ── Parse body ──
    if not request.is_json:
        return jsonify({"status": "error", "message": "Content-Type must be application/json"}), 400

    data = request.get_json(silent=True)
    if not data:
        return jsonify({"status": "error", "message": "Invalid or empty JSON body"}), 400

    # ── Validate required fields ──
    required = ["order_id", "client_email", "csv_url"]
    missing = [f for f in required if not data.get(f)]
    if missing:
        return jsonify({
            "status": "error",
            "message": f"Missing required fields: {', '.join(missing)}"
        }), 400

    order_id = data["order_id"]
    client_email = data["client_email"]
    client_name = data.get("client_name", "Client")
    company_name = data.get("company_name", "Store")
    csv_url = data["csv_url"]
    platform = data.get("platform", "shopify").lower()
    limit = data.get("limit", MAX_PRODUCTS)

    log.info(f"Processing order {order_id} for {client_email} ({company_name})")

    # ── Check API key ──
    if not ANTHROPIC_API_KEY:
        return jsonify({
            "status": "error",
            "message": "ANTHROPIC_API_KEY not configured on server"
        }), 503

    # ── Work in temp directory ──
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    safe_company = "".join(c for c in company_name if c.isalnum() or c in "-_")[:30]
    output_filename = f"optimized_{safe_company}_{timestamp}.csv"

    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = os.path.join(tmpdir, "raw_catalog.csv")
        output_path = os.path.join(tmpdir, output_filename)

        # ── Download CSV ──
        if not download_csv(csv_url, input_path):
            return jsonify({
                "status": "error",
                "order_id": order_id,
                "message": "Failed to download CSV from provided URL. Check the URL is publicly accessible."
            }), 400

        # ── Run optimization ──
        log.info(f"Starting optimization — limit: {limit} products")
        result = run_optimization(input_path, output_path, limit=limit)

        if result["error"]:
            return jsonify({
                "status": "error",
                "order_id": order_id,
                "message": f"Optimization failed: {result['error']}"
            }), 500

        if not Path(output_path).exists():
            return jsonify({
                "status": "error",
                "order_id": order_id,
                "message": "Optimization completed but output file not found"
            }), 500

        # ── Upload to Drive (optional backup — requires GOOGLE_SERVICE_ACCOUNT_JSON) ──
        drive_url = upload_to_drive(output_path, output_filename)

        # ── Read optimized CSV so it can be returned to the caller ──
        # The output file lives on ephemeral disk and is lost when the request
        # ends. Returning it in the response lets the caller (Make) attach it
        # directly to the customer's email — no Drive dependency required.
        csv_b64 = None
        csv_bytes_len = 0
        try:
            with open(output_path, "rb") as fh:
                raw = fh.read()
            csv_bytes_len = len(raw)
            csv_b64 = base64.b64encode(raw).decode("ascii")
            log.info(f"Returning CSV inline: {csv_bytes_len} bytes "
                     f"({len(csv_b64)} chars base64)")
        except Exception as e:
            log.error(f"Could not read output CSV for inline return: {e}")

        elapsed = round(time.time() - start_time, 1)

        response = {
            "status": "success",
            "order_id": order_id,
            "client_email": client_email,
            "client_name": client_name,
            "company_name": company_name,
            "platform": platform,
            "products_optimized": result["successful"],
            "products_failed": result["failed"],
            "output_filename": output_filename,
            "output_csv_url": drive_url or "Drive upload not configured — see server logs",
            "csv_base64": csv_b64,
            "csv_size_bytes": csv_bytes_len,
            "processing_time_seconds": elapsed,
            "message": f"Successfully optimized {result['successful']} products in {elapsed}s"
        }

        log.info(f"Order {order_id} complete: {result['successful']} products in {elapsed}s")
        return jsonify(response), 200


@app.route("/process", methods=["GET"])
def process_docs():
    """Quick docs for the /process endpoint."""
    return jsonify({
        "endpoint": "POST /process",
        "content_type": "application/json",
        "required_fields": {
            "order_id": "string — Stripe session or order ID",
            "client_email": "string — client email for delivery",
            "csv_url": "string — publicly accessible URL to download the product CSV"
        },
        "optional_fields": {
            "client_name": "string",
            "company_name": "string",
            "platform": "shopify | woocommerce | bigcommerce (default: shopify)",
            "notes": "string — any special instructions",
            "limit": "integer — max products to process (default: 100)"
        },
        "headers": {
            "X-Webhook-Secret": "string — shared secret (if WEBHOOK_SECRET env var is set)"
        }
    })


# ---------------------------------------------------------------------------
# ERROR HANDLERS
# ---------------------------------------------------------------------------

@app.errorhandler(404)
def not_found(e):
    return jsonify({"status": "error", "message": "Endpoint not found"}), 404


@app.errorhandler(405)
def method_not_allowed(e):
    return jsonify({"status": "error", "message": "Method not allowed"}), 405


@app.errorhandler(500)
def internal_error(e):
    log.error(f"Unhandled error: {traceback.format_exc()}")
    return jsonify({"status": "error", "message": "Internal server error"}), 500


# ---------------------------------------------------------------------------
# ENTRY POINT
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    log.info("=" * 50)
    log.info("ListingContent Co — Webhook Server")
    log.info(f"Port: {PORT}")
    log.info(f"Anthropic API Key: {'SET' if ANTHROPIC_API_KEY else 'MISSING ⚠️'}")
    log.info(f"Drive Folder ID: {GDRIVE_FOLDER_ID}")
    log.info(f"Max Products: {MAX_PRODUCTS}")
    log.info("=" * 50)
    app.run(host="0.0.0.0", port=PORT, debug=False)
