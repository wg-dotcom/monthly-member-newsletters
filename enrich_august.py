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
OUTPUT = ROOT / "monthly-member-newsletters" / "data" / "august-2026-enriched.json"
CANDIDATES = ROOT / "sourcing-matcher" / "data" / "candidates_full.json"


# Verified against the CORE candidate database, the GTC candidate sheet, and
# existing Sagan candidate presentation pages. The key includes the company so
# an abbreviated candidate name cannot collide with a past application.
VIDEO_OVERRIDES: dict[tuple[str, str], dict[str, str]] = {
    ("viridiana t", "molloy roofing company"): {
        "candidate_profile_name": "Viridiana T.",
        "role_title": "Scheduling Coordinator - Residential Estimating",
        "video_url": "https://candidate-video.com/uploads/308a2a46-0b62-49f8-aead-330956067e0d",
    },
    ("monica cornejo", "mw lawn landscape"): {
        "candidate_profile_name": "Monica Cornejo Sernaque",
        "role_title": "Office Manager",
        "video_url": "https://candidate-video.com/uploads/b37bf656-a041-4e7d-840d-594c7532b339",
    },
    ("carlos v", "rubicon"): {
        "candidate_profile_name": "Carlos V.",
        "role_title": "Regional Sourcing Associate",
        "video_url": "https://drive.google.com/file/d/1Opc_-bbzsHyhz81vj1kK6kX4lzNgkk9r/view?usp=drive_link",
    },
    ("andrea martinez", "rubicon"): {
        "candidate_profile_name": "Andrea M.",
        "role_title": "Training Content Specialist",
        "video_url": "https://drive.google.com/file/d/14ce-u_-qabLiLy0KeT0bHYlpKcjnluW6/view?usp=drive_link",
    },
    ("jose z", "rubicon"): {
        "candidate_profile_name": "Jose Z.",
        "role_title": "Regional Sourcing Associate",
        "video_url": "https://drive.google.com/file/d/1bUwIrXyASuLYunRLYa0kAI5XJ_4JfxFG/view?usp=drive_link",
    },
    ("samuel garrido", "rubicon"): {
        "candidate_profile_name": "Samuel G.",
        "role_title": "Key Account Analyst",
        "video_url": "https://drive.google.com/file/d/19MypRuyIcNgpUxy7fFZJCv4lI_v1eCCh/view?usp=drive_link",
    },
    ("joaquin e", "peak power"): {
        "candidate_profile_name": "Joaquin E.",
        "role_title": "Night Dispatch & Logistics Coordinator",
        "video_url": "https://candidate-video.com/uploads/96fa2d8f-c923-44d2-90ee-a94627fcb9e8",
    },
    ("jovanne z", "bonded"): {
        "candidate_profile_name": "Jovanne Z.",
        "role_title": "Technical Support Specialist",
        "video_url": "https://drive.google.com/file/d/1bghLpCmJUlI4TI-ek3Z1Fx2R-KGooAK7/view",
    },
    ("arleth carbaja", "docs dermatology"): {
        "candidate_profile_name": "Arleth Carbaja",
        "role_title": "Medical Administrative Assistant",
        "video_url": "https://drive.google.com/file/d/1peMfemdNP6oQrDHDYLa4fKkmAz3Kj62y/view?usp=drive_link",
    },
    ("alanna voigt", "victory sprinkler"): {
        "candidate_profile_name": "Alanna V.",
        "role_title": "Customer Success",
        "video_url": "https://drive.google.com/file/d/1CDBlFd7WvxymqNZGFUDEbvt_yUftIxdw/view?usp=sharing",
    },
    ("natalia e", "riverbend landscapes tree service"): {
        "candidate_profile_name": "Natalia E.",
        "role_title": "Service Coordinator & Dispatcher",
        "video_url": "https://drive.google.com/file/d/1b2GSDmK_9j6viPnmt1d_luwSQtl5Zh-V/view?usp=drive_link",
    },
    ("fernanda padilla", "divi"): {
        "candidate_profile_name": "Fernanda P.",
        "role_title": "Executive & Operations Coordinator",
        "video_url": "https://drive.google.com/file/d/1x1lEglF_IDdAKTy27Jf7Z7Mz1wUJvmFJ/view?usp=sharing",
    },
    ("miguel m", "emerson property management"): {
        "candidate_profile_name": "Miguel M.",
        "role_title": "Project Coordinator",
        "video_url": "https://drive.google.com/file/d/1EuKRzqqBujNv_4N1aELLhWolRtUyGuUT/view?usp=drive_link",
    },
    ("ana b", "emerson property management"): {
        "candidate_profile_name": "Ana B.",
        "role_title": "Leasing Specialist",
        "video_url": "https://ta-dashboard-supabase.replit.app/api/screening-candidates/rec2bgISxXgaiZADS/video-intro",
    },
    ("douglas m", "austin cleaning crew"): {
        "candidate_profile_name": "Douglas M.",
        "role_title": "Sales Development Representative",
        "video_url": "https://drive.google.com/file/d/123KY5P_DAuzhvNqjkTiwioUm89_eZ6sI/view?usp=drive_link",
    },
}


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
        company = normalize(hire.get("company_name", ""))
        override = VIDEO_OVERRIDES.get((target, company))
        if override:
            hire.update(
                candidate_profile_match="verified_source_override",
                department="",
                country="",
                monthly_rate="",
                **override,
            )
            matched += 1
            matched_with_video += 1
            continue

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
        "method": "Verified CORE/GTC/presentation links first, then exact or unique conservative name matching against the local candidate mirror. Unresolved records stay unresolved.",
    }
    OUTPUT.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(
        f"Wrote {OUTPUT.name}: {matched} candidate profiles matched, "
        f"{matched_with_video} with direct video links."
    )


if __name__ == "__main__":
    main()
