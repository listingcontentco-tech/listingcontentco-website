# Cold Email Domain Warmup Plan
**Domain:** listingcontentco.com
**Email:** byron@listingcontentco.com
**Goal:** Warm up sending reputation before cold outreach to 18+ prospects
**Start date:** After Zoho DNS verification (expected July 24-25, 2026)

---

## WHY WARMUP MATTERS
A brand new domain has zero sending reputation. Gmail, Outlook, and spam filters
will route cold emails straight to spam if you send too many too fast. A 2-week
warmup builds trust with email providers before you start cold outreach.

---

## WEEK 1 — TRUST BUILDING (Days 1-7)
**Goal:** Establish sending history with real, engaged recipients

| Day | Action | Volume |
|-----|--------|--------|
| 1 | Send test email to yourself (listingcontentco@gmail.com) and reply to it | 2 emails |
| 2 | Email 2-3 people you know personally from byron@listingcontentco.com and ask them to reply | 4-6 emails |
| 3 | Send the onboarding email template to yourself, open it, click the link | 2 emails |
| 4 | Email 3-4 more contacts, have them reply and mark as important | 6-8 emails |
| 5 | Forward some emails between byron@ and listingcontentco@gmail.com | 4 emails |
| 6 | Send 5 emails to personal contacts, ask for replies | 10 emails |
| 7 | Rest day — no sending |  |

**Week 1 total:** ~30 emails sent, all with replies
**Key rule:** Every email must get a reply. Engagement signals = good reputation.

---

## WEEK 2 — RAMP UP (Days 8-14)
**Goal:** Gradually increase volume, introduce prospect-style emails

| Day | Action | Volume |
|-----|--------|--------|
| 8 | Send 3 outreach drafts to friendly contacts for feedback | 3 emails |
| 9 | Send 5 outreach-style emails to warm contacts | 5 emails |
| 10 | Send 7 emails — mix of outreach style and personal | 7 emails |
| 11 | Send 10 emails | 10 emails |
| 12 | Send 10 emails | 10 emails |
| 13 | Send 15 emails | 15 emails |
| 14 | Full send ready — start real cold outreach at 15-20/day max | 15-20 |

**Week 2 total:** ~65-70 emails
**Key rule:** Never send more than 50 cold emails/day from a new domain. Start at 15-20.

---

## ONGOING SENDING RULES (Once Warmed Up)
- Max 20-30 cold emails per day from byron@listingcontentco.com
- Always include plain text version (no heavy HTML)
- Always include unsubscribe language ("reply STOP to unsubscribe")
- Never use spam trigger words: "FREE", "GUARANTEED", "CLICK HERE", "LIMITED TIME"
- Space sends throughout the day — not all at once
- Monitor spam rates — if above 2%, pause and investigate
- Always send from same IP/domain — consistency builds reputation

---

## TECHNICAL SETUP CHECKLIST (Complete After Zoho Verified)
- [ ] SPF record added to Namecheap DNS
- [ ] DKIM record added to Namecheap DNS  
- [ ] DMARC record added to Namecheap DNS
- [ ] Zoho SMTP credentials added to Make scenario 5728637
- [ ] Test email sent and received cleanly
- [ ] Email signature configured in Zoho

---

## SPF / DKIM / DMARC RECORDS TO ADD
After Zoho verifies the domain, add these to Namecheap Advanced DNS:

**SPF (TXT record):**
- Host: @
- Value: v=spf1 include:zoho.com ~all

**DKIM:** Zoho will provide this after verification — adds to Namecheap as TXT

**DMARC (TXT record):**
- Host: _dmarc
- Value: v=DMARC1; p=none; rua=mailto:byron@listingcontentco.com

---
*Last updated: July 24, 2026*
*ListingContent Co — byron@listingcontentco.com*
