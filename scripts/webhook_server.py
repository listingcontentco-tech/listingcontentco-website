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
    """Download a CSV from a URL to a local path."""
    try:
        log.info(f"Downloading CSV from: {url[:80]}...")
        urllib.request.urlretrieve(url, dest_path)
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

        # ── Upload to Drive ──
        drive_url = upload_to_drive(output_path, output_filename)

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
