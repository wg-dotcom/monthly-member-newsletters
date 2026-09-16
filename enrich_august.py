#!/usr/bin/env python3
"""Conservatively enrich August hires with local candidate profile data."""

from __future__ import annotations

import json
import re
import unicodedata
from collections import defaultdict
from difflib import SequenceMatcher
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "monthly-member-newsletters" / "data" / "august-2026.json"
CANDIDATES = ROOT / "sourcing-matcher" / "data" / "candidates_full.json"


def normalize(value: str) -> str:
    text = unicodedata.normalize("NFKD", value or "")
    text = text.encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", " ", text).strip()


def unique(items: list[dict]) -> dict | None:
    by_id = {item.get("id") or item.get("ats_id") or item.get("name"): item for item in items}
    return next(iter(by_id.values())) if len(by_id) == 1 else None


def main() -> None:
    data = json.loads(SOURCE.read_text(encoding="utf-8"))
    candidates = json.loads(CANDIDATES.read_text(encoding="utf-8"))

    exact: dict[str, list[dict]] = defaultdict(list)
    first_name: dict[str, list[dict]] = defaultdict(list)
    first_last_initial: dict[tuple[str, str], list[dict]] = defaultdict(list)

    for candidate in candidates:
        name = normalize(str(candidate.get("name") or ""))
        if not name:
            continue
        tokens = name.split()
        exact[name].append(candidate)
        first_name[tokens[0]].append(candidate)
        if len(tokens) > 1:
            first_last_initial[(tokens[0], tokens[-1][0])].append(candidate)

    matched = 0
    matched_with_video = 0
    for hire in data["hires"]:
        if hire.get("customer_type") != "Active Member":
            continue

        target = normalize(hire.get("candidate_name", ""))
        tokens = target.split()
        match = unique(exact.get(target, []))
        method = "exact" if match else ""

        if not match and len(tokens) == 1:
            match = unique(first_name.get(tokens[0], []))
            method = "unique_first_name" if match else ""

        if not match and len(tokens) == 2 and len(tokens[-1]) == 1:
            match = unique(first_last_initial.get((tokens[0], tokens[-1]), []))
            method = "unique_first_last_initial" if match else ""

        if not match and len(tokens) >= 2 and len(tokens[-1]) > 1:
            pool = first_name.get(tokens[0], [])
            scored = sorted(
                [
                    (
                        SequenceMatcher(None, target, normalize(str(item.get("name") or ""))).ratio(),
                        item,
                    )
                    for item in pool
                ],
                key=lambda pair: pair[0],
            )
            if scored and scored[-1][0] >= 0.91:
                gap = scored[-1][0] - (scored[-2][0] if len(scored) > 1 else 0)
                if gap >= 0.04:
                    match = scored[-1][1]
                    method = "high_confidence_name"

        if not match:
            hire["candidate_profile_match"] = "unresolved"
            continue

        matched += 1
        video_url = str(match.get("video_url") or "").strip()
        if video_url:
            matched_with_video += 1
        hire.update(
            candidate_profile_match=method,
            candidate_profile_name=match.get("name") or "",
            role_title=match.get("job_title") or "",
            department=match.get("department") or "",
            country=match.get("country") or "",
            monthly_rate=str(match.get("rate") or match.get("target_comp") or ""),
            video_url=video_url,
        )

    data["enrichment"] = {
        "active_member_hires": sum(h.get("customer_type") == "Active Member" for h in data["hires"]),
        "candidate_profiles_matched": matched,
        "matched_profiles_with_video_url": matched_with_video,
        "method": "Exact or unique conservative name matching against the local candidate mirror. Unresolved records stay unresolved.",
    }
    print(json.dumps(data, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
