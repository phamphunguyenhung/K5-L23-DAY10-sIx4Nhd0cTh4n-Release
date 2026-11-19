"""Build the P5 trace from the delivered ticket, guideline, jobs, and YOLO labels."""

from __future__ import annotations

import argparse
import json
import math
import re
from pathlib import Path

from qc_factory_day10.adapters.delivery_reader import load_delivery, safe_rel_path

VERSION = r"v\d+(?:\.\d+)+"
VERSION_HEADING = re.compile(rf"^##[ \t]+({VERSION})[ \t]*$", re.MULTILINE)
CLASS_CHANGE = re.compile(r"^[ \t]*[-*][ \t]+(?:lớp|class)[ \t]+`([^`\r\n]+)`[ \t]*:", re.MULTILINE | re.IGNORECASE)
COMPACT_CHANGE = re.compile(
    rf"^({VERSION})[ \t]*(?:→|->|to)[ \t]*{VERSION}[ \t]*:[ \t]*`?([^`\r\n]+?)`?[ \t]+rule updated\b",
    re.MULTILINE | re.IGNORECASE,
)


def _read_document(delivery: Path, relative: str) -> str:
    path = safe_rel_path(delivery, relative)
    if path is None or not path.is_file():
        raise ValueError(f"Thiếu tài liệu hợp lệ trong delivery: {relative}")
    return path.read_text(encoding="utf-8")


def _changed_rule(changelog: str) -> tuple[str, str]:
    headings = list(VERSION_HEADING.finditer(changelog))
    for current, previous in zip(headings, headings[1:]):
        match = CLASS_CHANGE.search(changelog, current.end(), previous.start())
        if match:
            return previous[1], match[1].strip()

    # The Factory's compact changelog format is also used in integration tests.
    compact = COMPACT_CHANGE.search(changelog)
    if compact:
        return compact[1].lower(), compact[2].strip()
    raise ValueError("Không xác định được guideline cũ và lớp đổi quy tắc từ changelog.md")


def _has_detection(label_path: Path, class_id: int) -> bool:
    for line in label_path.read_text(encoding="utf-8").splitlines():
        fields = line.split()
        if len(fields) != 5:
            continue
        try:
            if int(fields[0]) != class_id:
                continue
            xc, yc, width, height = map(float, fields[1:])
        except ValueError:
            continue
        if all(math.isfinite(value) for value in (xc, yc, width, height)) and width > 0 and height > 0:
            return True
    return False


def build_trace_from_delivery(delivery: Path, out_path: Path) -> dict[str, list[str]]:
    """Write tier_a, tier_b and notify using the guideline assigned to each job."""
    if out_path.resolve().is_relative_to(delivery.resolve()):
        raise ValueError("Hãy ghi trace.json bên ngoài thư mục delivery")

    changelog = _read_document(delivery, "guideline/changelog.md")
    ticket = _read_document(delivery, "incoming/ticket.md")
    old_guideline, changed_class = _changed_rule(changelog)
    reported_scenes = set(re.findall(r"\bscene_\d+\b", ticket))

    ctx = load_delivery(delivery)
    class_id = next((cid for cid, name in ctx.classes.items() if name.casefold() == changed_class.casefold()), None)
    if class_id is None:
        raise ValueError(f"Lớp {changed_class!r} trong changelog.md không có trong classes.txt")
    manifest_items = ctx.manifest.get("items")
    metadata_items = ctx.metadata.get("items")
    if not isinstance(manifest_items, dict) or not isinstance(metadata_items, list) or not ctx.jobs:
        raise ValueError("Cần manifest.json, metadata.json và jobs.csv hợp lệ để truy vết")

    tier_a: set[str] = set()
    tier_b: set[str] = set()
    notify: set[str] = set()
    for item in metadata_items:
        image = item["image"]
        job = ctx.jobs.get(item["job_id"], {})
        if (job.get("guideline") or "").strip() != old_guideline:
            continue
        label_rel = manifest_items.get(image, {}).get("label", "")
        label_path = safe_rel_path(delivery, label_rel)
        if label_path is None or not label_path.is_file() or not _has_detection(label_path, class_id):
            continue
        tier = tier_a if item["scene_id"] in reported_scenes else tier_b
        tier.add(image)
        for role in ("annotator", "reviewer"):
            person = (job.get(role) or "").strip()
            if person:
                notify.add(person)

    trace = {"tier_a": sorted(tier_a), "tier_b": sorted(tier_b), "notify": sorted(notify)}
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(trace, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    return trace


def main() -> int:
    parser = argparse.ArgumentParser(description="P5: truy vết ticket của team AI từ delivery")
    parser.add_argument("delivery", type=Path)
    parser.add_argument("--out", required=True, type=Path, help="Đường dẫn trace.json bên ngoài delivery")
    args = parser.parse_args()

    try:
        trace = build_trace_from_delivery(args.delivery, args.out)
    except (OSError, ValueError) as exc:
        parser.exit(2, f"Lỗi truy vết: {exc}\n")
    counts = ", ".join(f"{key}={len(values)}" for key, values in trace.items())
    print(f"{args.out}: {counts}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
