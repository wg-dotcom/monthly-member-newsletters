#!/usr/bin/env python3
"""Generate the August 2026 Sagan industry newsletter draft pack."""

from __future__ import annotations

import html
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from urllib.parse import quote


ROOT = Path(__file__).resolve().parent
DATA_PATH = ROOT / "data" / "august-2026-enriched.json"
ASSETS = ROOT / "assets"
CLUSTER_DIR = ROOT / "clusters"

CLUSTERS = {
    "Home & Field Services": [
        "Cleaning Services",
        "Environmental Services",
        "HVAC",
        "Home Improvement",
        "Home Services",
        "Home Services & Trades",
        "Landscaping",
        "Plumbing",
    ],
    "Property, Construction & Engineering": [
        "Commercial Real Estate",
        "Construction",
        "Construction & Engineering",
        "Real Estate",
        "Residential",
    ],
    "Finance & Business Services": [
        "Accounting",
        "Financial Services",
        "IT Services",
        "Marketing",
        "Professional Services",
        "Venture Capital",
    ],
    "Health, Wellness & Care": [
        "Fitness",
        "Healthcare",
        "Mental Healthcare",
        "Personal Care",
    ],
    "Consumer, Sports & Hospitality": [
        "Consumer Services",
        "Food & Beverage",
        "Food & Hospitality",
        "Sports",
    ],
    "Logistics & Industrial Operations": [
        "Equipment",
        "Renewable Energy",
        "Transportation",
        "Trucking",
    ],
}

AI_BUILD_BRIEFS = {
    "Account Receivables Tracker": {
        "does": "Keeps open invoices, aging, owners, and follow-up status in one working view.",
        "value": "The finance team can see what needs attention before overdue balances become a cash-flow problem.",
    },
    "Candidate Screening Agent": {
        "does": "Reviews applicant information against the role criteria and organizes the strongest matches for human review.",
        "value": "Hiring teams spend less time sorting applications and more time speaking with qualified people.",
    },
    "Cruise Flower Delivery CS Response Automation": {
        "does": "Drafts consistent answers for cruise flower-delivery questions using the details of the request.",
        "value": "Customers get faster answers while the service team handles more conversations without adding repetitive work.",
    },
    "Lease Renewal Assistance Agent": {
        "does": "Organizes lease details, renewal steps, and tenant communication into one repeatable workflow.",
        "value": "Property teams can move renewals forward without rebuilding the same checklist and messages each time.",
    },
    "Rent Benchmarking Agent": {
        "does": "Structures market-rent comparisons so operators can review current pricing against nearby alternatives.",
        "value": "Teams reach pricing decisions faster and enter owner or tenant conversations with clearer context.",
    },
    "Property Inspection Agent": {
        "does": "Turns inspection inputs into a structured record with clear issues and follow-up items.",
        "value": "Teams spend less time cleaning notes and can move repairs or owner updates forward sooner.",
    },
    "Client Approval Agent": {
        "does": "Tracks work that needs client sign-off, keeps the decision context together, and supports follow-up.",
        "value": "Campaigns and deliverables spend less time sitting in an approval queue.",
    },
    "Rental Performance Dashboard": {
        "does": "Brings the core rental-performance signals into one view for routine operating reviews.",
        "value": "Operators can spot weak performance and decide where to act without assembling the report by hand.",
    },
    "Timesheet Agent": {
        "does": "Collects, checks, and summarizes time entries before they reach billing or payroll review.",
        "value": "The team spends less time chasing missing entries and correcting avoidable time-reporting errors.",
    },
    "Property Update Summarizer": {
        "does": "Turns detailed property activity into a concise update for owners and internal teams.",
        "value": "Stakeholders get the important changes faster without an operator rewriting every update.",
    },
}


def esc(value: object) -> str:
    return html.escape(str(value or ""), quote=True)


def slugify(value: str) -> str:
    value = value.lower().replace("&", "and")
    return re.sub(r"[^a-z0-9]+", "-", value).strip("-")


def singular(value: str) -> str:
    return "hire" if value == "1" else "hires"


def public_name(value: str) -> str:
    parts = str(value or "").strip().split()
    if not parts:
        return "New hire"
    first = parts[0]
    if len(parts) == 1:
        return first
    last = parts[-1].rstrip(".")
    return f"{first} {last[0]}." if last else first


def page_head(title: str, description: str, asset_prefix: str = "") -> str:
    favicon = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'%3E%3Crect width='64' height='64' rx='18' fill='%23093A3E'/%3E%3Cpath d='M18 22c0-6 5-10 14-10 7 0 12 2 15 6l-7 6c-2-2-5-3-8-3-3 0-5 1-5 3 0 6 21 1 21 16 0 8-6 12-16 12-8 0-14-3-18-8l7-6c3 3 7 5 11 5 4 0 6-1 6-3 0-6-20-2-20-18z' fill='%23F5B800'/%3E%3C/svg%3E"
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{esc(title)}</title>
  <meta name="description" content="{esc(description)}">
  <link rel="icon" href="{favicon}">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Fragment+Mono&amp;family=Plus+Jakarta+Sans:wght@600;700;800&amp;family=Space+Grotesk:wght@400;500;600&amp;display=swap" rel="stylesheet">
  <link rel="stylesheet" href="{asset_prefix}assets/styles.css">
</head>"""


def site_header(prefix: str = "") -> str:
    return f"""<header class="site-header">
  <a class="brand" href="{prefix}index.html" aria-label="Sagan August newsletter drafts">
    <span class="brand-mark">S</span><span>SAGAN</span>
  </a>
  <div class="header-right">
    <span class="draft-chip">INTERNAL DRAFT</span>
    <span class="period">AUGUST 2026</span>
  </div>
</header>"""


def source_footer(prefix: str = "") -> str:
    return f"""<footer class="site-footer">
  <div>
    <strong>August member brief</strong>
    <p>Built from the August CORE, AI Builds, GPD, and installment exports. Data checked September 15, 2026.</p>
  </div>
  <a href="{prefix}index.html#sources">See source notes</a>
</footer>"""


def classify_ai_build(build: dict) -> set[str]:
    industry = str(build.get("industry_primary") or "").lower()
    company = str(build.get("company_name") or "").lower()
    tags: set[str] = set()
    if "real estate" in industry or company in {"monterey rentals", "red fortress", "coyote pmc"}:
        tags |= {"Real Estate", "Commercial Real Estate", "Residential"}
    if "cleaning" in industry:
        tags |= {"Cleaning Services", "Home Services", "Home Services & Trades"}
    if "healthcare" in industry:
        tags |= {"Healthcare", "Mental Healthcare", "Personal Care"}
    if "gardening" in industry:
        tags |= {"Landscaping", "Environmental Services"}
    if "cruise flower delivery" in str(build.get("build_name") or "").lower():
        tags |= {"Consumer Services", "Food & Hospitality"}
    if "digital" in industry:
        tags |= {"Marketing", "IT Services"}
    if "financial" in industry:
        tags |= {"Financial Services", "Accounting", "Professional Services", "Venture Capital"}
    return tags


NEXT_MOVES = {
    "finance": ("Add a close-ready operator", "Give them a timesheet or receivables agent so reporting does not become their second job."),
    "health": ("Add a patient-operations hire", "Pair the role with a screening or follow-up agent to clear repetitive intake work before it reaches the team."),
    "real": ("Add a property-operations hire", "Pair the role with rent benchmarking, inspection, lease-renewal, or owner-update automation."),
    "home": ("Add a dispatch or customer-operations hire", "Pair the role with an intake and follow-up agent so every request gets a fast response."),
    "construction": ("Add a project coordinator", "Pair the role with estimate, document, and vendor follow-up automation."),
    "sports": ("Add a coordinator who keeps programs moving", "Pair the role with lead follow-up and scheduling automation before the next enrollment cycle."),
    "marketing": ("Add an execution hire", "Pair the role with client-approval automation so work ships without approval-chasing."),
    "it": ("Add an operator who owns the queue", "Pair the role with triage and status-summary automation so experts stay on higher-value work."),
    "land": ("Add a service coordinator", "Pair the role with estimate follow-up and customer-response automation."),
    "environment": ("Add the next operator before volume breaks the process", "Pair the role with intake, QA, and reporting automation."),
    "logistics": ("Add an operations coordinator who owns the handoffs", "Pair the role with dispatch, tracking, and exception-summary automation."),
    "default": ("Add the operator your team keeps covering for", "Pair the role with one focused AI build that removes the repetitive work around it."),
}


def recommendation(industry: str) -> tuple[str, str]:
    text = industry.lower()
    for key, result in NEXT_MOVES.items():
        if key != "default" and key in text:
            return result
    return NEXT_MOVES["default"]


def render_candidate(hire: dict) -> str:
    name = public_name(hire.get("candidate_name", ""))
    role = str(hire.get("role_title") or "New team member")
    gtc = '<span class="mini-tag dark">GTC</span>' if hire.get("is_gtc") == "Yes" else ""
    video_url = str(hire.get("video_url") or "").strip()
    if hire.get("has_intro_video") == "Yes" and video_url:
        video = f'<a class="video-link" href="{esc(video_url)}" target="_blank" rel="noopener noreferrer">Watch intro <span aria-hidden="true">↗</span></a>'
    elif hire.get("has_intro_video") == "Yes":
        video = ""
    else:
        video = ""
    video_line = f"\n  {video}" if video else ""
    return f"""<article class="candidate-card">
  <div class="avatar" aria-hidden="true">{esc(name[0])}</div>
  <div class="candidate-copy">
    <div class="candidate-title"><h4>{esc(name)}</h4>{gtc}</div>
    <p>{esc(role)}</p>
  </div>{video_line}
</article>"""


def render_cluster_page(cluster: str, cluster_industries: list[str], hires: list[dict], ai_builds: list[dict], global_stats: dict) -> str:
    count = len(hires)
    companies = defaultdict(list)
    for hire in hires:
        companies[str(hire.get("company_name") or "Member company")].append(hire)
    gtc_count = sum(h.get("is_gtc") == "Yes" for h in hires)
    videos = sum(h.get("has_intro_video") == "Yes" for h in hires)
    related = [b for b in ai_builds if classify_ai_build(b).intersection(cluster_industries)]
    hire_action, build_action = recommendation(cluster)
    subject = quote(f"August hiring request — {cluster}")
    preview = f"{count} hires across {cluster} moved in August. See what members are building next."

    company_blocks = []
    for company, company_hires in sorted(companies.items(), key=lambda item: (-len(item[1]), item[0].lower())):
        candidate_cards = "".join(render_candidate(h) for h in company_hires)
        company_blocks.append(f"""<section class="company-block">
  <div class="company-heading">
    <h3>{esc(company)}</h3>
    <span>{len(company_hires)} {singular(str(len(company_hires)))}</span>
  </div>
  <div class="candidate-list">{candidate_cards}</div>
</section>""")

    cross_network = False
    featured_builds = related
    if not featured_builds:
        cross_network = True
        fallback_names = {
            "Account Receivables Tracker",
            "Timesheet Agent",
            "Property Update Summarizer",
        }
        featured_builds = [b for b in ai_builds if b.get("build_name") in fallback_names]

    build_cards = []
    for build in featured_builds:
            brief = AI_BUILD_BRIEFS.get(str(build.get("build_name")), {})
            build_cards.append(f"""<article class="build-card">
  <span class="build-label">SHIPPED IN AUGUST</span>
  <h3>{esc(build.get('build_name'))}</h3>
  <p class="build-company">Built for {esc(build.get('company_name'))}</p>
  <div class="build-brief">
    <div><span>WHAT IT DOES</span><p>{esc(brief.get('does', 'Turns a repeat workflow into a consistent operating step.'))}</p></div>
    <div><span>WHY IT MATTERS</span><p>{esc(brief.get('value', 'The team gets more capacity without adding more repetitive work.'))}</p></div>
  </div>
</article>""")
    builds_markup = "".join(build_cards)
    if cross_network:
        build_heading = "Three proven AI plays worth borrowing."
        build_intro = "These workflows shipped for other Sagan members in August. Each one can be adapted to remove repeat work from an operations team."
    else:
        build_heading = f"{len(featured_builds)} relevant AI {('build' if len(featured_builds) == 1 else 'builds')} shipped in August."
        build_intro = "Members are already using focused agents to remove repeat work from the teams they are growing."

    gtc_note = f"{gtc_count} came through GTC." if gtc_count else "Five August hires came through GTC across the Sagan network."
    gtc_stat = f"<div><strong>{gtc_count}</strong><span>GTC {singular(str(gtc_count))}</span></div>" if gtc_count else "<div><strong>5</strong><span>network GTC hires</span></div>"
    company_word = "company" if len(companies) == 1 else "companies"
    hiring_mail = f"mailto:?subject={subject}&body=I%20want%20to%20open%20a%20hiring%20request%20for%20my%20team."

    industry_counts = Counter(h.get("industry_primary") for h in hires)
    industry_tags = "".join(
        f'<span>{esc(name)} <strong>{industry_counts.get(name, 0)}</strong></span>'
        for name in cluster_industries
    )

    return f"""{page_head(f'{cluster} — August Member Brief', preview, '../../')}
<body>
<div class="page-shell">
{site_header('../../')}
<main>
  <section class="hero industry-hero">
    <div class="eyebrow">AUGUST SIGNAL / {esc(cluster).upper()}</div>
    <h1>The role your team keeps covering after hours? <span>{count} hires</span> moved across {esc(cluster)} in August.</h1>
    <p class="hero-copy">Other members stopped waiting for the perfect time. They added capacity, kept the work moving, and gave themselves room to grow.</p>
    <div class="hero-actions">
      <a class="button primary" href="{hiring_mail}">Open a hiring request <span aria-hidden="true">↗</span></a>
      <a class="text-link" href="#peer-moves">See the peer moves</a>
    </div>
  </section>

  <section class="proof-strip" aria-label="August industry proof">
    <div><strong>{count}</strong><span>accepted offers</span></div>
    <div><strong>{len(companies)}</strong><span>member {company_word}</span></div>
    <div><strong>{videos}</strong><span>intro videos ready</span></div>
    {gtc_stat}
  </section>

  <section class="cluster-scope" aria-label="Industries in this newsletter">
    <span class="cluster-label">INDUSTRIES IN THIS BRIEF</span>
    <div class="cluster-tags">{industry_tags}</div>
  </section>

  <section class="section" id="peer-moves">
    <div class="section-heading two-col-heading">
      <div>
        <span class="kicker">PEER MOVES</span>
        <h2>Here is who moved.</h2>
      </div>
      <p>{gtc_note} Every name below reached accepted-offer status in August.</p>
    </div>
    <div class="company-grid">{''.join(company_blocks)}</div>
  </section>

  <section class="section ai-section">
    <div class="section-heading two-col-heading">
      <div>
        <span class="kicker">AI BUILDS</span>
        <h2>{build_heading}</h2>
      </div>
      <p>{build_intro}</p>
    </div>
    <div class="build-grid">{builds_markup}</div>
    <div class="benchmark-line"><span>Across Sagan</span><strong>{global_stats['ai_builds']} customer builds</strong><span>created in August</span></div>
  </section>

  <section class="section pairing-section">
    <div class="pairing-number">02</div>
    <div class="pairing-copy">
      <span class="kicker">THE COMBINATION</span>
      <h2>Do not choose between a hire and an AI build.</h2>
      <p>The better move is to give a strong operator leverage from day one.</p>
    </div>
    <div class="pairing-actions">
      <article><span>HIRE</span><h3>{esc(hire_action)}</h3></article>
      <div class="plus" aria-hidden="true">+</div>
      <article><span>BUILD</span><h3>{esc(build_action)}</h3></article>
    </div>
  </section>

  <section class="section gpd-section">
    <div class="gpd-stat"><strong>77</strong><span>August CORE hires</span></div>
    <div class="gpd-copy">
      <span class="kicker light">GLOBAL PAY DIRECT</span>
      <h2>Two global hires started through GPD in August.</h2>
      <p>GPD turns a signed offer into a clean operating setup. Sagan handles the contract, onboarding, and global payments while you keep day-to-day management.</p>
      <p class="fine">GPD can handle contracts, onboarding, and global payments while you keep day-to-day management. Terms vary by member agreement.</p>
    </div>
  </section>

  <section class="final-cta">
    <span class="kicker">YOUR AUGUST SIGNAL</span>
    <h2>The market is not waiting for your org chart.</h2>
    <p>Tell us what is stuck. We will help you decide whether the next move is talent, an AI build, or both.</p>
    <a class="button primary large" href="{hiring_mail}">Start the request <span aria-hidden="true">↗</span></a>
  </section>
</main>
{source_footer('../../')}
</div>
</body>
</html>
"""


def render_hub(cluster_map: dict[str, list[dict]], ai_builds: list[dict], stats: dict, data: dict) -> str:
    cards = []
    for cluster, hires in sorted(cluster_map.items(), key=lambda item: (-len(item[1]), item[0].lower())):
        companies = len({h.get("company_name") for h in hires})
        gtc = sum(h.get("is_gtc") == "Yes" for h in hires)
        cluster_industries = CLUSTERS[cluster]
        related = sum(bool(classify_ai_build(b).intersection(cluster_industries)) for b in ai_builds)
        ai_tag = f"{related} relevant AI" if related else "AI ideas included"
        gtc_tag = f"{gtc} GTC" if gtc else "5 network GTC"
        coverage = " · ".join(cluster_industries)
        cards.append(f"""<a class="industry-card" href="clusters/{slugify(cluster)}/index.html">
  <div class="industry-card-top"><span>{esc(cluster)}</span><b aria-hidden="true">↗</b></div>
  <strong>{len(hires)}</strong>
  <p>{singular(str(len(hires)))} · {companies} {'company' if companies == 1 else 'companies'}</p>
  <small>{esc(coverage)}</small>
  <div class="industry-tags"><span>{gtc_tag}</span><span>{ai_tag}</span></div>
</a>""")

    sources = data.get("sources", {})
    source_links = "".join(
        f'<a href="{esc(url)}" target="_blank" rel="noopener noreferrer">{esc(label.replace("_", " ").title())} <span aria-hidden="true">↗</span></a>'
        for label, url in sources.items()
    )

    return f"""{page_head('August 2026 Member Newsletter Drafts', 'Six member newsletter drafts grouped by similar industries and built from August hiring and AI activity.')}
<body>
<div class="page-shell">
{site_header()}
<main>
  <section class="hero hub-hero">
    <div class="eyebrow">TEAM WORKING PACK / MC-250</div>
    <h1>Members made <span>77 hires</span> in August. Six focused newsletters make the next request hard to ignore.</h1>
    <p class="hero-copy">Similar industries now share one stronger story. Real member activity. Strong pressure without invented claims.</p>
    <div class="hero-actions">
      <a class="button primary" href="#industries">Browse industry drafts</a>
      <a class="text-link" href="#editorial">See the editorial logic</a>
    </div>
  </section>

  <section class="proof-strip global-proof" aria-label="August Sagan activity">
    <div><strong>{stats['hires']}</strong><span>CORE accepted offers</span></div>
    <div><strong>{stats['ai_builds']}</strong><span>customer AI builds</span></div>
    <div><strong>{stats['white_glove']}</strong><span>White Glove placements</span></div>
    <div><strong>{stats['gtc']}</strong><span>GTC hires</span></div>
  </section>

  <section class="section" id="industries">
    <div class="section-heading two-col-heading">
      <div><span class="kicker">6 MEMBER GROUPS</span><h2>Pick the member’s world.</h2></div>
      <p>Each page is a complete newsletter. The peer proof, AI builds, and recommendation change with the group.</p>
    </div>
    <div class="industry-grid">{''.join(cards)}</div>
  </section>

  <section class="section editorial" id="editorial">
    <div class="section-heading"><span class="kicker">EDITORIAL LOGIC</span><h2>Sales pressure, with receipts.</h2></div>
    <div class="logic-grid">
      <article><span>01</span><h3>Start with the move</h3><p>Lead with accepted offers in the member’s own industry.</p></article>
      <article><span>02</span><h3>Show the leverage</h3><p>Connect the hire to a focused AI build that removes repeat work.</p></article>
      <article><span>03</span><h3>Close the operating gap</h3><p>Position GPD as the way to move from offer to global payment without new payroll infrastructure.</p></article>
    </div>
  </section>

  <section class="section data-room" id="sources">
    <div>
      <span class="kicker">DATA ROOM</span>
      <h2>What is verified.</h2>
      <p>Seventy-seven active-member CORE hires. Five GTC. Seventy-six intro videos confirmed. Ten separate White Glove placement invoices. Ten included customer AI builds. No August CORE hire matched an August installment invoice.</p>
    </div>
    <div class="source-links">{source_links}</div>
    <div class="caveat-box">
      <strong>Deliberate omissions</strong>
      <p>The export does not include accepted compensation. The pages do not present candidate profile rates as member-paid compensation. Unmatched video URLs stay unlinked.</p>
      <p>The AI briefs explain the intended workflow based on each build name. Confirm the final wording with the build owner before sending.</p>
    </div>
  </section>
</main>
{source_footer()}
</div>
</body>
</html>
"""


STYLES = r"""
:root{--cream:#F5F2ED;--paper:#FCFAF6;--glacier:#093A3E;--glacier-2:#15545A;--yellow:#F5B800;--blue:#2197FF;--ink:#10292C;--muted:#617174;--line:rgba(9,58,62,.18);--white:#fff;--radius:24px;--mono:'Fragment Mono',monospace;--display:'Plus Jakarta Sans',sans-serif;--body:'Space Grotesk',sans-serif}
*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:var(--cream);color:var(--ink);font-family:var(--body);line-height:1.55}.page-shell{max-width:1500px;margin:0 auto;overflow:hidden}.site-header{height:88px;padding:0 clamp(24px,5vw,72px);display:flex;align-items:center;justify-content:space-between;border-bottom:1px solid var(--line)}.brand{display:flex;gap:12px;align-items:center;color:var(--glacier);font-family:var(--display);font-weight:800;letter-spacing:.12em;text-decoration:none}.brand-mark{display:grid;place-items:center;width:34px;height:34px;border-radius:11px;background:var(--glacier);color:var(--yellow);letter-spacing:0}.header-right{display:flex;gap:12px;align-items:center}.draft-chip,.period,.eyebrow,.kicker,.build-label{font-family:var(--mono);font-size:11px;letter-spacing:.1em;text-transform:uppercase}.draft-chip{padding:7px 11px;border:1px solid var(--line);border-radius:999px}.period{color:var(--muted)}main{padding:0 clamp(24px,5vw,72px)}.hero{padding:clamp(72px,10vw,150px) 0 80px;max-width:1240px}.eyebrow{display:inline-flex;align-items:center;gap:9px;color:var(--glacier);font-weight:600}.eyebrow:before{content:"";width:24px;height:3px;border-radius:3px;background:var(--yellow)}h1,h2,h3,h4{font-family:var(--display);margin:0;color:var(--glacier);line-height:1.05}h1{font-size:clamp(44px,7.2vw,108px);letter-spacing:-.055em;max-width:1280px;margin-top:24px}h1 span{color:var(--glacier);box-shadow:inset 0 -.18em 0 var(--yellow)}h2{font-size:clamp(36px,4.6vw,68px);letter-spacing:-.04em}.hero-copy{font-size:clamp(18px,2vw,25px);max-width:760px;color:var(--muted);margin:30px 0 0}.hero-actions{display:flex;gap:26px;align-items:center;flex-wrap:wrap;margin-top:40px}.button{display:inline-flex;align-items:center;justify-content:center;gap:18px;padding:15px 24px;border-radius:999px;font-family:var(--display);font-weight:700;text-decoration:none;transition:transform .18s ease,background .18s ease}.button:hover{transform:translateY(-2px)}.button.primary{background:var(--yellow);color:var(--glacier)}.button.large{padding:19px 30px}.text-link{color:var(--glacier);font-weight:600;text-underline-offset:5px}.proof-strip{display:grid;grid-template-columns:repeat(4,1fr);border:1px solid var(--line);border-radius:var(--radius);background:var(--paper);overflow:hidden}.proof-strip div{padding:34px;border-right:1px solid var(--line)}.proof-strip div:last-child{border:0}.proof-strip strong{display:block;font:clamp(38px,5vw,68px)/1 var(--mono);letter-spacing:-.06em;color:var(--glacier)}.proof-strip span{display:block;margin-top:12px;color:var(--muted)}.section{padding:clamp(80px,10vw,140px) 0;border-bottom:1px solid var(--line)}.section-heading{max-width:900px;margin-bottom:50px}.section-heading h2{margin-top:14px}.two-col-heading{display:grid;grid-template-columns:minmax(0,1.35fr) minmax(280px,.65fr);max-width:none;gap:70px;align-items:end}.two-col-heading p{margin:0;color:var(--muted);font-size:18px}.kicker{font-weight:600;color:var(--glacier)}.kicker.light{color:var(--yellow)}.company-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:20px}.company-block{background:var(--paper);border:1px solid var(--line);border-radius:var(--radius);padding:28px}.company-heading{display:flex;justify-content:space-between;gap:18px;align-items:start;padding-bottom:22px;border-bottom:1px solid var(--line)}.company-heading h3{font-size:23px;line-height:1.25}.company-heading span{font:12px var(--mono);white-space:nowrap;color:var(--muted)}.candidate-list{display:grid}.candidate-card{display:grid;grid-template-columns:48px minmax(0,1fr) auto;align-items:center;gap:15px;padding:19px 0;border-bottom:1px solid var(--line)}.candidate-card:last-child{border:0;padding-bottom:0}.avatar{display:grid;place-items:center;width:46px;height:46px;border-radius:14px;background:var(--glacier);color:var(--yellow);font-family:var(--display);font-weight:800}.candidate-title{display:flex;gap:8px;align-items:center}.candidate-title h4{font-size:17px}.candidate-copy p{margin:4px 0 0;color:var(--muted);font-size:14px}.mini-tag{font:9px var(--mono);padding:3px 6px;border-radius:999px}.mini-tag.dark{background:var(--glacier);color:var(--white)}.video-link,.video-ready,.video-missing{font:11px var(--mono);white-space:nowrap}.video-link{color:var(--glacier);text-underline-offset:4px}.video-ready{color:var(--glacier)}.video-ready:before{content:"";display:inline-block;width:7px;height:7px;border-radius:50%;background:var(--blue);margin-right:7px}.video-missing{color:#945f32}.data-note{font-size:13px;color:var(--muted);margin:22px 4px 0}.ai-section{background:var(--paper);margin-left:calc(clamp(24px,5vw,72px) * -1);margin-right:calc(clamp(24px,5vw,72px) * -1);padding-left:clamp(24px,5vw,72px);padding-right:clamp(24px,5vw,72px)}.build-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:20px}.build-card{min-height:220px;border:1px solid var(--line);border-radius:var(--radius);padding:30px;display:flex;flex-direction:column;justify-content:flex-end;background:var(--cream)}.build-card.open-lane{grid-column:1/-1;min-height:260px;background:var(--glacier);border-color:var(--glacier)}.build-card h3{font-size:clamp(26px,3vw,42px);margin-top:48px}.build-card p{color:var(--muted);margin:10px 0 0}.build-card.open-lane h3,.build-card.open-lane p{color:var(--white)}.build-label{color:var(--glacier)}.open-lane .build-label{color:var(--yellow)}.benchmark-line{display:flex;gap:18px;align-items:center;flex-wrap:wrap;margin-top:22px;font-size:14px}.benchmark-line strong{font-family:var(--mono);color:var(--glacier)}.benchmark-line span{color:var(--muted)}.pairing-section{display:grid;grid-template-columns:110px .7fr 1.3fr;gap:40px;align-items:start}.pairing-number{font:62px/1 var(--mono);color:var(--yellow)}.pairing-copy h2{font-size:clamp(34px,4vw,58px);margin:12px 0 22px}.pairing-copy p{color:var(--muted);font-size:18px}.pairing-actions{display:grid;grid-template-columns:1fr 48px 1fr;align-items:stretch}.pairing-actions article{padding:28px;border:1px solid var(--line);border-radius:var(--radius);background:var(--paper)}.pairing-actions article span{font:11px var(--mono);color:var(--muted)}.pairing-actions article h3{font-size:21px;line-height:1.3;margin-top:24px}.plus{display:grid;place-items:center;font:30px var(--mono);color:var(--glacier)}.gpd-section{display:grid;grid-template-columns:.55fr 1.45fr;gap:70px;padding-left:clamp(28px,5vw,70px);padding-right:clamp(28px,5vw,70px);background:var(--glacier);border:0;border-radius:var(--radius);margin-top:clamp(80px,10vw,140px)}.gpd-stat{display:flex;flex-direction:column;justify-content:center}.gpd-stat strong{font:clamp(88px,12vw,180px)/.85 var(--mono);letter-spacing:-.08em;color:var(--yellow)}.gpd-stat span{color:var(--white);margin-top:18px}.gpd-copy h2{color:var(--white);margin:14px 0 26px}.gpd-copy p{font-size:19px;color:#d7e5e3;max-width:700px}.gpd-copy .fine{font-size:14px;color:#abc2bf}.final-cta{text-align:center;padding:clamp(100px,12vw,170px) 0}.final-cta h2{max-width:980px;margin:18px auto}.final-cta p{max-width:700px;margin:25px auto 34px;color:var(--muted);font-size:19px}.site-footer{display:flex;justify-content:space-between;gap:40px;align-items:end;padding:45px clamp(24px,5vw,72px);background:var(--glacier);color:var(--white)}.site-footer strong{font-family:var(--display)}.site-footer p{max-width:660px;margin:8px 0 0;color:#abc2bf;font-size:13px}.site-footer a{color:var(--yellow);font-weight:600}.industry-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:16px}.industry-card{display:block;min-height:245px;padding:26px;border:1px solid var(--line);border-radius:var(--radius);background:var(--paper);color:inherit;text-decoration:none;transition:background .18s ease,transform .18s ease}.industry-card:hover{background:var(--white);transform:translateY(-3px)}.industry-card-top{display:flex;justify-content:space-between;gap:16px;color:var(--glacier);font-weight:600}.industry-card>strong{display:block;font:62px/1 var(--mono);letter-spacing:-.07em;color:var(--glacier);margin-top:38px}.industry-card>p{color:var(--muted);margin:8px 0 24px}.industry-tags{display:flex;gap:8px;flex-wrap:wrap}.industry-tags span{font:10px var(--mono);padding:6px 9px;border:1px solid var(--line);border-radius:999px}.editorial{background:var(--paper);margin-left:calc(clamp(24px,5vw,72px) * -1);margin-right:calc(clamp(24px,5vw,72px) * -1);padding-left:clamp(24px,5vw,72px);padding-right:clamp(24px,5vw,72px)}.logic-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:18px}.logic-grid article{padding:28px;border-top:3px solid var(--yellow);background:var(--cream);border-radius:0 0 var(--radius) var(--radius)}.logic-grid article>span{font:34px var(--mono);color:var(--glacier)}.logic-grid h3{font-size:21px;margin:30px 0 12px}.logic-grid p{color:var(--muted);margin:0}.data-room{display:grid;grid-template-columns:1fr .75fr;gap:50px}.data-room h2{margin:14px 0 22px}.data-room p{color:var(--muted)}.source-links{display:flex;flex-direction:column;border:1px solid var(--line);border-radius:var(--radius);overflow:hidden;background:var(--paper)}.source-links a{display:flex;justify-content:space-between;padding:18px 22px;color:var(--glacier);font-weight:600;text-decoration:none;border-bottom:1px solid var(--line)}.source-links a:last-child{border:0}.caveat-box{grid-column:1/-1;padding:22px;border-left:4px solid var(--yellow);background:var(--paper)}.caveat-box p{margin:5px 0 0}.hub-hero{max-width:1300px}
.build-card{justify-content:flex-start;min-height:360px}.build-card h3{margin-top:32px}.build-card .build-company{margin-top:10px;font-size:14px}.build-brief{display:grid;grid-template-columns:1fr 1fr;gap:22px;margin-top:auto;padding-top:30px;border-top:1px solid var(--line)}.build-brief span{font:10px var(--mono);letter-spacing:.08em;color:var(--glacier)}.build-brief p{font-size:15px;line-height:1.5;margin-top:8px;color:var(--ink)}
.industry-card small{display:block;min-height:58px;margin:-12px 0 22px;color:var(--muted);font-size:12px;line-height:1.45}.cluster-scope{display:grid;grid-template-columns:220px 1fr;gap:24px;align-items:start;padding:26px 4px 0}.cluster-label{font:11px var(--mono);letter-spacing:.1em;color:var(--muted)}.cluster-tags{display:flex;gap:8px;flex-wrap:wrap}.cluster-tags span{font-size:13px;padding:7px 10px;border:1px solid var(--line);border-radius:999px;background:var(--paper)}.cluster-tags strong{font-family:var(--mono);margin-left:5px;color:var(--glacier)}
.ai-section,.editorial{margin-left:clamp(-72px,-5vw,-24px);margin-right:clamp(-72px,-5vw,-24px)}
@media(max-width:900px){.proof-strip{grid-template-columns:repeat(2,1fr)}.proof-strip div:nth-child(2){border-right:0}.proof-strip div:nth-child(-n+2){border-bottom:1px solid var(--line)}.two-col-heading,.pairing-section,.gpd-section,.data-room{grid-template-columns:1fr}.company-grid,.build-grid,.industry-grid{grid-template-columns:1fr 1fr}.pairing-number{display:none}.gpd-section{gap:35px}.gpd-stat strong{font-size:100px}.logic-grid{grid-template-columns:1fr}.site-footer{align-items:start}}
@media(max-width:620px){.site-header{height:76px}.draft-chip{display:none}.hero{padding-top:66px}h1{font-size:44px}.proof-strip{grid-template-columns:1fr 1fr}.proof-strip div{padding:23px}.proof-strip strong{font-size:39px}.proof-strip span{font-size:13px}.company-grid,.build-grid,.industry-grid{grid-template-columns:1fr}.candidate-card{grid-template-columns:42px 1fr}.candidate-card>.video-link,.candidate-card>.video-ready,.candidate-card>.video-missing{grid-column:2}.pairing-actions{grid-template-columns:1fr}.plus{height:46px}.site-footer{flex-direction:column}.header-right{gap:0}.company-block{padding:22px}.gpd-section{border-radius:18px}.industry-card{min-height:220px}.cluster-scope{grid-template-columns:1fr}.build-brief{grid-template-columns:1fr}}
@media(prefers-reduced-motion:reduce){html{scroll-behavior:auto}.button,.industry-card{transition:none}}
"""


def main() -> None:
    data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    active_hires = [h for h in data["hires"] if h.get("customer_type") == "Active Member"]
    ai_builds = [b for b in data["ai_builds"] if b.get("include_in_customer_count") == "Yes"]
    cluster_map: dict[str, list[dict]] = defaultdict(list)
    industry_to_cluster = {
        industry: cluster
        for cluster, industries in CLUSTERS.items()
        for industry in industries
    }
    ungrouped = []
    for hire in active_hires:
        industry = str(hire["industry_primary"])
        cluster = industry_to_cluster.get(industry)
        if not cluster:
            ungrouped.append(industry)
            continue
        cluster_map[cluster].append(hire)
    if ungrouped:
        raise ValueError(f"Ungrouped industries: {sorted(set(ungrouped))}")

    stats = {
        "hires": len(active_hires),
        "ai_builds": len(ai_builds),
        "white_glove": sum(h.get("customer_type") == "White Glove" for h in data["hires"]),
        "gtc": sum(h.get("is_gtc") == "Yes" for h in active_hires),
    }

    ASSETS.mkdir(parents=True, exist_ok=True)
    CLUSTER_DIR.mkdir(parents=True, exist_ok=True)
    (ASSETS / "styles.css").write_text(STYLES.strip() + "\n", encoding="utf-8")
    (ROOT / "index.html").write_text(render_hub(cluster_map, ai_builds, stats, data), encoding="utf-8")
    for cluster, hires in cluster_map.items():
        output = CLUSTER_DIR / slugify(cluster)
        output.mkdir(parents=True, exist_ok=True)
        (output / "index.html").write_text(
            render_cluster_page(cluster, CLUSTERS[cluster], hires, ai_builds, stats),
            encoding="utf-8",
        )
    (ROOT / ".nojekyll").write_text("", encoding="utf-8")
    print(json.dumps({"cluster_pages": len(cluster_map), "cluster_hires": {k: len(v) for k, v in cluster_map.items()}, "stats": stats}, indent=2))


if __name__ == "__main__":
    main()
