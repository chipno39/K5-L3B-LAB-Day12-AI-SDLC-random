# Kế hoạch Phase 2 (≤ 1 trang)

- **Mục tiêu:** Contract v1.1 chạy trọn vòng ngày (sáng → tối → cửa hàng, D1–D5) và chơi được trên giao diện; gắn tag `phase-2` trước 1:55; đóng băng code 1:45.

- **Việc / người / phụ thuộc:**

| Việc (AC tự đặt) | Người | Phụ thuộc |
|---|---|---|
| AC-P2-01 gather v1.1: 6 nguyên liệu, cá bơi/sinh theo lịch, Cá Sấu Năm Chèo | Đạt (`sim/gather`) | xong, đã merge |
| AC-P2-02 `--mode day`, Shop (oxy/Máu), Pause trong `runner`/`headless` | Đạt | xong, đã merge |
| AC-P2-03 quan v1.1: 2 bếp, 4 bàn, 6 món, lọc thực đơn theo `day_plan` | Huy (`sim/quan`) | AC-P2-02 |
| AC-P2-04 live: `--mode day --days`, nhận `pause`/`shop_done`/`buy`, màn chờ UI | Duy (`client/ui`) | AC-P2-02 |
| AC-P2-05 UI gather: Cá Sấu + cảnh báo "Thủy quái!"/"Hết hơi!", cá bơi theo hướng, nguyên liệu mới, danh sách cần lấy | Duy | AC-P2-01 |
| AC-P2-06 UI quan: 2 bếp / 4 bàn, thực đơn theo kế hoạch ngày, nhãn ngày | Duy | AC-P2-03 |
| AC-P2-07 UI: menu chính, giới thiệu ngày/buổi tối, kết quả ngày, cửa hàng, tổng kết, pause (P/Esc) | Duy | AC-P2-02 |
| AC-P2-08 test `quan` v1.1 / `day` / regression P1, proof, `docs/verification/phase-2.md`, Skill #2 | Đức Anh (`qa`) | AC-P2-03 |
| AC-P2-09 retro Phase 2 (3 phút cuối) + README/CREDITS cập nhật | Duy (Scrum) | — |

- **Mốc giờ (Scrum: Duy nhắc):** phút 20 smoke tích hợp (`--mode day` chạy được từ đầu đến cuối) · 1:25 standup · 1:45 đóng băng · 1:45–1:53 `check_team.py` + full test + gom proof · tag `phase-2` chậm nhất 1:55.

- **Rủi ro:**
  1. Quan trong `day` có lệch PRD (đã báo Huy: `hand` payload, `order_status`, `no_dish`, đóng ca…) → test ẩn có thể fail; UI nhận cả hai dạng nên không vỡ.
  2. Màn chờ UI giãn nhịp thời gian thực của live (sim đứng yên khi hiện); đây chỉ là lớp UI, không đổi luật/headless. Cần ghi rõ trong README.
  3. Máy Windows không có `python3`: test hộp đen cần alias.
  4. Chưa chơi tay trọn 5 ngày trên trình duyệt thật; mới kiểm bằng test HTTP + snapshot thật + ảnh chụp.
