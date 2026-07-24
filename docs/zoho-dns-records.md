# Zoho DNS Records for listingcontentco.com
**Add these to Namecheap → Advanced DNS tomorrow morning**

---

## MX Records (3 total)
| Type | Host | Value | Priority |
|------|------|-------|----------|
| MX | @ | mx.zoho.com | 10 |
| MX | @ | mx2.zoho.com | 20 |
| MX | @ | mx3.zoho.com | 50 |

---

## SPF Record
| Type | Host | Value |
|------|------|-------|
| TXT | @ | v=spf1 include:zoho.com ~all |

*(If Zoho shows a different SPF value, use theirs)*

---

## DKIM Record
| Type | Host | Value |
|------|------|-------|
| TXT | zmail._domainkey | v=DKIM1; k=rsa; p=MIGfMA0GCSqGSIb3DQEBAQUAAGNADCBiQKBgQCo+Bh4wRR+jaJy8wGww1XmoJMKYS0ZxHxp1I4NgyE0SBuyszI6dWFxdVQ8N4XgkGuq2aq+xshTLwfnixUN6DRi1+v0+X0AB1O9SBv6hs/oC7NjhN0QkULeAEJD+JnZ0cD+oMzzOIl0yJCW6mrn9OoAt5I4VByyiQZL7jWjRK25iAQIDAQAB |

---

## DMARC Record (add this too for best deliverability)
| Type | Host | Value |
|------|------|-------|
| TXT | _dmarc | v=DMARC1; p=none; rua=mailto:byron@listingcontentco.com |

---

## After adding all records:
1. Go back to Zoho DNS Mapping page
2. Click **"Verify all records"**
3. All status indicators should turn green
4. Then go to **mail.zoho.com** and log in as byron@listingcontentco.com
5. Set up email forwarding to listingcontentco@gmail.com if desired

---
*Saved: July 24, 2026 — add to Namecheap in the morning*
