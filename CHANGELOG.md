# Changelog

## [v1.0.0 — Phase 4 — Contract v1.3] — Phát hành chính thức
* Nâng `game.contract.json` lên `contract_version: "1.3"`, bổ sung `bench_cmd` (`python3 -m chonoi.bench`) và `soak_cmd` (`python3 -m chonoi.soak`).
* Thêm `chonoi/bench.py` (cảnh lặn 1280×720, làm nóng 3s + đo 30s, xuất `bench.json` đủ 5 trường `avg_fps`, `p1_low_fps`, `frames`, `measured_s`, `load_ms`).
* Thêm `chonoi/soak.py` (chạy 10 Ngày liên tiếp bằng bot tất định, lặp kế hoạch D1–D5 ở Ngày 6–10, giữ tiến trình xuyên suốt, `crashes = 0`).
* Hoàn thiện cảnh báo dễ nhận biết (thủy quái gần, oxy sắp hết, khách sắp giận) kèm chế độ Tương phản cao (High Contrast), tài liệu đóng gói, retro tổng kết và phản tư cá nhân.

## [Phase 3 — Contract v1.2] — Mùa Nước Nổi (Breaking Change)

### Breaking Changes
* **Đổi schema file kho (`gather` → `quan`):** Chuyển từ kho đếm theo loại `{"items":{"ca_loc":1}}` sang **kho cá thể có độ tươi**:
  ```json
  {"items":[{"id":"I1","kind":"ca_linh","fresh":100},{"id":"I2","kind":"ca_loc","fresh":97.5}]}
  ```
  Kho rỗng là `{"items":[]}`. File kho đếm kiểu cũ (v1.0/v1.1) nay bị từ chối với **mã thoát `2`**.
* **Đổi schema Scenario & JSONL:**
  * `gather.hold`, `quan.stock` (và `stock` ở Shop) chuyển sang mảng cá thể `{id, kind, fresh}`.
  * `customers[].reserved` chuyển từ map số lượng sang **mảng ID cá thể** `["I1", ...]`.
  * `cook_started.data.items` chuyển sang mảng cá thể sắp theo `(kind, id)`.
  * `monster_hit.data.lost` và `faint.data.lost` chuyển sang mảng cá thể theo thứ tự bỏ LIFO.
* **Luật mới:**
  * Thêm `tuning.freshness` (`initial: 100`, `gather_decay_per_s: 0.5`, `quan_decay_per_s: 0.25`, `spoiled_below: 30`).
  * Cá thể mới có `fresh = 100`, hao từ bước sau; vượt từ `>= 30` xuống `< 30` phát sự kiện `spoiled` đúng 1 lần theo thứ tự `id`.
  * Khi bắt đầu nấu: `base_price = floor(giá niêm yết × trung bình fresh / 100)`; boa (nếu đạt điều kiện) tính trên `base_price` đã chốt.

### Cách cập nhật Fixture & Test từ v1.1 → v1.2
1. Đổi `"hold": ["ca_loc", "bong_sung"]` thành `"hold": [{"id":"I1","kind":"ca_loc","fresh":100},{"id":"I2","kind":"bong_sung","fresh":100}]`.
2. Đổi `"stock": {"ca_loc": 1}` thành `"stock": [{"id":"I1","kind":"ca_loc","fresh":100}]`.
3. Đổi `"reserved": {"ca_loc": 1}` thành `"reserved": ["I1"]`.
4. Kiểm chứng đọc/ghi kho bằng `docs/contracts/inventory.sample.json` mới; kiểm kho đếm cũ trả mã `2`.

## [Phase 2 — Contract v1.1] — Một ngày ở chợ nổi
* Chốt số liệu chuẩn, 6 nguyên liệu (`+ ca_keo, keo_neo`), 6 món, 2 bếp `B1–B2`, 4 bàn `T1–T4`.
* Thêm cá bơi/phản xạ/sinh theo lịch, Cá Sấu Năm Chèo `M1`/`M2`, chế độ `--mode day --days 1..5`, Shop (`oxygen`/`hp`), Pause/Resume.

## [Phase 1 — Contract v1.0] — Lõi Quán Ăn Chợ Nổi
* Hoàn thiện `gather` (Lát 1–2), `quan` (Lát 3–4), bàn giao kho hai tiến trình, HUD chơi trực tiếp và bộ test tự động.
