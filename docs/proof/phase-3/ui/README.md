# Bằng chứng UI Phase 3 (TV 3 — Duy): kho cá thể + độ tươi (Contract v1.2)

| Ảnh | Dữ liệu | Cho thấy |
|---|---|---|
| `gather-v12-snapshot-that.png` | snapshot gather **thật** (nền v1.2 của Đạt, `feat/p3-freshness-v12`) qua `mk_real_v12.py` | thanh độ tươi từng ô, hàng ươn (< 30) có nhãn "ươn" + viền đỏ, toast `spoiled` thật (`I4`, `I5`), tóm tắt "tươi TB %, n ươn" |
| `quan-v12-snapshot-that.png` | snapshot quan **thật** (quan v1.2 của Huy, `feat/p3-quan`, bản tích hợp `qa/phase-3` 407ee3b) | `stock[]` mảng cá thể, khách C1 `reserved: ["I1"]`, **kho khả dụng đã bỏ đúng cá thể bị giữ**, hàng ươn trong kho, toast "Khách mới" |
| `gather-do-tuoi-hang-uon.png`, `quan-kho-kha-dung-theo-ca-the.png` | snapshot **mô phỏng** (`to_v12.py`) dựng trước khi nền v1.2 có trên `main` | cùng giao diện, dùng để thiết kế; hai ảnh `*-snapshot-that.png` là bằng chứng chính |

Kiểm tra kèm theo:
- Chạy script của `index.html` trong Node với canvas giả trên snapshot thật: không lỗi runtime.
- Chuyển gather → quan trong `LiveGame` (`--mode day`) với giỏ có hàng: chạy, không lỗi (trước khi quan v1.2 có thì lỗi `dict(inventory)`).
- Toàn bộ test trên bản tích hợp `qa/phase-3` + UI của Duy: **106/106 xanh**.

Giới hạn trung thực:
- Chưa chơi tay trọn vòng ngày với kho cá thể trên trình duyệt thật; ảnh là trạng thái tĩnh từ snapshot thật.
- `order_status` của quan vẫn là `waiting/cooking/eating` (không theo PRD `reserved/assigned/served`); UI nhận cả hai.
- Ảnh quan chụp ở thời điểm khách mới đến (chưa nấu); chưa chụp các bước nấu / giữ lại khi ươn.
