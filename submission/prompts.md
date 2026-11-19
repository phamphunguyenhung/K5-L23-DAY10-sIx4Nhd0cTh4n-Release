# Nhật ký dùng AI (`prompts.md`)

> Ghi lại prompt đã dùng, chỗ AI làm sai/chưa đủ và cách nhóm tự kiểm chứng lại theo [RULES.md](../RULES.md).

## 1. Thiết kế & nâng cấp `qc_factory_day10/` + `validator/validate.py`
- **Prompt / Yêu cầu:** Tái sử dụng kiến trúc từ CVAT Factory (`cache`, `shapestore`, `HTML review`, `frame_profiler`) sang nền tảng QC thuần Python stdlib cho Day10 (`qc_factory_day10/`, `tools/qc_factory.py`, `tools/build_handover.py`), giữ `validator/validate.py` 100% stdlib, bổ sung `instance_merge` và bảo vệ path traversal.
- **Chỗ AI sai / cần sửa:**
  1. Test tổng hợp ban đầu dùng ảnh giả lập `4x4` với 2 box cách tâm `2px`, khiến rule `duplicate_box` (`DUP_CENTER_TOL_PX = 2`) bắt nhầm thành box trùng; nhóm đã sửa fixture lên `20x20` để tách biệt `duplicate_box` và `instance_merge`.
  2. `ReviewStore._connect()` dùng `with sqlite3.connect(...)` trên Windows không tự đóng file descriptor sau transaction, gây `WinError 32` khi cleanup thư mục tạm; đã sửa sang `@contextmanager` gọi `conn.close()` tường minh.
- **Cách kiểm lại:** Chạy `python -m pytest tests/validator/test_validator_rules.py tests/test_qc_factory.py -v` (7/7 PASS), `python tools/qc_factory.py doctor`, `python tools/qc_factory.py benchmark` trên `runs/clean` và `runs/r9007`, và `python scripts/check_handover.py --run runs/r9007`.

## 2. Quy tắc con người review ảnh
- Toàn bộ `review_log.csv` (mục H3) **không** dùng AI tự điền `confirmed`/`rejected`; thành viên nhóm mở ảnh thật qua Review UI (`http://127.0.0.1:8765/`) để tự xác nhận và ghi chú ≥ 20 ký tự.

## 3. Thiết kế P3 Release Gate (`release/`) & P4 Dataset v2 Handover (`handover/`) — Đỗ Anh Hoàng
- **Người thực hiện:** Đỗ Anh Hoàng (`2A202604061` · GitHub: `@AnhHoangDepTrai`)
- **Prompt / Yêu cầu:** Thiết kế module `release/gate.py` đánh giá ngưỡng 2% (Day 7) trên lô v1 và ghi nhận sự kiện `decision` (HOLD/RELEASE), truy vấn blast radius của `R-021` qua `scripts/lineage.py`. Thiết kế `handover/builder.py` tự động hóa toàn bộ quy trình xây dựng gói bàn giao v2 không sửa đè v1, phân loại đúng 3 luồng (rework, sửa kỹ thuật trực tiếp, panoptic độc lập), sinh đầy đủ 7 thành phần cấu trúc (images, labels, rework_queue.csv, manifest.csv, label_summary.csv, truyvet.csv, README.txt), đóng gói zip tái lập `.sha256`, ghi nhận lineage `release` v2 với `parent`, và vượt qua bộ kiểm `check_handover.py` (H1–H15).
- **Chỗ AI làm sai / chưa đủ:**
  1. Ban đầu AI xếp tất cả các ảnh có lỗi trong `errors.json` vào `rework_queue.csv`. Tuy nhiên, các lỗi chỉ thuộc panoptic (`invalid_category_id`, `thing_overlap`, `category_swap`, `instance_merge`) thì nhãn detection của ảnh vẫn hoàn toàn hợp lệ, do đó ảnh phải ở lại trong v2 (báo team panoptic ở phần Ghi chú README) thay vì tách sang rework (sẽ bị FAIL H5).
  2. Với `scene_leak`, AI ban đầu giữ nguyên metadata dẫn đến v2 vẫn bị scene xuất hiện ở cả train và val (FAIL H11). Đã bổ sung logic chuẩn hóa tự động toàn bộ ảnh trong scene về cùng một split (split đa số/train).
  3. Giá trị guideline trong `truyvet.csv` nếu lấy từ metadata của ảnh sẽ bị sai khi gặp lỗi `guideline_mismatch`. Đã sửa để guideline luôn truy xuất từ `jobs.csv` làm single source of truth (đạt H10).
- **Cách kiểm lại:** Viết unit tests (`tests/test_release_gate.py`, `tests/test_handover_builder.py` 4/4 PASS), chạy thực tế trên `runs/r9007`, xác nhận `python scripts/check_handover.py --run runs/r9007` đạt tuyệt đối 15/15 PASS ở các tiêu chí H1–H15.

## 4. P6 — Security, Hidden-test Prep & Reporting (Nguyễn Quốc Hưng, `2A202603324`)

Công cụ: Claude Code (Opus 5), ngày 19/11/2026. **Không dán ảnh nào của lô vào công cụ AI.**

### 4.1 Kiểm điều kiện H17 bằng mã nguồn, không tin mô tả

- **Prompt:** *"Phần P6 của tôi (security.md, chuẩn bị đề ẩn, REPORT.md) có phải đợi P1–P5 không?"*
- **AI trả lời:** `security.md` chỉ cần lô v1 tồn tại, không phụ thuộc pha nào.
- **Chỗ AI thiếu:** không nói ra điều kiện tên ảnh phải nằm trong `manifest.json` của lô v1.
- **Cách kiểm lại:** đọc thẳng `scripts/check_handover.py` dòng 243–249, rồi **chạy lại đúng đoạn logic
  H17 đó** trên file đã viết: ≥ 3 mục `##` mỗi mục ≥ 80 ký tự sau khi bỏ khoảng trắng, mục "khuôn mặt"
  chứa chữ "hold", nêu tên ảnh có trong manifest v1, không còn chuỗi `<<` → PASS trước khi commit.

### 4.2 Nhờ AI viết `tools/review_viewer.py` — 4 chỗ sai

Tìm ra bằng cách render rồi **mở ảnh ra nhìn**, không tin "code chạy xong là đúng":

1. **Cỡ chữ nhân theo hệ số phóng** — ảnh nhỏ phóng ×9 thì nhãn cao 64 px, che gần hết vật.
   Sửa: kẹp cỡ chữ theo chiều cao panel.
2. **Nhãn ở mép phải bị cắt chữ.** Sửa: kéo nhãn vào trong khung trước khi vẽ.
3. **Panel "phóng to" cắt từ ảnh trần**, không có box lẫn viền segment — vô dụng đúng chỗ cần nhìn kỹ
   nhất. Sửa: cắt từ ảnh đã vẽ, và cắt quanh **vật bị nghi** (lấy tên lớp từ `evidence` của ứng viên).
4. **Văng `KeyError: 126` trên ảnh `000000009590`.** Code tra `self.cat[seg["category_id"]]["name"]`,
   mà ảnh này có segment `category_id=126` không nằm trong `categories` — chính là lỗi
   `invalid_category_id` validator vừa bắt. Nghĩa là công cụ **im lặng bỏ qua đúng những ảnh đang có
   lỗi**. Sửa: tra bằng `.get()` và in `category_id 126 (KHÔNG có trong categories)` lên nhãn.
   Lỗi này chỉ lộ ra khi chạy trên lô thật — bộ fixture tự tạo không có ca đó.

- **Cách kiểm lại:** đối chiếu số box vẽ ra với số dòng trong `labels/<ảnh>.txt`, số segment vẽ ra với
  `segments_info` của ảnh đó trong `panoptic.json` (lọc `isthing`). Verdict trong
  `review_log_todo.csv` để **trống** — công cụ không tự chấm.

### 4.3 Số liệu trong `REPORT.md`

Không nhờ AI đoán số. Prompt dùng là *"chạy các lệnh này rồi dán kết quả nguyên văn"*, không phải
*"REPORT.md nên ghi F1 khoảng bao nhiêu"*. Mọi con số đối chiếu với `runs/r9007/report.md` và output
của `python3 tools/qc_factory.py benchmark`.

### 4.4 Ba điểm AI phát hiện khi đọc code của nhóm (đã ghi ở `REPORT.md` mục 6)

- Review UI gửi `pan_boxes` lấy từ `seg["bbox"]` → người xem đang so hai hình chữ nhật, trong khi GUIDE
  Pha 2 nói IoU hai bbox không đủ để phân biệt `bbox_drift` / `instance_merge`.
- Cùng seed 9007 nhưng hai máy ra `release_id` khác nhau, dù mọi số đếm trùng khít.
- Ứng viên `class_swap` ở `000000013774` có `evidence` ghi `box=` rỗng; kiểm lại nhãn thấy dòng
  `80 ...` — `class_id` ngoài 0–79, ảnh đã bị bắt `invalid_class`, nên ứng viên này nhiều khả năng là
  báo thừa.

## 5. P5 — Truy vết ticket với Codex

- Prompt đã dùng là “đã pull code mới về, tiến hành làm P5”.
- Codex phát hiện logic cũ dò mọi tên lớp xuất hiện trong ticket nên từ `train` trong câu về huấn luyện cũng được tính là lớp đổi quy tắc. Code P5 đọc chính xác mục đổi lớp trong changelog và lấy guideline theo `jobs.csv`.
- Đã chạy test hồi quy với tên lớp lồng nhau, guideline ảnh khác guideline job, nhãn thiếu và dòng YOLO hỏng. Đã đối chiếu ba danh sách trên lô r9007 với ticket, changelog, nhãn YOLO và `jobs.csv`, rồi tự đo một lần bằng `score_findings.py --run runs/r9007`.
