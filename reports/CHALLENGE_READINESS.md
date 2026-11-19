# Challenge Readiness Report

- **Python:** `3.14.6` (stdlib-only validator & factory)
- **Clean Calibration (`runs/clean`):** `0` rule errors, `7` semantic candidates
- **Practice Seed (`runs/r9007`):** `14` rule errors, `30` candidates in `119.116s`
- **Estimated Human Review Time (at ~20s/candidate):** ~`10.0` minutes for `30` candidates (fits comfortably in 40-min / 60-min window with parallel reviewers).
- **Commands:**
  - `python tools/qc_factory.py doctor`
  - `python tools/qc_factory.py benchmark`
  - `python tools/qc_factory.py challenge --input delivery --out-dir submission/de_an --serve`
  - `python tools/qc_factory.py finalize --run submission/de_an`
