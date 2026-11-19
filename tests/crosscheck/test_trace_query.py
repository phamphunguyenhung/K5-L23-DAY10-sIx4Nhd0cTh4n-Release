import json
import tempfile
import unittest
from pathlib import Path

from trace.trace_query import build_trace_from_delivery


class TraceQueryTest(unittest.TestCase):
    """Regression tests for cross-checking the ticket against the delivered labels."""

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.delivery = self.root / "delivery"
        self.out = self.root / "result" / "trace.json"
        self.write("guideline/changelog.md", (
            "# Changelog guideline\n\n"
            "## v2.4\n"
            "- Lớp `hot dog`: chỉnh quy tắc cho vật bị che.\n\n"
            "## v2.3\n- Bản dùng cho các job cũ.\n"
        ))
        self.write("incoming/ticket.md", "Lỗi hot dog ở scene_11. Giữ quy tắc person và dog.\n")
        self.write("classes.txt", "0 person\n1 dog\n9 hot dog\n")
        self.write("jobs.csv", (
            "job_id,annotator,reviewer,guideline\n"
            "old_a,A03,Q01,v2.3\n"
            "old_b,A05,Q01,v2.3\n"
            "old_other,A07,Q04,v2.3\n"
            "new,A08,Q05,v2.4\n"
        ))
        # The image-level value deliberately disagrees with the job on two images.
        records = [
            ("img_0007", "scene_22", "old_b", "v2.3", "9 .5 .5 .2 .2\n"),
            ("img_0002", "scene_11", "old_a", "v2.4", "9 .6 .6 .3 .3\n9 .5 .5 .2 .2\n"),
            ("img_0003", "scene_11", "new", "v2.3", "9 .5 .5 .2 .2\n"),
            ("img_0004", "scene_11", "old_other", "v2.3", "0 .5 .5 .2 .2\n1 .5 .5 .2 .2\n"),
            ("img_0005", "scene_11", "old_other", "v2.3", "9\n9 .5 .5 nan .4\n9 .5 .5 0 .4\n"),
            ("img_0006", "scene_11", "old_other", "v2.3", None),
            ("img_0001", "scene_11", "old_a", "v2.3", "9 .5 .5 .2 .2\n"),
        ]
        self.write("metadata.json", json.dumps({"items": [
            {"image": image, "scene_id": scene, "job_id": job, "guideline_version": guideline}
            for image, scene, job, guideline, _ in records
        ]}))
        self.write("manifest.json", json.dumps({"items": {
            image: {"label": f"labels/{image}.txt"} for image, *_ in records
        }}))
        for image, _, _, _, label in records:
            if label is not None:
                self.write(f"labels/{image}.txt", label)

    def write(self, relative, text):
        path = self.delivery / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def test_uses_exact_changed_class_and_job_guideline(self):
        expected = {
            "tier_a": ["img_0001", "img_0002"],
            "tier_b": ["img_0007"],
            "notify": ["A03", "A05", "Q01"],
        }
        self.assertEqual(build_trace_from_delivery(self.delivery, self.out), expected)
        self.assertEqual(json.loads(self.out.read_text(encoding="utf-8")), expected)

    def test_compact_changelog_matches_the_same_rule(self):
        expected = build_trace_from_delivery(self.delivery, self.out)
        self.write("guideline/changelog.md", "v2.3 -> v2.4: hot dog rule updated\n")
        self.assertEqual(build_trace_from_delivery(self.delivery, self.out), expected)

    def test_missing_rule_does_not_publish_empty_trace(self):
        self.write("guideline/changelog.md", "# Changelog đang soạn\n")
        with self.assertRaisesRegex(ValueError, "changelog.md"):
            build_trace_from_delivery(self.delivery, self.out)
        self.assertFalse(self.out.exists())

    def test_output_cannot_overwrite_delivery(self):
        metadata = self.delivery / "metadata.json"
        original = metadata.read_bytes()
        with self.assertRaisesRegex(ValueError, "delivery"):
            build_trace_from_delivery(self.delivery, metadata)
        self.assertEqual(metadata.read_bytes(), original)
