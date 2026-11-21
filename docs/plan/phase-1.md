# Kế hoạch Phase 1 (≤ 1 trang)

- **Mục tiêu:** chơi được cả hai buổi (`gather` sáng, `quan` tối) đúng phạm vi lõi PRD-0; HUD đọc được; kho nối được qua hai tiến trình headless; gắn tag `phase-1` trước 1:00.

- **Việc / người / phụ thuộc:**

| Việc (AC tự đặt) | Người | Phụ thuộc |
|---|---|---|
| AC-P1-01 gather lát 1–2: oxy, ngạt, ngất, hái, bắt cá, giỏ LIFO, cập bến, ghi kho | Đạt (`sim/gather`) | xong, đã merge |
| AC-P1-02 hợp đồng kho + sự kiện + giao diện sim–UI (`docs/contracts/`) | Đạt | xong |
| AC-P1-03 quan lát 3–4: khách, giữ chỗ, bếp, bưng, phục vụ, tiền, uy tín | Huy (`sim/quan`) | AC-P1-02 (schema kho) |
| AC-P1-04 UI/HUD gather: giờ, oxy, Máu, giỏ, nút hái, cá, gợi ý phím | Duy (`client/ui`) | AC-P1-01 (snapshot gather) |
| AC-P1-05 UI/HUD quan: kho khả dụng, đơn, kiên nhẫn, bếp, món trên tay, tiền, uy tín | Duy | AC-P1-03 (snapshot quan: `hand`, `stoves[].dish`, `reserved`) |
| AC-P1-06 UI chỉ đọc snapshot + gửi input, không đổi headless | Duy | — |
| AC-P1-07 test cho quan/scenario + ma trận truy vết + proof | Đức Anh (`qa`) | AC-P1-03 |
| AC-P1-08 README (cách chạy ≤ 3 lệnh, điều khiển, cách tính điểm, lệnh test) | Duy | tất cả lát |
| AC-P1-09 `TEAM.md` đủ handle, `team_size` khớp, ≥ 3 commit mỗi người | cả nhóm | — |

- **Mốc giờ (Scrum: Duy nhắc):** 0:20 rà lát vướng · 0:25 thử xuất file kho thật · 0:35 standup 2 phút (khớp snapshot UI ↔ sim) · 0:50 đóng băng tính năng, chỉ sửa lỗi · 0:50–0:58 `check_team.py` + full test + gom proof · tag `phase-1` chậm nhất 1:00.

- **Rủi ro:**
  1. Snapshot `quan` chưa chốt dạng `hand` / `stoves[].dish` / kho khả dụng → UI đoán sai. Giảm thiểu: UI xử lý cả hai dạng, hỏi Huy ở standup, ghi `docs/clarify.md`.
  2. Quan trễ → UI chưa thử được với luật thật. Giảm thiểu: thử bằng scenario dựng sẵn (khách, bếp), thử lại khi có bản quan.
  3. Máy Windows không có `python3` → test hộp đen lỗi. Giảm thiểu: đặt alias `python3` cục bộ; đề nghị Đạt cân nhắc `headless_cmd`.
  4. Handle trong `TEAM.md` lệch tài khoản commit (Đạt: `chipno39` / `datnxhe181631fpt`) → commit không được tính. Giảm thiểu: Đạt xác nhận và ghi đủ.
