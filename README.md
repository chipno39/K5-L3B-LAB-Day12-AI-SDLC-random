# Quán Ăn Chợ Nổi — nhóm `random`

Game quản lý quán ăn miền Tây (Day 12 · AI SDLC). Út Sen lặn bắt cá, hái bông trên sông Chín Khúc vào **buổi sáng** (`gather`), tối mở quán nấu và phục vụ khách trên nhà bè của Má Tư (`quan`). Những gì mang về quyết định quán bán được món nào.

Thành viên và vai trò: xem [TEAM.md](TEAM.md). Đề bài gốc của lab: [docs/STARTER.md](docs/STARTER.md).

## Chạy từ clone sạch (macOS / Linux, Python 3, không cần cài thêm)

```bash
git clone https://github.com/chipno39/K5-L3B-LAB-Day12-AI-SDLC-random.git && cd K5-L3B-LAB-Day12-AI-SDLC-random
python3 -m chonoi.live --mode gather --inventory-out kho.json   # buổi sáng: mở địa chỉ in ra bằng trình duyệt
python3 -m chonoi.live --mode quan --inventory kho.json         # buổi tối: chạy sau khi buổi sáng kết thúc (Ctrl+C lệnh trên)
```

**Chơi trọn vòng ngày (khuyến nghị, Phase 2):** sáng → tối → cửa hàng, lặp 1–5 ngày, chỉ cần một lệnh:

```bash
python3 -m chonoi.live --mode day --days 5
```

Có menu chính, màn giới thiệu ngày / buổi tối, kết quả ngày, cửa hàng nâng cấp (oxy, Máu) và tổng kết. Các màn chờ chỉ là lớp giao diện: sim đứng yên trong lúc chúng hiện, nên luật và kết quả headless không đổi.

Buổi sáng ghi `kho.json` khi kết thúc (cập bến, hết giờ hoặc ngất → kho rỗng). Buổi tối đọc đúng file đó làm kho nguyên liệu. Thêm `--seed N` hoặc `--port N` nếu cần. Chạy riêng một buổi: bỏ cờ kho (quán sẽ có kho rỗng).

## Điều khiển

| Phím | Tác dụng |
|---|---|
| **W A S D** hoặc **mũi tên** | Bơi (sáng, `S` = lặn xuống) / đi (tối, `W` = lên phía bắc) |
| **E** | Sáng: cập bến (trong vùng bến) hoặc hái bông (ở mặt nước). Tối: nấu ở bếp, lấy món chín, phục vụ khách ở bàn |
| **Space** | Sáng: bắt đàn cá khi đang dưới nước |
| **Enter** (hoặc bấm chuột) | Qua màn chờ; ở cửa hàng: xong, sang ngày mới |
| **1** / **2** (hoặc bấm vào ô) | Cửa hàng: mua nâng cấp bình oxy / thêm Máu |
| **P** hoặc **Esc** | Tạm dừng / tiếp tục |
| **R** | Chơi lại |

Màn hình luôn hiện gợi ý phím gần nhất ("E: hái bông súng", "E: phục vụ"…), thông báo nhanh khi có sự kiện, và HUD:
- **Sáng:** thời gian, thanh oxy, Máu, giỏ (ô theo thứ tự nhặt).
- **Tối:** thời gian, tiền, uy tín (5 sao), điểm, kho, món trên tay, bếp (đang nấu / chín), khách cùng món gọi và thanh kiên nhẫn, danh sách đơn, thực đơn.

## Cách tính điểm

`điểm = earned + 100 × floor(uy tín)`

- `earned`: tổng tiền thu được cả lượt (nghìn đồng, số nguyên): tiền món + boa.
- Uy tín bắt đầu từ 3.0, kẹp trong [0, 5]. Khách bỏ đi vì hết kiên nhẫn: −0.5. Boa dương: +0.2.
- Boa = `floor(tiền món × 0.2)` nếu phục vụ khi kiên nhẫn còn ≥ 50%.

Các số khác (oxy, giá món, thời gian nấu…) nằm trong [game.contract.json](game.contract.json); luật chỉ đọc số từ đó.

## Test

```bash
PYTHONPATH=tests:. python3 -m unittest discover -s tests -v     # toàn bộ test (1 lệnh)
python3 tools/check_team.py                                      # kiểm danh sách thành viên
```

Headless (dùng cho chấm tự động, cùng seed → cùng từng byte):

```bash
python3 -m chonoi.headless --mode gather --seed 1 --ticks 600 --out out.jsonl --inventory-out kho.json
python3 -m chonoi.headless --mode quan --seed 1 --ticks 600 --inventory kho.json --out out.jsonl
```

> Windows: máy chỉ có `python` (không có `python3`) thì test hộp đen không chạy được. Tạo alias `python3` trỏ tới `python`, hoặc dùng WSL.

## Cấu trúc

- `chonoi/sim/gather.py`, `chonoi/sim/quan.py`: luật chơi (nhóm viết). Khung (`runner`, `inputs`, `jsonl`…) do giảng viên cấp.
- `chonoi/live.py` + `chonoi/web/index.html`: cửa sổ chơi trên trình duyệt. Chỉ **đọc snapshot** (`GET /state`) và **gửi input** (`POST /input`), không chứa luật; hiệu ứng chỉ dùng đồng hồ trình duyệt nên không ảnh hưởng headless.
- `docs/contracts/`: hợp đồng tích hợp (file kho, sự kiện, giao diện sim–UI). `docs/proof/`, `docs/verification/`: bằng chứng và ma trận truy vết. `AGENTS.md`, `.agents/skills/`: hướng dẫn cho agent AI.

## Sáng tạo của nhóm

Chưa có (Phase 1 chỉ làm lõi). Ghi ở đây kèm bằng chứng lõi vẫn đúng khi thêm, và liệt kê asset ngoài trong [CREDITS.md](CREDITS.md).
