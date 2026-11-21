# Nhật ký dùng AI (theo phase và theo người)

| Phase | Người | Công cụ / model | Việc | Token / chi phí ước tính | Ghi chú (AI sai ở đâu?) |
|---|---|---|---|---|---|
| Phase 1 | chipno39 (Đạt) | Antigravity (Gemini) | Phân tích lab, kickoff `TEAM.md` & `game.contract.json`, chốt `docs/contracts/README.md`, code `chonoi/sim/gather.py` (Lát 1–2), viết `tests/test_gather_rules.py`, tạo skill `phase-release-check` | ~25k tokens | Lần chạy lệnh đầu dùng `&&` trên Windows PowerShell 5.1 bị lỗi cú pháp; cổng 8000 bị Windows chặn (`WinError 10013`) phải đổi sang 8765; cần yêu cầu AI chờ PRD chi tiết mục E/F thay vì tự đoán payload sự kiện. |
| Phase 1 | Zellsed (Huy) | Antigravity (Gemini Flash) | Viết tài liệu làm rõ `docs/clarify.md` và lập trình logic Mở Quán `chonoi/sim/quan.py` (Lát 3 & 4) | ~15k tokens | AI ban đầu dùng tên trường `customer_id` trong sự kiện thay vì `order_id` như hợp đồng kho `docs/contracts/README.md`; tôi đã đối soát lại hợp đồng tích hợp và chuẩn hóa theo đúng Test Contract v1.0. |
