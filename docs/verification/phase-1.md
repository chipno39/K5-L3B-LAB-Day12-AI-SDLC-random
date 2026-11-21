# Ma trận truy vết Phase 1

| AC | Cách kiểm chứng | Bằng chứng (link `docs/proof/phase-1/...`) | Kết quả (đạt / chưa đạt — ghi trung thực) |
|---|---|---|---|
| `tuning.quan.walk_speed`, `ramp_max_ticks` | Unit test: đo quãng đường trong 60 tick sau ramp; đối chiếu với contract. | [test_walk_reaches_contract_speed_and_respects_bounds](../../tests/test_quan_scenario.py); [kết quả chạy](../proof/phase-1/quan-qa-tests.txt) | Đạt — test mới pass. |
| `tuning.quan.bounds` | Unit test: đi sát biên phải, xác nhận vị trí bị chặn ở biên và vận tốc dừng. | [test_player_is_clamped_at_room_edge_and_velocity_stops](../../tests/test_quan_scenario.py); [kết quả chạy](../proof/phase-1/quan-qa-tests.txt) | Đạt — test mới pass. |
| `tuning.quan.duration_s` / kết thúc ca | Unit test với scenario còn 1 tick; xác nhận `quan_end` có lý do `time`. | [test_shift_end_emits_time_event_once_at_last_tick](../../tests/test_quan_scenario.py); [kết quả chạy](../proof/phase-1/quan-qa-tests.txt) | Đạt — test mới pass. |
| Scenario `quan`: schema, bounds, kho, khách/bàn, `time_left_ticks` | Unit test chấp nhận fixture hợp lệ; từ chối trường lạ, vị trí/vận tốc sai, kho sai, ID/bàn trùng và thời gian ngoài miền. | [QuanScenarioTests](../../tests/test_quan_scenario.py); [kết quả chạy](../proof/phase-1/quan-qa-tests.txt) | Đạt — 7 test mới pass. |

## Đánh giá ngắn
- Yêu cầu nào đạt / chưa đạt: Các kiểm tra scenario `quan`, đi bộ/chặn biên và kết thúc ca đã triển khai hiện tại đều đạt. Chưa kiểm chứng vòng đời khách, nấu món, phục vụ, thanh toán và uy tín vì các phần này còn TODO trong `chonoi/sim/quan.py`.
- Điều cần chỉnh cho phase sau: Bổ sung test khi luật khách và tương tác bếp/bàn được triển khai.

## Lệnh và kết quả
- `PYTHONPATH=tests:. python3 -m unittest tests.test_quan_scenario -v` — 10 test đạt.
- `PYTHONPATH=tests:. python3 -m unittest discover -s tests -v` — 54 test đạt.
