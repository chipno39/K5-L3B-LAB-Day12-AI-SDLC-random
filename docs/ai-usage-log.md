# Nhật ký dùng AI (theo phase và theo người)

| Phase | Người | Công cụ / model | Việc | Token / chi phí ước tính | Ghi chú (AI sai ở đâu?) |
|---|---|---|---|---|---|
| Phase 1 | chipno39 (Đạt) | Antigravity (Gemini) | Phân tích lab, kickoff `TEAM.md` & `game.contract.json`, chốt `docs/contracts/README.md`, code `chonoi/sim/gather.py` (Lát 1–2), viết `tests/test_gather_rules.py`, tạo skill `phase-release-check` | ~25k tokens | Lần chạy lệnh đầu dùng `&&` trên Windows PowerShell 5.1 bị lỗi cú pháp; cổng 8000 bị Windows chặn (`WinError 10013`) phải đổi sang 8765; cần yêu cầu AI chờ PRD chi tiết mục E/F thay vì tự đoán payload sự kiện. |
