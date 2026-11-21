# AGENTS.md — hướng dẫn chung cho mọi agent AI của nhóm

> Cập nhật file này qua các phase (lịch sử git phải cho thấy điều đó). Ngắn gọn, có lệnh chạy thật.

## Lệnh
- Test (Linux/macOS): `PYTHONPATH=tests:. python3 -m unittest discover -s tests -v`
- Test nhanh trên Windows (PowerShell): `$env:PYTHONPATH="tests;."; python -m unittest test_gather_rules test_python_starter_units test_team_check -v`
- Kiểm tra thành viên: `python3 tools/check_team.py` (Windows: `python tools/check_team.py`)
- Headless: `python3 -m chonoi.headless --mode gather|quan --seed 1 --ticks 600 --out out.jsonl`
- Chơi thử trên trình duyệt: `python3 -m chonoi.live --mode gather|quan --port 8765` (mở địa chỉ in ra; WASD, E, Space, R)

## Cấu trúc & quy ước
- (Starter Python là TÙY CHỌN; nhóm có thể dùng ngôn ngữ khác nếu giữ Test Contract.) Khung do giảng viên cấp: `chonoi/{headless,inputs,scenario,contract,rng,ids,jsonl,inventory,runner,live}.py` và `chonoi/web/`. Hạn chế sửa; nếu phải sửa thì báo cả nhóm và ghi lại lý do.
- Luật chơi của nhóm: `chonoi/sim/gather.py`, `chonoi/sim/quan.py` (tìm `TODO(nhóm)`).
- **Số liệu chỉ đọc từ `game.contract.json` / dữ liệu**, không hard-code trong luật.
- Mọi số ngẫu nhiên đi qua `Streams` (`chonoi/rng.py`); không dùng `random` toàn cục, không dùng đồng hồ hệ thống.
- Sắp danh sách thực thể bằng `ids.sort_by_id`; cấp id bằng `IdAllocator`.

## Nên tránh
- Không sửa `docs/contracts/`, `game.contract.json` (khóa contract) hoặc schema kho khi chưa báo cả nhóm (đổi hợp đồng ảnh hưởng mọi module).
- Không làm hỏng nhánh chính: trước khi đẩy, chạy test.
- Không bịa yêu cầu: chỗ mơ hồ thì ghi `docs/clarify.md` và hỏi PO.
- Không sửa test cho xanh khi luật sai; phải sửa luật hoặc ghi lý do đổi test trong commit.

## Quy tắc làm việc với agent
- Mỗi agent một việc rõ ràng (một lát). Cho agent đọc PRD/ticket đúng phase và hợp đồng kho trước.
- Agent làm xong phải chạy test và ghi kết quả vào mô tả commit hoặc `docs/proof/`; người đọc lại thay đổi trước khi đẩy.
- Sáng tạo thêm được khuyến khích nhưng phải tắt ở headless (xem README, mục "Tự do sáng tạo").

## Skills / hooks của nhóm
- `phase-release-check` (`.agents/skills/phase-release-check/SKILL.md`): Dùng trước khi gắn tag `phase-1`..`phase-4` để kiểm tra `check_team.py`, chạy test hộp đen + unit test, kiểm tra tích hợp kho `gather -> quan`, rà soát tài liệu DoD và đẩy tag đúng hạn.
- `qa-regression` (`.agents/skills/qa-regression/SKILL.md`): Dùng khi đổi contract, mô phỏng hoặc vòng ngày để kiểm hồi quy, so byte JSONL và ghi bằng chứng.

## Nhật ký tiến hóa AGENTS.md
- **Phase 1:** Chốt lệnh chạy trên cả Linux/macOS và Windows PowerShell, giữ nguyên `python3` trong `game.contract.json` cho CI Linux, bổ sung skill `phase-release-check`.
- **Phase 2:** Nâng cấp Test Contract v1.1 (`--mode day --days 1..5`, `Shop`, `Pause`, cá bơi/sinh, Cá Sấu M1/M2); tách test regression `test_gather_p2` & `test_day_pause_shop`; nhắc giữ bản sao list trong `snapshot()` tránh đột biến tham chiếu giữa các tick.
- **Phase 2 QA:** Bổ sung skill `qa-regression` cho kiểm chứng v1.1 và hồi quy Phase 1.
