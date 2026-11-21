---
name: phase-release-check
description: Checklist kiểm chứng tích hợp và gắn tag cuối mỗi phase (phase-1..phase-4, v1.0.0) cho Integrator nhóm random.
---

# Skill: Phase Release Check (Nhóm `random`)

Dùng skill này ở phút cuối của mỗi phase (trước hạn tag 10 phút) để đảm bảo nhánh `main` sạch, chạy được, đúng Test Contract và đủ bằng chứng trước khi đẩy tag `phase-n`.

## Các bước bắt buộc

1. **Đồng bộ nhánh chính:**
   ```bash
   git checkout main
   git pull origin main
   ```
2. **Kiểm tra danh sách thành viên & `team_size`:**
   ```bash
   python3 tools/check_team.py
   ```
   *(Trên Windows dùng `python tools/check_team.py`.)* Đảm bảo 4/4 thành viên đã có GitHub handle thật trong `TEAM.md` và khớp `game.contract.json`.
3. **Chạy toàn bộ unit test & smoke test hộp đen:**
   ```bash
   PYTHONPATH=tests:. python3 -m unittest discover -s tests -v
   ```
   Kiểm tra không có test nào fail và chế độ headless tất định (cùng seed ra JSONL giống từng byte).
4. **Kiểm tra tích hợp 2 tiến trình (`gather` → file kho → `quan`):**
   * Chạy `gather` với `--inventory-out` kết thúc bằng `docked`.
   * Chạy `quan` với `--inventory` đọc đúng file kho vừa tạo và kiểm tra `stock` ở snapshot tick 0.
5. **Rà soát tài liệu bắt buộc của phase:**
   * `docs/contracts/README.md` khớp bản chạy.
   * `docs/verification/phase-n.md` có link bằng chứng thật trong `docs/proof/phase-n/`.
   * `docs/ai-usage-log.md`, `docs/clarify.md` (và `docs/retro.md` ở Phase 2, 4; `docs/members/<handle>.md` ở Phase 4) đã cập nhật.
   * `README.md` có cách chạy ≤ 3 lệnh, điều khiển, cách tính điểm và lệnh test.
6. **Gắn tag và đẩy đúng hạn:**
   ```bash
   git tag -a phase-<n> -m "Release phase-<n>"
   git push origin phase-<n>
   ```
   *(Ở Phase 4, tạo thêm GitHub Release `v1.0.0`.)*
