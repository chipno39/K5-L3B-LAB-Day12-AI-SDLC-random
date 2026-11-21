# Retro nhóm

## Phase 2 (nhanh)
- Điều tốt: Chia ranh giới file theo 4 module rõ ràng nên gộp nhánh Phase 2 không phát sinh xung đột code; nâng cấp Contract v1.1 và `docs/contracts/README.md` sớm giúp cả 4 người chạy song song nhanh; cả 4/4 thành viên đều vượt mốc ≥ 3 commit và hoàn thiện đủ 2 skill (`phase-release-check`, `qa-regression`).
- Điều tệ: `GatherSim.snapshot()` ban đầu trả tham chiếu list trực tiếp làm snapshot tick trước bị đột biến ở test recoil; `runner._start_quan` ban đầu tự lọc `menu` riêng trước khi đồng bộ tham số `dishes` với `QuanSim`; môi trường Windows dính alias `python3` khi chạy test hộp đen.
- 1 hành động cho Phase 3: Trước khi code Phase 3, chốt chữ ký giao diện `runner` ↔ `sim/*` ↔ `live/ui` trong 3 phút đầu và chạy đủ cả test unit + headless + live trước mốc đóng băng 10 phút (Người nhận: Đạt `chipno39` & Đức Anh `ldlda`).

## Phase 4 (cuối)
- Rà lại hành động Phase 2: đã làm chưa? vì sao?
- Điều tốt / điều tệ:
- Số liệu: số commit theo người, cách đọc code của nhau, token theo người:
- Một lần AI sai và cách nhóm phát hiện:
- Nếu làm lại, đổi gì:
