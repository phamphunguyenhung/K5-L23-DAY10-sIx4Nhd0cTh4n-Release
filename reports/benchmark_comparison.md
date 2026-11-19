# Benchmark Comparison (Authorized Datasets)

| Dataset | Available | Rule Errors | Semantic Candidates | Tiers (E/M/H) | Elapsed (s) | Peak Mem (MB) |
|---|---:|---:|---:|---|---:|---:|
| clean_calib_50 | Yes | 0 | 7 | 0/0/7 | 12.907 | 1.06 |
| practice_r9007_250 | Yes | 14 | 31 | 14/3/28 | 72.862 | 3.39 |

## Breakdown by Type
- **clean_calib_50 candidates:** `{'class_swap': 1, 'missing_box': 6}`
- **practice_r9007_250 rule errors:** `{'bbox_out_of_bounds': 2, 'duplicate_box': 1, 'guideline_mismatch': 2, 'invalid_category_id': 1, 'invalid_class': 2, 'missing_image': 1, 'scene_leak': 1, 'thing_overlap': 2, 'wrong_hash': 2}`
- **practice_r9007_250 candidates:** `{'bbox_drift': 1, 'class_swap': 10, 'instance_merge': 5, 'missing_box': 15}`
- **practice_r9007_250 trace counts:** `{'tier_a': 4, 'tier_b': 3, 'notify': 2}` (P5 rerun)
