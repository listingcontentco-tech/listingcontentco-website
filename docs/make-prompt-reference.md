# Make Scenario 5728637 — Copy-Paste Reference
**Last updated: July 22, 2026**

---

## MODULE 2 — Anthropic Claude
**Model:** claude-sonnet-4-6
**Max Tokens:** 2000
**Text Prompt:**

```
You are an expert e-commerce SEO copywriter. Create a Before and After audit for 3 products.

CRITICAL RULES:
- Return ONLY clean HTML using ONLY these tags: <p>, <b>, <ul>, <li>
- NO markdown, NO backticks, NO code fences, NO plain text outside HTML tags
- NO <html>, <body>, <head>, <style>, <table>, <pre>, <code> tags
- Do NOT wrap output in ``` or ```html or any code block
- Output must render as normal formatted text in Gmail

Format EXACTLY like this:

<p><b>1. [Product 1 Name]</b></p><ul><li><b>Original Title:</b> [original]</li><li><b>Optimized Title:</b> [SEO version under 80 chars]</li><li><b>Optimized Meta Description:</b> [under 160 chars]</li><li><b>Top Keywords:</b> [6 comma-separated tags]</li></ul><p><b>2. [Product 2 Name]</b></p><ul><li><b>Original Title:</b> [original]</li><li><b>Optimized Title:</b> [SEO version under 80 chars]</li><li><b>Optimized Meta Description:</b> [under 160 chars]</li><li><b>Top Keywords:</b> [6 comma-separated tags]</li></ul><p><b>3. [Product 3 Name]</b></p><ul><li><b>Original Title:</b> [original]</li><li><b>Optimized Title:</b> [SEO version under 80 chars]</li><li><b>Optimized Meta Description:</b> [under 160 chars]</li><li><b>Top Keywords:</b> [6 comma-separated tags]</li></ul>

Products to optimize:
1. Title: {{1.product_1_title}} | Description: {{1.product_1_desc}}
2. Title: {{1.product_2_title}} | Description: {{1.product_2_desc}}
3. Title: {{1.product_3_title}} | Description: {{1.product_3_desc}}
```

---

## MODULE 3 — Gmail Create Draft
**To:** {{1.email}}
**Subject:** I audited 3 products from {{1.company_name}} — here's what I found
**Body Type:** HTML (rawHtml)
**Content:**

```
<p>Hi {{1.first_name}},</p>

<p>I was browsing <b>{{1.website}}</b> and ran a quick SEO audit on a few of your product listings. Sharing what I found — no strings attached.</p>

<p>Here's what I found:</p>

{{2.result}}

<p>I can optimize your <b>entire catalog</b> (titles, meta descriptions, keyword tags, and HTML descriptions) with a <b>48-hour turnaround</b> for a flat <b>$497</b>. You'll receive an import-ready CSV file that uploads straight into Shopify in two clicks.</p>

<p><a href="https://buy.stripe.com/5kQ7sM8Rt3lE7GLabHfrW05" style="background-color:#10B981;color:#000000;padding:10px 20px;text-decoration:none;border-radius:6px;font-weight:bold;display:inline-block">👉 View Catalog Pricing & Details</a></p>

<p>Happy to answer any questions — just reply here.</p>

<p>Best,<br><b>BJ Thomas</b><br>Listing Content Co.<br><a href="https://listingcontentco.com">listingcontentco.com</a></p>
```
