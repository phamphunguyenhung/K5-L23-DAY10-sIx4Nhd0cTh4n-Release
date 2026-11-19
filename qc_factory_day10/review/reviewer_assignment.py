"""Deterministic reviewer assignment grouped by image_id and difficulty tier."""
from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path
from typing import Any


def load_team_members(team_md: Path) -> list[str]:
    """Extract team member names or handles from submission/TEAM.md if present."""
    if not team_md.is_file():
        return ["Reviewer-1", "Reviewer-2", "Reviewer-3"]
    members: list[str] = []
    for line in team_md.read_text(encoding="utf-8").splitlines():
        if (
            line.startswith("|")
            and not line.startswith("|---")
            and "Họ tên" not in line
            and "Họ và tên" not in line
            and "Thành viên" not in line
        ):
            cols = [c.strip() for c in line.strip("|").split("|")]
            if cols and cols[0]:
                handle = next((c for c in cols if c.startswith("@") or "`@" in c), "")
                clean = re.sub(r"[`*]", "", handle or cols[0]).strip()
                if clean and clean not in members:
                    members.append(clean)
    return members or ["Reviewer-1", "Reviewer-2", "Reviewer-3"]


def assign_reviewers(triage_rows: list[dict[str, Any]], reviewers: list[str]) -> list[dict[str, Any]]:
    """Group semantic candidates by image_id and balance workload across reviewers."""
    if not reviewers:
        reviewers = ["Reviewer-1"]

    by_image: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for r in triage_rows:
        if r.get("kind") == "semantic":
            by_image[r["image_id"]].append(r)

    # Sort images by max priority descending so highest-value images distribute evenly
    ordered_imgs = sorted(
        by_image.keys(),
        key=lambda img: (-max(r["priority"] for r in by_image[img]), img),
    )

    loads = [0] * len(reviewers)
    for img in ordered_imgs:
        # Round-robin to least-loaded reviewer
        idx = min(range(len(reviewers)), key=lambda i: (loads[i], i))
        rev = reviewers[idx]
        for r in by_image[img]:
            r["assigned_reviewer"] = rev
            loads[idx] += 2 if r.get("difficulty_tier") == "HARD" else 1
    return triage_rows
