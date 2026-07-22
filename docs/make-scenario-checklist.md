# Make.com Scenario 5728637 — Verification Checklist
**Scenario Name:** Phase 2 - SEO Audit Draft-Queue v2
**Purpose:** Takes prospect data → Claude generates SEO audit → Creates Gmail draft
**Status when you open it:** Inactive (paused) — correct

---

## PRE-CHECK (Before opening scenario)
- [ ] You are logged into make.com with listingcontentco@gmail.com account
- [ ] You are in the correct team (My Team / listingcontentco)
- [ ] Scenario 5728637 shows as **Inactive** in the scenarios list

---

## MODULE 1 — Tools (Basic Trigger)
Click the purple Tools module and verify:
- [ ] Module type shows: **Basic trigger**
- [ ] You can see prospect data rows with these fields:
  - first_name, last_name, email, company_name, website
  - product_1_title, product_1_desc
  - product_2_title, product_2_desc
  - product_3_title, product_3_desc
- [ ] There is at least 1 data row present (Jane Smith test row)
- [ ] Click **OK** to close without changes

---

## MODULE 2 — Anthropic Claude (Simple Text Prompt)
Click the brown/orange Anthropic Claude module and verify:
- [ ] **Model** field shows: `claude-sonnet-4-6`
- [ ] **Max Tokens** field shows: `2000`
- [ ] **Text Prompt** field is NOT empty — should contain a multi-line prompt starting with:
  *"You are an expert e-commerce SEO copywriter..."*
- [ ] The prompt references these variables from Module 1:
  - `{{1.product_1_title}}`
  - `{{1.product_2_title}}`
  - `{{1.product_3_title}}`
  - `{{1.product_1_desc}}`
  - `{{1.product_2_desc}}`
  - `{{1.product_3_desc}}`
- [ ] Click **OK** to close without changes

---

## MODULE 3 — Gmail (Create a Draft)
Click the Gmail/Google module and verify:
- [ ] **Connection** shows: a Gmail account (listingcontentco@gmail.com)
  - If connection is empty → click Add → sign in with listingcontentco@gmail.com
- [ ] **To** field contains: `{{1.email}}`
- [ ] **Subject** field contains: something like *"I audited 3 products from {{1.company_name}}"*
- [ ] **Body Type** is set to: **HTML**
- [ ] **Content/Body** field is NOT empty — should contain HTML email with:
  - Greeting using `{{1.first_name}}`
  - Reference to `{{1.website}}`
  - The audit output: `{{2.result}}`
  - The Stripe link: `https://buy.stripe.com/5kQ7sM8Rt3lE7GLabHfrW05`
- [ ] Click **OK** to close without changes

---

## RUN TEST
- [ ] Click **Run once** in the bottom toolbar
- [ ] Watch all 3 modules turn green ✅
- [ ] Go to **listingcontentco@gmail.com Drafts** folder in Gmail
- [ ] Confirm a new draft email appeared addressed to `jane@examplestore.com`
- [ ] Open the draft and verify:
  - [ ] Subject line looks correct
  - [ ] Greeting says "Hi Jane"
  - [ ] Before/after audit content is present (not blank)
  - [ ] Stripe checkout link is clickable
  - [ ] Your signature is at the bottom

---

## IF SOMETHING IS WRONG

**Module 2 Text Prompt is empty:**
Paste this into the Text Prompt field:
```
You are an expert e-commerce SEO copywriter. Create a Before and After audit for 3 products. Plain text only, no markdown, no code blocks.

PRODUCT 1
Before Title: {{1.product_1_title}}
After Title: [optimized under 80 chars]
After Meta Description: [under 160 chars]
After Keywords: [6 comma separated tags]

PRODUCT 2
Before Title: {{1.product_2_title}}
After Title: [optimized under 80 chars]
After Meta Description: [under 160 chars]
After Keywords: [6 comma separated tags]

PRODUCT 3
Before Title: {{1.product_3_title}}
After Title: [optimized under 80 chars]
After Meta Description: [under 160 chars]
After Keywords: [6 comma separated tags]

Descriptions for context:
1. {{1.product_1_desc}}
2. {{1.product_2_desc}}
3. {{1.product_3_desc}}
```

**Gmail connection is missing:**
1. Click Add next to the connection field
2. Select Google Mail
3. Sign in with listingcontentco@gmail.com
4. Allow all permissions
5. Click Save

**Draft not appearing in Gmail:**
- Check spam/all mail folders
- Make sure the Gmail connection is listingcontentco@gmail.com (not byron92@gmail.com)
- Check the execution log in Make for any error messages

---

## AFTER SUCCESSFUL TEST — ACTIVATION CHECKLIST
Only activate when you're ready to send real outreach:
- [ ] Review the email copy in the Gmail draft — does it sound right?
- [ ] Confirm Stripe link works (click it, verify $497 product loads)
- [ ] Update Module 1 with first real prospect's data (replace Jane Smith)
- [ ] Set scenario to **Active**
- [ ] Monitor first 3 drafts before letting it run in batch

---
*Checklist prepared: July 22, 2026*
*Scenario ID: 5728637*
*Next step after activation: Load real prospect CSV into 03_Prospect_CSVs_Incoming*
