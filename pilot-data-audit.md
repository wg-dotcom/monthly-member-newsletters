# Pilot data audit

## What we can prove now

The local taxonomy export contains 303 member records.

The largest primary groups are:

| Industry | Records |
| --- | ---: |
| Professional Services | 72 |
| Home Services & Trades | 66 |
| Technology & Software | 35 |
| Real Estate & Property | 23 |
| Investment & Capital | 19 |
| Health Care & Wellness | 17 |

The latest local signed-offer export ends on July 29, 2026. After filtering to Core members and removing one obvious test record, July contains:

| Metric | July result |
| --- | ---: |
| Signed offers | 32 |
| Member companies | 24 |
| Median monthly salary | $2,000 |
| Average monthly salary | $2,325 |
| Monthly payroll added | $74,400 |
| Salary range | $1,250 to $7,000 |
| Exact candidate video matches | 9 |

This headline is already useful:

> 24 Sagan members added 32 people in July. The median salary was $2,000 per month.

## What is blocked

The local signed-offer file does not include the canonical account ID. The taxonomy file uses a separate account label. Most July hires cannot be joined safely by company name alone.

The active database must provide the canonical join:

`hire.account_id -> account.id -> account.primary_taxonomy`

The active database is also required for August. The current local export stops in July.

## Data quality rules

- Exclude tests, canceled offers, and records without a valid member account.
- Count replacements separately. Do not present a replacement as fresh team growth.
- Use the signed-offer date for the first version. Change to start date only if the business wants to report people who began work that month.
- Do not fuzzy-match candidate videos. Use the candidate ID.
- Do not show a named candidate, exact salary, or intro video without the right consent.
- If fewer than three companies contributed to a segment, roll it into the parent taxonomy.

## August pull needed

The first live pull should return:

- August signed offers for active member accounts
- Canonical account ID and taxonomy
- Role title and monthly salary
- Candidate ID and approved display name
- Intro video URL and sharing permission
- AI builds launched in August and their measured result
- Member name-sharing permission

