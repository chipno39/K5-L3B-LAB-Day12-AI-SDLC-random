# Bằng chứng UI Phase 1 (TV 3 — Duy)

Chụp bằng Microsoft Edge headless (1200×720) từ `python -m chonoi.live`, trên scenario dựng sẵn (không phải một lượt chơi hoàn chỉnh).

| Ảnh | Lệnh / tình huống | Cho thấy |
|---|---|---|
| `gather-hud.png` | `--mode gather --scenario` (player [28,0], giỏ 3 món) | Giờ, oxy, Máu, giỏ 3/12, nút hái, đàn cá, bến, gợi ý "E: hái bông điên điển" |
| `gather-end.png` | cùng scenario, `time_left_ticks: 2` | Màn kết thúc: lý do và kho mang về quán |
| `quan-hud.png` | `--mode quan --inventory kho.json --scenario` (1 khách, bếp B1 đang nấu) | Kho, bếp đang nấu có đếm giây, khách + thanh kiên nhẫn, đơn, thực đơn, uy tín, điểm |
| `quan-end.png` | cùng, `time_left_ticks: 2` | Màn kết thúc ca tối: thu nhập, uy tín, điểm |

Kiểm tra kèm theo:
- Chạy script của `index.html` trong Node với canvas giả, nạp snapshot thật của hai chế độ ở nhiều kích thước màn hình và cả snapshot thiếu hầu hết trường → không có lỗi runtime.
- `unittest`: 44/44 xanh (máy Windows cần alias `python3`).

Giới hạn trung thực:
- Chưa kiểm UI với luật `quan` thật của Huy (khách tự đến, bếp, bưng, trả tiền): chỉ thử bằng scenario. Hiển thị "kho" ở quán hiện là `stock` nguyên dạng, chưa trừ phần giữ chỗ (chờ chốt dạng snapshot).
- Ở `quan-end.png` khách vẫn ngồi sau khi hết ca vì luật đóng ca của `quan` chưa làm; đó là việc của sim, không phải UI.
- Chưa thử bằng tay qua phím (bơi, hái, nấu, phục vụ) trên trình duyệt thật.
