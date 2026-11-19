# Day 10 Pipeline Integration Summary — `run_20261119`

- **Pipeline Version:** `day10-oneshot-v1`
- **Team:** `sIx4Nhd0cTh4n`
- **Generated At (UTC):** `2026-11-19T12:15:00.558576+00:00`
- **Submission Status:** `PENDING_HUMAN_REVIEW` *(0 fake rows written to `review_log.csv`; 827 dedup semantic candidates across 725 images await human visual review)*
- **Outer Archive:** `20 mã đề-20261119T113108Z-1-001.zip` (`460,085,750` bytes, SHA-256 `e9f6d48ae41c62ff4185adf2f6db107eebe69f19abbf5f536edc9b92876f87d1`)

## 1. Global KPIs & Verification Status

| Metric | Value | Notes |
|---|---:|---|
| Total Exams | 20 | `de_an_01` .. `de_an_20` (all preflight ready) |
| Total Images | 5,000 | 250 images per exam |
| Auto-Verified Rule Errors | 196 | Written to official `errors.json` across 20 exams |
| Semantic Candidates (Raw) | 847 | `class_swap`: 329, `missing_box`: 347, `instance_merge`: 157, `bbox_drift`: 14, `category_swap`: 0 |
| Semantic Candidates (Dedup) | 827 | 20 duplicates removed (`hard`: 685, `medium`: 142) |
| Images To Open (Human Review Queue) | 725 | `hard_images`: 590, `medium_only_images`: 135 (14.50% of 5,000) |
| Auto-Verified Only Images | 146 | Rule errors only, no semantic candidate |
| NO ACTION Images | 4,129 | `725 + 146 + 4,129 = 5,000` |
| Review Completed | 0 | 0 rows in `review_log.csv` across all 20 exams |
| Review Pending | 827 | 827 dedup candidates (847 raw) pending human review |
| Trace Status | PASSED | 20/20 passed (`tier_a`: 47, `tier_b`: 92, `notify`: 85) |
| Schema Status | PASSED | 20/20 passed (8/8 schema checks per exam) |
| Verification Status | PASSED | 20/20 passed, 0 contradictions, `de_an_08 == de_an_20` determinism PASSED |

### Rule Error Breakdown (196 Total)

| Rule Type | Count |
|---|---:|
| `bbox_out_of_bounds` | 29 |
| `duplicate_box` | 7 |
| `guideline_mismatch` | 33 |
| `invalid_category_id` | 11 |
| `invalid_class` | 11 |
| `missing_image` | 27 |
| `scene_leak` | 20 |
| `thing_overlap` | 27 |
| `wrong_hash` | 31 |

## 2. Pipeline Stages (10/10 Completed)

| Stage | Agent | Status | Completed At (UTC) | Runtime (s) | Artifact |
|---|---|---|---|---:|---|
| `1_preflight` | Agent 1: Preflight & Archive Extraction | `completed` | `2026-11-19T11:52:05.830699+00:00` | 42.7116 | `archive_inventory.json` |
| `2_rules` | Agent 2: Rule Engine | `completed` | `2026-11-19T12:03:38.251221+00:00` | 627.2437 | `agent2_rules_summary.json` |
| `3_yolo_geometry` | Agent 3: YOLO Geometry | `completed` | `2026-11-19T11:55:47.648801+00:00` | 106.4659 | `agent3_yolo_summary.json` |
| `4_panoptic_analysis` | Agent 4: Panoptic Analysis | `completed` | `2026-11-19T11:57:32.366989+00:00` | 177.8402 | `agent4_panoptic_summary.json` |
| `5_semantic_matching` | Agent 5: Semantic Matching | `completed` | `2026-11-19T12:08:52.091318+00:00` | 0.2241 | `agent5_semantic_summary.json` |
| `6_candidate_ranking` | Agent 6: Candidate Ranking | `completed` | `2026-11-19T12:09:44.573406+00:00` | 1.8290 | `agent6_ranking_summary.json` |
| `7_visual_evidence` | Agent 7: Visual Evidence Generation | `completed` | `2026-11-19T12:11:07.974500+00:00` | 19.2993 | `agent7_evidence_summary.json` |
| `8_traceability` | Agent 8: Traceability | `completed` | `2026-11-19T11:57:34.034496+00:00` | 3.4328 | `agent8_trace_summary.json` |
| `9_independent_verification` | Agent 9: Independent Verification | `completed` | `2026-11-19T12:13:06.535327+00:00` | 6.3070 | `agent9_verification_summary.json` |
| `10_integration_export` | Agent 10: Integration & Export | `completed` | `2026-11-19T12:15:00.558576+00:00` | 0.3442 | `summary.json` |

## 3. Per-Exam Breakdown (`de_an_01` .. `de_an_20`)

| Exam | Rank | Tier | Images | Rule Errors | Raw Cand | Dedup Cand | To Open | Auto-Only | No Action | Review Done | Review Pending | Trace | Schema | Verify | ZIP (bytes) |
|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|---:|
| `de_an_01` | 15 | MODERATE | 250 | 10 | 44 | 44 | 40 | 8 | 202 | 0 | 44 | PASSED | PASSED | PASSED | 531 |
| `de_an_02` | 1 | EASIEST | 250 | 10 | 28 | 26 | 23 | 8 | 219 | 0 | 26 | PASSED | PASSED | PASSED | 533 |
| `de_an_03` | 16 | HARDEST | 250 | 10 | 51 | 49 | 40 | 7 | 203 | 0 | 49 | PASSED | PASSED | PASSED | 522 |
| `de_an_04` | 3 | EASIEST | 250 | 10 | 35 | 34 | 33 | 8 | 209 | 0 | 34 | PASSED | PASSED | PASSED | 533 |
| `de_an_05` | 7 | MODERATE | 250 | 7 | 39 | 39 | 35 | 5 | 210 | 0 | 39 | PASSED | PASSED | PASSED | 496 |
| `de_an_06` | 19 | HARDEST | 250 | 8 | 48 | 47 | 43 | 5 | 202 | 0 | 47 | PASSED | PASSED | PASSED | 509 |
| `de_an_07` | 8 | MODERATE | 250 | 11 | 42 | 42 | 35 | 8 | 207 | 0 | 42 | PASSED | PASSED | PASSED | 532 |
| `de_an_08` | 11 | MODERATE | 250 | 10 | 45 | 44 | 36 | 8 | 206 | 0 | 44 | PASSED | PASSED | PASSED | 522 |
| `de_an_09` | 18 | HARDEST | 250 | 11 | 47 | 46 | 42 | 8 | 200 | 0 | 46 | PASSED | PASSED | PASSED | 531 |
| `de_an_10` | 17 | HARDEST | 250 | 8 | 52 | 50 | 41 | 3 | 206 | 0 | 50 | PASSED | PASSED | PASSED | 499 |
| `de_an_11` | 4 | EASIEST | 250 | 10 | 37 | 37 | 33 | 7 | 210 | 0 | 37 | PASSED | PASSED | PASSED | 519 |
| `de_an_12` | 5 | EASIEST | 250 | 11 | 38 | 38 | 33 | 9 | 208 | 0 | 38 | PASSED | PASSED | PASSED | 533 |
| `de_an_13` | 13 | MODERATE | 250 | 12 | 42 | 41 | 37 | 10 | 203 | 0 | 41 | PASSED | PASSED | PASSED | 538 |
| `de_an_14` | 10 | MODERATE | 250 | 9 | 43 | 43 | 36 | 7 | 207 | 0 | 43 | PASSED | PASSED | PASSED | 528 |
| `de_an_15` | 9 | MODERATE | 250 | 8 | 37 | 36 | 36 | 5 | 209 | 0 | 36 | PASSED | PASSED | PASSED | 524 |
| `de_an_16` | 2 | EASIEST | 250 | 9 | 37 | 34 | 30 | 7 | 213 | 0 | 34 | PASSED | PASSED | PASSED | 520 |
| `de_an_17` | 14 | MODERATE | 250 | 11 | 42 | 42 | 38 | 9 | 203 | 0 | 42 | PASSED | PASSED | PASSED | 534 |
| `de_an_18` | 6 | MODERATE | 250 | 12 | 41 | 41 | 35 | 11 | 204 | 0 | 41 | PASSED | PASSED | PASSED | 527 |
| `de_an_19` | 20 | HARDEST | 250 | 9 | 54 | 50 | 43 | 5 | 202 | 0 | 50 | PASSED | PASSED | PASSED | 505 |
| `de_an_20` | 12 | MODERATE | 250 | 10 | 45 | 44 | 36 | 8 | 206 | 0 | 44 | PASSED | PASSED | PASSED | 522 |

## 4. Submission Gate ZIPs Verification

- **Directory:** `runs/day10_oneshot/run_20261119/submission_zips/`
- **Total ZIPs Generated:** 20 / 20 (`all_verified_clean`: `True`, `all_under_50mb`: `True`)
- **Entries Per ZIP (Strictly Only):** `submission/de_an/errors.json`, `submission/de_an/review_log.csv`
- **Min ZIP Size:** `496` bytes (`de_an_05`)
- **Max ZIP Size:** `538` bytes (`de_an_13`)
- **Total ZIP Size:** `10,458` bytes
- **Safety Checks:** 0 `delivery/` entries, 0 `_private/` entries, 0 symlinks, 0 fake `confirmed`/`rejected` rows in `review_log.csv`.
