#!/usr/bin/env python3
"""Build a read-only monthly hiring snapshot from local Sagan exports."""

from __future__ import annotations

import argparse
import csv
import json
import re
import statistics
import unicodedata
from collections import Counter, defaultdict
from difflib import SequenceMatcher
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
TAXONOMY_PATH = ROOT / "sagan-members-clean.json"
SIGNED_OFFERS_PATH = ROOT / "revenue-data" / "signed_offers.csv"
CANDIDATES_PATH = ROOT / "sourcing-matcher" / "data" / "candidates_full.json"


def normalize(value: str) -> str:
    ascii_value = unicodedata.normalize("NFKD", value or "").encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", " ", ascii_value.lower()).strip()


def company_from_account(account: str) -> str:
    return (account or "").split(" - ", 1)[0].strip()


def best_match(
    query: str,
    values: list[str],
    normalized_values: dict[str, str],
    threshold: float,
    margin: float = 0.0,
):
    normalized_query = normalize(query)
    if normalized_query in normalized_values:
        return normalized_values[normalized_query], 1.0
    scored = sorted(
        (
            (SequenceMatcher(None, normalized_query, normalize(value)).ratio(), value)
            for value in values
        ),
        reverse=True,
    )
    if not scored or scored[0][0] < threshold:
        return None, scored[0][0] if scored else 0.0
    if len(scored) > 1 and scored[0][0] - scored[1][0] < margin:
        return None, scored[0][0]
    return scored[0][1], scored[0][0]


def money_stats(values: list[float]) -> dict:
    return {
        "min": min(values) if values else None,
        "median": statistics.median(values) if values else None,
        "mean": round(statistics.mean(values)) if values else None,
        "max": max(values) if values else None,
        "monthly_payroll_added": sum(values) if values else 0,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--month", required=True, help="Month in YYYY-MM format")
    parser.add_argument("--core-only", action="store_true")
    args = parser.parse_args()

    taxonomy_records = json.loads(TAXONOMY_PATH.read_text(encoding="utf-8"))
    taxonomy_by_company = {
        company_from_account(record["account"]): record for record in taxonomy_records
    }
    taxonomy_companies = list(taxonomy_by_company)
    normalized_taxonomy_companies = {
        normalize(company): company for company in taxonomy_companies
    }

    candidate_records = json.loads(CANDIDATES_PATH.read_text(encoding="utf-8"))
    candidate_by_name = {record.get("name", ""): record for record in candidate_records}
    normalized_candidate_names = {
        normalize(name): name for name in candidate_by_name if name
    }

    with SIGNED_OFFERS_PATH.open(encoding="utf-8", newline="") as source:
        hires = [
            row
            for row in csv.DictReader(source)
            if row["date"].startswith(args.month)
            and (not args.core_only or row["core_member"] == "Yes")
            and normalize(row["company"]) != "fabi s company"
        ]

    enriched = []
    unmatched_companies = Counter()
    unmatched_candidates = Counter()
    for hire in hires:
        company_match, company_score = best_match(
            hire["company"],
            taxonomy_companies,
            normalized_taxonomy_companies,
            threshold=0.76,
            margin=0.04,
        )
        taxonomy = taxonomy_by_company.get(company_match or "", {})
        if not company_match:
            unmatched_companies[hire["company"]] += 1

        normalized_candidate = normalize(hire["talent_name"])
        candidate_match = normalized_candidate_names.get(normalized_candidate)
        candidate_score = 1.0 if candidate_match else 0.0
        candidate = candidate_by_name.get(candidate_match or "", {})
        if not candidate_match:
            unmatched_candidates[hire["talent_name"]] += 1

        enriched.append(
            {
                "date": hire["date"],
                "company": hire["company"],
                "core_member": hire["core_member"] == "Yes",
                "candidate": hire["talent_name"],
                "role": hire["role_title"],
                "monthly_salary": float(hire["monthly_salary"]),
                "primary": taxonomy.get("primary") or "Unmapped",
                "specialty": taxonomy.get("specialty") or "Unmapped",
                "structure": taxonomy.get("structure") or "Unmapped",
                "video_url": candidate.get("video_url") or None,
                "company_match_score": round(company_score, 3),
                "candidate_match_score": round(candidate_score, 3),
            }
        )

    by_primary = defaultdict(list)
    for hire in enriched:
        by_primary[hire["primary"]].append(hire)

    segments = []
    for primary, segment_hires in by_primary.items():
        salaries = [hire["monthly_salary"] for hire in segment_hires]
        segments.append(
            {
                "primary": primary,
                "hires": len(segment_hires),
                "companies": len({hire["company"] for hire in segment_hires}),
                "salary": money_stats(salaries),
                "top_roles": Counter(hire["role"] for hire in segment_hires).most_common(5),
                "videos_available": sum(bool(hire["video_url"]) for hire in segment_hires),
                "records": segment_hires,
            }
        )
    segments.sort(key=lambda segment: (-segment["hires"], segment["primary"]))

    output = {
        "month": args.month,
        "cohort": "core_members" if args.core_only else "all_signed_offers",
        "summary": {
            "hires": len(enriched),
            "companies": len({hire["company"] for hire in enriched}),
            "salary": money_stats([hire["monthly_salary"] for hire in enriched]),
            "videos_available": sum(bool(hire["video_url"]) for hire in enriched),
        },
        "segments": segments,
        "data_quality": {
            "unmatched_companies": unmatched_companies,
            "unmatched_candidates": unmatched_candidates,
            "note": "The latest local signed-offer export ends in July 2026. Use the live database for August and later editions.",
        },
    }
    print(json.dumps(output, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
