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

## Chơi thử với luật `quan` thật (nhánh `feat/p1-quan` của Huy, commit e4853a8)

`play_quan.py` điều khiển `chonoi.live` qua `POST /input` (đi tới bếp, E nấu, E lấy món, đi tới bàn, E phục vụ) và chụp bằng Edge ở từng giai đoạn. Kho đầu vào `{"items":{"ca_loc":1}}`.

| Ảnh | Giai đoạn |
|---|---|
| `quan-live-1-khach-cho.png` | khách C1 đến (tick 120), món gọi + thanh kiên nhẫn đầy |
| `quan-live-2-dang-nau.png` | bếp B1 đang nấu, kho đã bị trừ |
| `quan-live-3-cam-mon.png` | món trên tay (`hand` là chuỗi `dish_id`), bếp về trống |
| `quan-live-4-khach-an.png` | phục vụ xong, thanh ăn, uy tín 3.2, "boa 12k" |

Kết quả in ra: sau khi khách ăn xong `money = 72` (60 + boa 12), `reputation = 3.2`, `score = 372` (trùng ví dụ dòng `end` trong PRD-0).

UI nhận cả hai dạng `hand` (chuỗi `dish_id` hiện tại / payload `{order_id,dish_id,base_price}` theo PRD) và cả hai bộ giá trị `order_status`; kho hiển thị là kho khả dụng = `stock` trừ tổng `customers[].reserved`.

Giới hạn trung thực:
- Chơi qua HTTP `/input` do script gửi, chưa phải gõ phím tay trên trình duyệt thật.
- Ở `quan-end.png` khách vẫn ngồi sau khi hết ca vì luật đóng ca của `quan` chưa làm (việc của sim; đã báo Huy).
- Chưa kiểm `gather` với luật thật qua trình duyệt; mới kiểm bằng scenario.
