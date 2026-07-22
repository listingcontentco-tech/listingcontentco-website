# Make Scenario 5728637 — Copy-Paste Reference
**Use this when the Make UI shows blank fields — paste directly into each module.**

---

## MODULE 2 — Anthropic Claude Text Prompt
**Field:** Text Prompt
**Copy everything between the lines:**

---
You are an expert e-commerce SEO copywriter. Create a Before and After audit for 3 products.

Return ONLY a clean HTML snippet — no markdown, no code fences, no plain text. Use only these HTML tags: <p>, <b>, <ul>, <li>. No <html>, <body>, <head>, <style>, or <table> tags.

Format it exactly like this for each product:

<p><b>1. {{1.product_1_title}}</b></p>
<ul>
<li><b>Original Title:</b> {{1.product_1_title}}</li>
<li><b>Optimized Title:</b> [your SEO optimized version under 80 chars]</li>
<li><b>Optimized Meta Description:</b> [compelling description under 160 chars]</li>
<li><b>Top Keywords:</b> [6 comma-separated tags]</li>
</ul>

<p><b>2. {{1.product_2_title}}</b></p>
<ul>
<li><b>Original Title:</b> {{1.product_2_title}}</li>
<li><b>Optimized Title:</b> [your SEO optimized version under 80 chars]</li>
<li><b>Optimized Meta Description:</b> [compelling description under 160 chars]</li>
<li><b>Top Keywords:</b> [6 comma-separated tags]</li>
</ul>

<p><b>3. {{1.product_3_title}}</b></p>
<ul>
<li><b>Original Title:</b> {{1.product_3_title}}</li>
<li><b>Optimized Title:</b> [your SEO optimized version under 80 chars]</li>
<li><b>Optimized Meta Description:</b> [compelling description under 160 chars]</li>
<li><b>Top Keywords:</b> [6 comma-separated tags]</li>
</ul>

Descriptions for context:
1. {{1.product_1_desc}}
2. {{1.product_2_desc}}
3. {{1.product_3_desc}}
---

**Other Module 2 settings:**
- Model: claude-sonnet-4-6
- Max Tokens: 2000

---

## MODULE 3 — Gmail Create Draft
**Field:** Content (HTML Body)
**Copy everything between the lines:**

---
<p>Hi {{1.first_name}},</p>

<p>I was browsing <b>{{1.website}}</b> and ran a quick SEO audit on a few of your product listings. Sharing what I found — no strings attached.</p>

<p>Here's what I found:</p>

{{2.result}}

<p>I can optimize your <b>entire product catalog</b> — titles, meta descriptions, keyword tags, and HTML descriptions — with a <b>48-hour turnaround</b>. You get back an import-ready CSV that uploads directly into your store in minutes.</p>

<p><a href="https://buy.stripe.com/5kQ7sM8Rt3lE7GLabHfrW05" style="background-color:#10B981;color:#000000;padding:10px 20px;text-decoration:none;border-radius:6px;font-weight:bold;display:inline-block">👉 Get Your Full Catalog Optimized — $497</a></p>

<p>Happy to answer any questions — just reply here.</p>

<p>Best,<br><b>Byron Thomas</b><br>ListingContent Co<br><a href="https://listingcontentco.com">listingcontentco.com</a></p>
---

**Other Module 3 settings:**
- To: {{1.email}}
- Subject: I audited 3 products from {{1.company_name}} — here's what I found
- Body Type: HTML (rawHtml)
- Connection: listingcontentco@gmail.com

---

## WHY THE UI SHOWS BLANK
Make's API stores the prompt correctly but the UI sometimes fails to render
long text fields that were set via API. Pasting manually fixes it permanently.
After you paste and save, it will show correctly going forward.

---
*Last updated: July 22, 2026*
