#!/usr/bin/env python3
"""
ListingContent Co — Catalog SEO Processor
==========================================
Accepts a Shopify-format product CSV, runs each product through
Claude via the Anthropic API, and outputs a fully optimized
Shopify-ready CSV with updated titles, descriptions, meta fields,
keyword tags, and image alt text.

Usage:
    python process_catalog.py --input products.csv --output optimized.csv
    python process_catalog.py --input products.csv --output optimized.csv --limit 10
"""

import anthropic
import argparse
import csv
import json
import logging
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

# ---------------------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------------------

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
MODEL = "claude-sonnet-4-6"
MAX_TOKENS = 1500
MAX_RETRIES = 3
RETRY_DELAY = 5  # seconds between retries on rate limit

# Products are optimized concurrently. Each product is one independent
# Anthropic call, so this is pure I/O wait — threads are cheap and the
# only real ceiling is the account rate limit.
#
# Org is on Scale tier: 10,000 requests/min on Sonnet 4.x. At 32 workers
# a 500-product catalog issues ~500 requests over ~90s, which is roughly
# 330 req/min — about 3% of the available limit.
PARALLEL_WORKERS = int(os.getenv("PARALLEL_WORKERS", 32))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# SHOPIFY CSV FIELD MAPPING
# These are the standard Shopify product CSV column headers.
# We read from these and write back to them.
# ---------------------------------------------------------------------------

SHOPIFY_READ_FIELDS = [
    "Handle",
    "Title",
    "Body (HTML)",
    "Vendor",
    "Product Category",
    "Type",
    "Tags",
    "Image Src",
    "Image Alt Text",
    "SEO Title",
    "SEO Description",
    "Variant Price",
]

# Fields we will UPDATE in the output CSV
SHOPIFY_WRITE_FIELDS = {
    "Title": "optimized_title",
    "Body (HTML)": "html_description",
    "Tags": "keyword_tags",
    "Image Alt Text": "image_alt_text",
    "SEO Title": "meta_title",
    "SEO Description": "meta_description",
}

# ---------------------------------------------------------------------------
# SEO OPTIMIZATION PROMPT
# ---------------------------------------------------------------------------

def build_prompt(product: dict) -> str:
    return f"""You are an expert e-commerce SEO copywriter specializing in Shopify product optimization.

Optimize the following product and return ONLY a valid JSON object — no extra text, no markdown, no code fences.

Return exactly these keys:
{{
  "optimized_title": "Keyword-rich product title under 80 characters",
  "meta_title": "SEO meta title strictly under 60 characters",
  "meta_description": "Compelling meta description strictly under 160 characters",
  "keyword_tags": "8 comma-separated keyword tags relevant to this product",
  "image_alt_text": "Descriptive image alt text under 125 characters",
  "html_description": "<p>Opening benefit statement.</p><h2>Key Features</h2><ul><li><strong>Feature 1</strong> — benefit explanation</li><li><strong>Feature 2</strong> — benefit explanation</li><li><strong>Feature 3</strong> — benefit explanation</li></ul><p>Closing conversion statement.</p>"
}}

ACCURACY RULES — THESE MATTER MORE THAN ANYTHING ELSE BELOW:

You have NOT seen this product. You have only the text supplied at the bottom of
this prompt. The merchant will publish whatever you write to real customers, and
they carry the legal and financial risk for every claim in it.

NEVER assert any of the following unless the words appear in the supplied title
or description:
- Materials or composition (cotton, linen, soy wax, ceramic, brass, stainless,
  "100% anything", "natural materials", "high-quality materials")
- Care instructions (machine-washable, dishwasher-safe, wipe-clean, hand-wash)
- Performance or durability claims (weather-resistant, waterproof, fade-resistant,
  UV-resistant, tarnish-resistant, drip-free, long-lasting, clean-burning)
- Construction or process claims (hand-poured, handcrafted, artisan, hand-woven)
- Dimensions, capacity, weight, or quantity not already stated
- Certifications, safety claims, or origin claims

COLOUR AND TEXTURE WORDS ARE NOT MATERIALS. Words in the title such as Sand,
Clay, Slate, Ivory, Rust, Fog, Sage, Ochre, Charcoal, Linen, Woven, Textured,
Matte or Folded describe appearance only. NEVER infer a material from them.
"Clay Mug" does not mean ceramic. "Sand Clock" does not mean glass. "Linen
Cushion" does not mean linen fabric. If the material is not stated in plain
words in the supplied text, do not name a material at all.

A single fabricated attribute can cause the merchant a return, a chargeback, or a
false-advertising complaint. Being general and accurate is ALWAYS better than
being specific and wrong.

If the supplied description is empty or missing, write ONLY from the words in the
title. A shorter, honest description is a success. Padding it with invented
detail is a failure.

Subjective and aesthetic language IS allowed: stylish, versatile, simple, classic,
elegant, understated. These are opinions, not factual claims about the product.

NEVER mention price, cost, discounts, or value-for-money in any field. The store
displays price separately, and hardcoded prices go stale the moment the merchant
changes them.

If two products are variants of the same item (different size or colour), write
genuinely distinct copy for each — do not reuse near-identical paragraphs.

Rules:
- meta_title MUST be under 60 characters — count carefully
- meta_description MUST be under 160 characters — count carefully
- optimized_title MUST be under 80 characters
- keyword_tags must be exactly 8 tags separated by commas
- html_description must use proper HTML tags (p, h2, ul, li, strong)
- Write for conversion AND search intent — not just keyword stuffing
- Never use the word "best" in titles (Google filters it)
- If you cannot fill three Key Features accurately from the supplied text, write
  two. Never invent a third.

Product to optimize:
Title: {product.get('Title', 'Unknown Product')}
Description: {product.get('Body (HTML)', 'No description provided')}
Category: {product.get('Product Category', product.get('Type', 'General'))}
Vendor: {product.get('Vendor', 'Unknown')}
Current Tags: {product.get('Tags', 'None')}"""


# ---------------------------------------------------------------------------
# ANTHROPIC API CALL WITH RETRY
# ---------------------------------------------------------------------------

def optimize_product(client: anthropic.Anthropic, product: dict, row_num: int) -> dict | None:
    prompt = build_prompt(product)

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            log.info(f"  Row {row_num}: Sending to Claude (attempt {attempt}/{MAX_RETRIES})...")

            message = client.messages.create(
                model=MODEL,
                max_tokens=MAX_TOKENS,
                messages=[{"role": "user", "content": prompt}]
            )

            raw = message.content[0].text.strip()

            # Strip any accidental markdown fences
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
            raw = raw.strip()

            result = json.loads(raw)

            # Validate required keys are present
            required = ["optimized_title", "meta_title", "meta_description",
                        "keyword_tags", "image_alt_text", "html_description"]
            missing = [k for k in required if k not in result]
            if missing:
                log.warning(f"  Row {row_num}: Missing keys in response: {missing}")
                return None

            # Enforce character limits
            if len(result["meta_title"]) > 60:
                result["meta_title"] = result["meta_title"][:57] + "..."
                log.warning(f"  Row {row_num}: meta_title truncated to 60 chars")

            if len(result["meta_description"]) > 160:
                result["meta_description"] = result["meta_description"][:157] + "..."
                log.warning(f"  Row {row_num}: meta_description truncated to 160 chars")

            if len(result["optimized_title"]) > 80:
                result["optimized_title"] = result["optimized_title"][:77] + "..."
                log.warning(f"  Row {row_num}: optimized_title truncated to 80 chars")

            log.info(f"  Row {row_num}: ✅ Optimized — '{result['optimized_title']}'")
            return result

        except json.JSONDecodeError as e:
            log.error(f"  Row {row_num}: JSON parse error on attempt {attempt}: {e}")
            log.debug(f"  Raw response: {raw[:200]}")
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY)

        except anthropic.RateLimitError:
            log.warning(f"  Row {row_num}: Rate limited. Waiting {RETRY_DELAY * attempt}s...")
            time.sleep(RETRY_DELAY * attempt)

        except anthropic.APIError as e:
            log.error(f"  Row {row_num}: API error on attempt {attempt}: {e}")
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY)

    log.error(f"  Row {row_num}: ❌ Failed after {MAX_RETRIES} attempts. Skipping.")
    return None


# ---------------------------------------------------------------------------
# CSV PROCESSING
# ---------------------------------------------------------------------------

def process_csv(input_path: str, output_path: str, limit: int | None = None):
    if not ANTHROPIC_API_KEY:
        log.error("ANTHROPIC_API_KEY environment variable not set.")
        sys.exit(1)

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    input_file = Path(input_path)
    if not input_file.exists():
        log.error(f"Input file not found: {input_path}")
        sys.exit(1)

    log.info(f"Reading input CSV: {input_path}")

    rows = []
    fieldnames = []

    with open(input_path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames or []
        for row in reader:
            rows.append(row)

    if not rows:
        log.error("Input CSV is empty.")
        sys.exit(1)

    # Only process rows that have a Handle AND a Title (skip variant rows)
    product_rows = [r for r in rows if r.get("Handle") and r.get("Title")]
    variant_rows = [r for r in rows if not r.get("Title") and r.get("Handle")]

    log.info(f"Found {len(product_rows)} product rows, {len(variant_rows)} variant rows")

    if limit:
        product_rows = product_rows[:limit]
        log.info(f"Limiting to first {limit} products")

    # Process each product row
    successful = 0
    failed = 0
    optimized_rows = []

    workers = max(1, min(PARALLEL_WORKERS, len(product_rows)))
    log.info(f"Optimizing {len(product_rows)} products with {workers} parallel workers")
    parallel_start = time.time()

    # Submit every product at once and collect results by index so the
    # output CSV keeps the exact row order of the input.
    results: list[dict | None] = [None] * len(product_rows)

    def _worker(args):
        idx, row = args
        try:
            return idx, optimize_product(client, row, idx + 1)
        except Exception as e:
            log.error(f"  Row {idx + 1}: Unhandled worker error: {e}")
            return idx, None

    with ThreadPoolExecutor(max_workers=workers) as pool:
        for idx, result in pool.map(_worker, list(enumerate(product_rows))):
            results[idx] = result

    log.info(f"Parallel optimization finished in {round(time.time() - parallel_start, 1)}s")

    for i, (row, result) in enumerate(zip(product_rows, results), 1):
        if result:
            # Update the row with optimized content
            updated_row = dict(row)
            updated_row["Title"] = result["optimized_title"]
            updated_row["Body (HTML)"] = result["html_description"]
            updated_row["SEO Title"] = result["meta_title"]
            updated_row["SEO Description"] = result["meta_description"]
            updated_row["Tags"] = result["keyword_tags"]
            # Only update Image Alt Text on the first image row
            if updated_row.get("Image Src"):
                updated_row["Image Alt Text"] = result["image_alt_text"]
            optimized_rows.append(updated_row)
            successful += 1
        else:
            # Keep original row on failure
            optimized_rows.append(row)
            failed += 1

    # Merge variant rows back in (preserving original order by handle)
    all_output_rows = []
    handles_seen = {}

    for row in optimized_rows:
        handle = row.get("Handle")
        handles_seen[handle] = row
        all_output_rows.append(row)

    for row in variant_rows:
        handle = row.get("Handle")
        if handle in handles_seen:
            all_output_rows.append(row)

    # Write output CSV
    log.info(f"Writing output CSV: {output_path}")

    # Ensure output directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(all_output_rows)

    log.info("=" * 50)
    log.info(f"✅ Complete! Results:")
    log.info(f"   Products processed: {len(product_rows)}")
    log.info(f"   Successfully optimized: {successful}")
    log.info(f"   Failed (original kept): {failed}")
    log.info(f"   Output file: {output_path}")
    log.info("=" * 50)

    return successful, failed


# ---------------------------------------------------------------------------
# CLI ENTRY POINT
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="ListingContent Co — Shopify Catalog SEO Processor"
    )
    parser.add_argument(
        "--input", "-i",
        required=True,
        help="Path to input Shopify product CSV"
    )
    parser.add_argument(
        "--output", "-o",
        required=True,
        help="Path for optimized output CSV"
    )
    parser.add_argument(
        "--limit", "-l",
        type=int,
        default=None,
        help="Limit number of products to process (for testing)"
    )

    args = parser.parse_args()
    process_csv(args.input, args.output, args.limit)


if __name__ == "__main__":
    main()
