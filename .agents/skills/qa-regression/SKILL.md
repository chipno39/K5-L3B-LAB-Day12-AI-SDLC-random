---
name: qa-regression
description: Kiểm hồi quy và tính tất định của Chợ Nổi khi đổi contract, luật mô phỏng hoặc vòng ngày.
---

1. Đọc `game.contract.json`, `docs/contracts/README.md` và tiêu chí phase. Với phase mới, giữ hành vi còn hiệu lực của phase trước; ghi lý do nếu contract đã thay đổi.
2. Ưu tiên kiểm tra qua `headless_cmd` bằng `tests/helpers.py`. Dùng số liệu trong contract. Với fixture lỗi, kiểm mã thoát và file đầu ra; cô lập từng nguyên nhân lỗi.
3. Với tính tất định, chạy hai lần cùng seed, scenario và inputs, qua các bước hoặc chuyển pha cần kiểm tra. So byte JSONL và kiểm các sự kiện chính để tránh hai đầu ra rỗng vẫn được tính đạt.
4. Từ gốc repo, với Phase 2 chạy `PYTHONPATH=tests:. python3 -m unittest test_qa_p2 test_day_pause_shop -v`, rồi chạy `PYTHONPATH=tests:. python3 -m unittest discover -s tests -v`.
5. Lưu lệnh và kết quả thật vào `docs/proof/phase-n/`. Trong `docs/verification/phase-n.md`, liên kết bằng chứng và ghi phạm vi, kết quả, phần chưa kiểm hoặc đang chờ triển khai.
