# Monthly newsletter data contract

## 1. Recipient table

| Field | Use |
| --- | --- |
| `account_id` | Canonical join key |
| `company_name` | Personalization and approved attribution |
| `contact_first_name` | Greeting |
| `contact_email` | Delivery |
| `membership_status` | Send only to active members |
| `primary_taxonomy` | Main edition |
| `specialty_taxonomy` | Narrow edition when the cohort is large enough |
| `structure_taxonomy` | Optional variation for PE-backed, franchise, or holding-company members |
| `member_strategist_id` | Reply routing and ownership |
| `newsletter_opt_out` | Suppression |

## 2. Hire table

| Field | Use |
| --- | --- |
| `hire_id` | Deduplication |
| `account_id` | Industry join |
| `candidate_id` | Exact candidate and video join |
| `role_title` | Role proof |
| `signed_offer_date` | Monthly inclusion rule |
| `start_date` | Optional future reporting rule |
| `monthly_salary_usd` | Median, range, and payroll added |
| `hire_type` | New hire, replacement, or Talent Pool |
| `status` | Include only confirmed signed offers |
| `member_name_share_ok` | Permission to name the company |
| `exact_pay_share_ok` | Permission to show exact role pay |

## 3. Candidate table

| Field | Use |
| --- | --- |
| `candidate_id` | Exact join |
| `approved_display_name` | First name and last initial by default |
| `country` | Global talent story |
| `intro_video_url` | Video button |
| `newsletter_video_consent` | Required before use |
| `video_consent_date` | Audit trail |

Candidate videos are strong proof. They are also personal data. The default should be no video until the candidate has agreed to this specific use.

## 4. AI build table

| Field | Use |
| --- | --- |
| `build_id` | Deduplication |
| `account_id` | Industry join |
| `launch_date` | Monthly inclusion rule |
| `workflow_name` | Plain description of the build |
| `problem_before` | Painful moment |
| `result_after` | Measured result |
| `metric_name` | Hours, response time, conversion, backlog, or error rate |
| `metric_before` | Baseline |
| `metric_after` | Result |
| `member_name_share_ok` | Permission to name the company |
| `build_share_ok` | Permission to show the workflow |

Do not publish a build without a result. “Built an AI agent” is not a story. “Cut estimate follow-up from two days to two hours” is a story.

## 5. Monthly aggregation

Use the previous complete calendar month.

1. Select confirmed signed offers for active members.
2. Exclude tests and cancellations.
3. Separate new hires, replacements, and Talent Pool hires.
4. Join each hire to the account by canonical account ID.
5. Group by primary taxonomy.
6. Use specialty taxonomy only when at least three companies appear in that cohort.
7. Calculate hire count, company count, median pay, pay range, and monthly payroll added.
8. Rank roles by frequency and commercial usefulness.
9. Select up to three approved hire stories and two approved AI build stories.
10. Generate one recommendation for the recipient: hire, build, or both.

## 6. Personal recommendation logic

Recommend an AI build when the work is repetitive, rules-based, high volume, and easy to check.

Recommend a hire when the work needs judgment, trust, ownership, negotiation, or persistent follow-up.

Recommend both when AI can prepare the work but a person must own the result.

| Industry need | AI handles | Person owns | Likely hire |
| --- | --- | --- | --- |
| Missed calls and slow follow-up | Transcription, tagging, routing, first draft | Exceptions, scheduling, customer recovery | Dispatcher or customer operations coordinator |
| Estimates and quotes | Data extraction, draft scope, reminder sequence | Final pricing, tradeoffs, close | Estimator or sales coordinator |
| Finance backlog | Invoice capture, reconciliation suggestions, variance flags | Close, controls, member judgment | Bookkeeper, staff accountant, or FP&A analyst |
| Client delivery | Meeting notes, task creation, status summaries | Relationship, scope, escalation | Account coordinator or client success manager |
| Sales pipeline | Research, enrichment, call QA, CRM cleanup | Messaging, objection handling, close | BDR, SDR, or RevOps specialist |
| Deal and property work | Document extraction, comp collection, first-pass memo | Thesis, diligence, negotiation | Analyst or transaction coordinator |
| Health care administration | Intake, classification, summary, denial draft | Patient communication, verification, escalation | Biller, insurance coordinator, or care coordinator |

## 7. Send and measurement

Every email has one primary CTA: `Open a hiring request`.

The secondary path is a direct reply:

> Send me the bottleneck. I will tell you if it should be a hire, an AI build, or both.

Attach these fields to every click and request:

- Newsletter month
- Industry edition
- Member account ID
- CTA position
- Recommended role or build
- Member Strategist owner

Measure qualified hiring requests and realized revenue. Opens are useful for diagnosing the email, but they are not the goal.

