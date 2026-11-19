# P5 — Ticket Traceability (`tier_a`, `tier_b`, `notify`)

- **Owner:** Hoàng Trọng Trà (`2A202603342` · `@trahoangdev`)
- **Mục tiêu:** Truy vết ticket của team AI theo `guideline` của job (không theo ảnh), xuất `trace.json` đầy đủ 3 khóa `tier_a`, `tier_b`, `notify` cho cả seed luyện tập và đề ẩn.

Chạy từ thư mục gốc repo trên Windows (`python3` trên macOS/Linux).

```powershell
py -m trace.trace_query runs/r9007/delivery --out runs/r9007/trace.json
py -m trace.trace_query delivery --out submission/de_an/trace.json
```

`tools/qc_factory.py challenge` gọi cùng hàm truy vết. Lệnh riêng chạy được khi chỉ cần tái tạo `trace.json`.

1. Lấy cảnh được báo trong `incoming/ticket.md`, lớp đổi quy tắc và phiên bản trước đó trong `guideline/changelog.md`.
2. Dùng `metadata.json` để nối ảnh với cảnh và job. Đọc guideline từ `jobs.csv` vì guideline ghi ở ảnh có thể bị gài lỗi.
3. Với các job dùng guideline cũ, kiểm tra box detection của đúng lớp trong file nhãn do `manifest.json` chỉ định. Ảnh thuộc cảnh được báo vào `tier_a`. Ảnh đủ điều kiện ở cảnh khác vào `tier_b`.
4. Lấy mã người gán và kiểm của cả hai tầng từ `jobs.csv`. `trace.json` sắp xếp từng danh sách và loại bỏ mục trùng.

Kiểm thử hồi quy bằng `py -m unittest discover -s tests/crosscheck -p test_trace_query.py -v`.
