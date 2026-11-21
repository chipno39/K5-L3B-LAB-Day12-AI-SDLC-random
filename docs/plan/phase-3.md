# Kế hoạch Phase 3 — Mùa Nước Nổi, Contract v1.2 (≤ 1 trang)

- **Mục tiêu:** chuyển kho đếm sang **kho cá thể** `{id, kind, fresh}` với độ tươi (gather hao 0.5/s, quán hao 0.25/s, ươn khi < 30); chơi được và hiển thị rõ độ tươi / hàng ươn; gắn tag `phase-3` trước 2:30; đóng băng code 2:20.

- **Việc / người / phụ thuộc:**

| Việc (AC tự đặt) | Người | Phụ thuộc |
|---|---|---|
| AC-P3-01 nền v1.2: `game.contract.json` (`freshness`), schema kho cá thể trong `inventory`/`scenario`, kho đếm cũ → mã 2, hao tươi + `spoiled` ở gather, giữ ID `I1..` xuyên pha/ngày, cập nhật contract + CHANGELOG | Đạt (`sim/gather`, Integrator) | — (làm trước, đẩy `main` đầu tiên) |
| AC-P3-02 quan v1.2: `stock[]`, hao 0.25/s + `spoiled`, `reserved` là mảng ID (tươi nhất, hòa theo id), nhả + thử giữ lại 1 lần khi ươn, `base_price = floor(price × avg_fresh / 100)`, `cook_started.items` là mảng cá thể | Huy (`sim/quan`, PO) | AC-P3-01 |
| AC-P3-03 UI đọc `hold[]`/`stock[]` mảng cá thể: thanh độ tươi, hàng ươn (< 30) có nhãn + màu, tóm tắt "tươi TB %, n ươn", kho khả dụng bỏ đúng ID bị giữ | Duy (`client/ui`) | AC-P3-01 (schema `fresh`, ngưỡng, `spoiled`) |
| AC-P3-04 UI: toast `spoiled`; màn giới thiệu buổi tối / cửa hàng dùng kho cá thể; `live.py` chuyển tiếp khối `freshness` | Duy | AC-P3-01 |
| AC-P3-05 cập nhật test P1–P2 sang kho cá thể (ghi rõ lý do), test ngưỡng 30, giữ lại khi ươn, chốt giá theo tươi, kho đếm cũ → mã 2; proof + `docs/verification/phase-3.md` | Đức Anh (`qa`) | AC-P3-01..02 |
| AC-P3-06 proof UI Phase 3, README/CREDITS cập nhật, dòng AI log, nhắc mốc (Scrum) | Duy | — |

- **Mốc giờ (Scrum: Duy nhắc):** 3 phút đầu chốt chữ ký `runner` ↔ `sim/*` ↔ `live/ui` (hành động từ retro P2) · giữa phase smoke `--mode day` chạy từ đầu đến cuối với kho cá thể · 2:20 đóng băng · 2:20–2:28 `check_team.py` + full test + gom proof · tag `phase-3` chậm nhất 2:30.

- **Rủi ro:**
  1. UI viết trước khi nền v1.2 có trên `main` → tên trường (`fresh`, ngưỡng, dạng event `spoiled`) có thể lệch. Giảm thiểu: UI nhận cả dạng cũ và mới, ngưỡng mặc định 30 nếu contract chưa khai; kiểm lại ngay khi Đạt đẩy.
  2. Đổi schema kho kéo theo test P1–P2 và proof cũ: cần Đức Anh cập nhật cùng lúc, tránh đỏ `main`.
  3. Quan của Huy còn một số điểm lệch PRD (đã báo ở Phase 1–2): có thể dồn lại khi đổi sang kho cá thể.
  4. Chưa chơi tay trọn vòng ngày với kho cá thể trên trình duyệt thật.
