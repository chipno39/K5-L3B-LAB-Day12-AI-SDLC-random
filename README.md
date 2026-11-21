# Quán Ăn Chợ Nổi — nhóm `random` · `v1.0.0`

Game quản lý quán ăn miền Tây (Day 12 · AI SDLC). Út Sen lặn bắt cá, hái bông trên sông Chín Khúc vào **buổi sáng** (`gather`), tối mở quán nấu và phục vụ khách trên nhà bè của Má Tư (`quan`), rồi ghé **cửa hàng** mua nâng cấp. Một ván gồm 1–5 Ngày theo kế hoạch D1–D5. Nguyên liệu có **độ tươi**: để lâu thì ươn, món nấu từ hàng kém tươi bán được ít tiền hơn.

Thành viên và vai trò: [TEAM.md](TEAM.md). Lịch sử thay đổi: [CHANGELOG.md](CHANGELOG.md). Đề bài gốc của lab: [docs/STARTER.md](docs/STARTER.md).

## Chạy từ clone sạch (macOS / Linux, 3 lệnh)

```bash
git clone https://github.com/chipno39/K5-L3B-LAB-Day12-AI-SDLC-random.git
cd K5-L3B-LAB-Day12-AI-SDLC-random
python3 -m chonoi.live --mode day --days 5      # mở địa chỉ in ra (mặc định cổng 8000) bằng trình duyệt
```

Có menu chính, màn giới thiệu Ngày / buổi tối, kết quả Ngày, cửa hàng nâng cấp và màn tổng kết. Thêm `--seed N` để đổi ván, `--port N` nếu cổng 8000 bận (`--port 0` = cổng ngẫu nhiên).

Chạy riêng từng buổi (hai tiến trình nối nhau qua file kho):

```bash
python3 -m chonoi.live --mode gather --inventory-out kho.json   # buổi sáng; kết thúc khi cập bến / hết giờ / ngất
python3 -m chonoi.live --mode quan --inventory kho.json         # buổi tối đọc đúng file kho đó (Ctrl+C lệnh trên trước)
```

## Yêu cầu môi trường

- **Python ≥ 3.8**, chỉ dùng thư viện chuẩn: không cần `pip install`, không có bước build (`build_cmd` = `true`). Nhóm kiểm trên Python 3.13.
- Lệnh `python3` có trong `PATH`, vì mọi lệnh trong [game.contract.json](game.contract.json) gọi `python3`.
- Trình duyệt hiện đại (Chrome / Edge / Firefox / Safari) để chơi. Headless, test, bench và soak không cần trình duyệt.

## Điều khiển

| Phím | Tác dụng |
|---|---|
| **W A S D** hoặc **mũi tên** | Bơi (sáng, `S` = lặn xuống) / đi (tối, `W` = lên phía bắc) |
| **E** | Sáng: cập bến (trong vùng bến) hoặc hái bông (ở mặt nước). Tối: nấu ở bếp, lấy món chín, phục vụ khách ở bàn |
| **Space** | Sáng: bắt đàn cá khi đang dưới nước |
| **Enter** (hoặc bấm chuột) | Qua màn chờ; ở cửa hàng: xong, sang Ngày mới |
| **1** / **2** (hoặc bấm vào ô) | Cửa hàng: mua nâng cấp bình oxy / thêm Máu |
| **P** hoặc **Esc** | Tạm dừng / tiếp tục (độ tươi cũng dừng hao) |
| **R** | Chơi lại |

Màn hình luôn hiện gợi ý phím gần nhất ("E: hái bông súng", "E: phục vụ"…), thông báo nhanh khi có sự kiện và cảnh báo bằng chữ kèm biểu tượng (thủy quái gần, oxy sắp hết, hàng ươn). HUD:
- **Sáng:** thời gian, thanh oxy, Máu, giỏ (từng cá thể kèm thanh độ tươi), danh sách cần lấy theo kế hoạch Ngày.
- **Tối:** thời gian, tiền, uy tín (5 sao), điểm, kho khả dụng (bỏ phần khách đang giữ, đánh dấu hàng ươn), món trên tay, 2 bếp, 4 bàn, khách kèm món gọi và thanh kiên nhẫn, thực đơn của Ngày.

## Luật chính & cách tính điểm

`điểm = earned + 100 × floor(uy tín)`

- `earned`: tổng tiền thu được cả lượt (nghìn đồng, số nguyên), gồm tiền món và tiền boa.
- **Giá món theo độ tươi**, chốt lúc bắt đầu nấu: `base_price = floor(giá niêm yết × độ tươi trung bình / 100)`.
- **Boa** = `round(base_price × 0.2)` nếu phục vụ khi kiên nhẫn còn ≥ 50%, kèm +0.2 uy tín.
- Uy tín bắt đầu từ 3.0, kẹp trong [0, 5]. Khách bỏ đi vì hết kiên nhẫn: −0.5. Có bàn trống mà kho không nấu được món nào (`no_dish`): −0.5. Hết ca: khách đang ăn trả tiền ngay, khách đang chờ ra về mà không trừ uy tín.
- **Độ tươi:** cá/bông mới có `fresh = 100`. Trong giỏ hao 0.5/giây, trong kho quán hao 0.25/giây. Dưới 30 là **ươn**: không được giữ chỗ, không được nấu.
- Buổi tối chỉ bán các món trong kế hoạch của Ngày đó (`day_plan`). Nguyên liệu dư sau cửa hàng **không** mang sang Ngày sau.

Mọi con số (oxy, giá món, thời gian nấu, độ tươi…) nằm trong [game.contract.json](game.contract.json); luật chỉ đọc số từ đó. Các điểm mơ hồ đã chốt: [docs/clarify.md](docs/clarify.md).

## Test, headless, bench, soak

```bash
PYTHONPATH=tests:. python3 -m unittest discover -s tests -v     # toàn bộ test hộp đen + unit test
python3 tools/check_team.py                                      # kiểm danh sách thành viên
```

Headless (dùng cho chấm tự động; cùng seed + cùng input thì ra file giống nhau từng byte):

```bash
python3 -m chonoi.headless --mode gather --seed 1 --ticks 600 --out out.jsonl --inventory-out kho.json
python3 -m chonoi.headless --mode quan   --seed 1 --ticks 600 --inventory kho.json --out out.jsonl
python3 -m chonoi.headless --mode day    --days 5 --seed 1 --ticks 120000 --out day.jsonl
```

Cờ khác: `--scenario file.json` (dựng sẵn trạng thái), `--inputs file.json` (chuỗi phím theo tick), `--snapshot-every N`. Sai tham số hoặc file đầu vào → mã thoát `2`, không ghi đầu ra.

Bench và soak (Contract v1.3; lệnh chuẩn nằm ở `bench_cmd` / `soak_cmd` trong [game.contract.json](game.contract.json)):

```bash
python3 -m chonoi.bench     # cảnh lặn 1280×720: làm nóng 3 s rồi đo 30 s, ghi bench.json
python3 -m chonoi.soak      # chạy lặp 10 Ngày (D1–D5 hai lượt), tất định, báo crashes=0
```

## Giới hạn đã biết

- **Windows:** máy thường chỉ có `python` (lệnh `python3` trỏ vào alias Microsoft Store), nên test hộp đen báo mã `9009`. Cách khắc phục: dùng WSL, hoặc tạo venv rồi chép `Scripts\python.exe` thành `python3.exe` và đưa thư mục đó vào `PATH`. Test nhanh trên PowerShell: `$env:PYTHONPATH="tests;."; python -m unittest discover -s tests`.
- **Windows có thể chặn cổng 8000** (`WinError 10013`): chạy `chonoi.live` với `--port 8765`.
- **Console Windows (cp1252)** có thể lỗi khi in tiếng Việt. Đặt `PYTHONIOENCODING=utf-8` trước khi chạy `chonoi.live` hoặc các script.
- Chưa có âm thanh; toàn bộ hình vẽ bằng mã trên `<canvas>` (xem [CREDITS.md](CREDITS.md)).
- Giao diện chỉ chạy trên trình duyệt qua máy chủ cục bộ `chonoi.live`; không có bản đóng gói desktop/mobile.
- Kết quả `bench.json` phụ thuộc máy chạy; chỉ so sánh được trên cùng một máy.
- Độ tươi tính bằng phân số chính xác (`fractions.Fraction`) nên `fresh` trong JSONL có thể là số thực dài (99.6666…); UI làm tròn khi hiển thị.
- Không làm phần Mở rộng (nhóm 4 người); chỉ hoàn thiện lõi Phase 1–4.

## Cấu trúc

- `chonoi/sim/gather.py`, `chonoi/sim/quan.py`: luật chơi (nhóm viết). `chonoi/runner.py`: vòng tick, vòng Ngày, cửa hàng, pause. Khung (`inputs`, `jsonl`, `rng`, `ids`…) do giảng viên cấp.
- `chonoi/live.py` + `chonoi/web/index.html`: cửa sổ chơi trên trình duyệt. Chỉ **đọc snapshot** (`GET /state`) và **gửi input** (`POST /input`), không chứa luật; hiệu ứng chỉ dùng đồng hồ trình duyệt nên không ảnh hưởng headless.
- `docs/contracts/`: hợp đồng tích hợp (file kho, sự kiện, giao diện sim–UI). `docs/proof/`, `docs/verification/`: bằng chứng và ma trận truy vết theo phase. `docs/members/`: phản tư cá nhân. `AGENTS.md`, `.agents/skills/`: hướng dẫn cho agent AI.

## Sáng tạo của nhóm

Không làm phần Mở rộng. Asset ngoài: không có, xem [CREDITS.md](CREDITS.md).
