# Hợp đồng tích hợp — Nhóm `random` (Test Contract v1.1)

> Cập nhật lên **Contract v1.1 (Phase 2)** giữa 4 module (`sim/gather`, `sim/quan`, `client/ui`, `qa`). Khi cần thay đổi ở phase sau, báo cả nhóm và ghi lại lý do.

---

## 1. Schema file kho (`gather` → `quan`)

Khớp PRD-0 mục G & TICKET-02, dùng mẫu hợp lệ tại [`inventory.sample.json`](inventory.sample.json):

```json
{"items":{"bong_sung":2,"ca_loc":1}}
```

* Chỉ có 1 khóa gốc `"items"`: map `kind -> int >= 0`.
* 6 `kind` hợp lệ ở v1.1: `ca_loc`, `ca_linh`, `ca_keo`, `bong_dien_dien`, `bong_sung`, `keo_neo`.
* Bên ghi bỏ các khóa có giá trị `0`, sắp khóa theo thứ tự từ điển, ghi nguyên tử (file tạm cùng thư mục → `os.replace`). Kho rỗng là `{"items":{}}`.
* Ghi **đúng một lần** khi `gather` kết thúc (`gather_end`: `docked` / `time` / `fainted` — ngất thì ghi rỗng). Chạm `--ticks` trước khi kết thúc buổi sáng thì **không** tạo/ghi đè file kho.
* Bên đọc (`quan`) từ chối sai schema, `kind` lạ, số âm hoặc khai đồng thời `--inventory` và `scenario.quan.stock` (mã thoát `2`).

---

## 2. Giao diện giữa `sim/*` và `client/ui`

`client/ui` (`chonoi/live.py` + `chonoi/web/index.html`) chạy qua `chonoi.runner.Session` (cùng lớp sim với headless), **chỉ đọc snapshot và gửi input**, không tự tính luật:

* **Lệnh UI gửi vào (`LiveInputs.set`):**
  * `move`: `[x, d]` cho `gather` (`d > 0` là lặn xuống), `[x, z]` cho `quan` (`z > 0` là hướng bắc), mỗi thành phần trong `[-1, 1]`.
  * `interact`: boolean (cạnh lên `false -> true`; phím `E`).
  * `catch`: boolean (cạnh lên `false -> true`; phím `Space`, dùng ở `gather`).
* **Trạng thái UI đọc từ `Session.snapshot()`:**
  * **Chung:** `tick`, `sim_tick`, `mode`, `phase`, `phase_tick`, `state` (`playing`/`finished`), `time_left_ticks`, `money`, `earned`, `reputation`, `score`.
  * **`gather`:** `player` (`pos`, `vel`, `heading_deg`, `oxygen_ticks`, `oxygen_max_ticks`, `hp`, `hp_max`, `zero_oxy_ticks`, `catch_cd_ticks`, `at_surface`), `hold`, `hold_count`, `hold_capacity`, `nodes[]` (`id`, `pos`, `kind`, `ready`, `regrow_ticks`), `fish[]` (`id`, `pos`, `kind`, `heading_deg`).
  * **`quan`:** `player` (`pos`), `stock`, `hand`, `stoves[]` (`id`, `pos`, `state`, `dish`, `cook_ticks_left`, `ready_ticks`), `tables[]` (`id`, `pos`, `customer_id`), `customers[]` (`id`, `table_id`, `dish_id`, `order_tick`, `state`, `patience_ticks_left`, `eat_ticks_left`, `order_status`, `reserved`, `base_price`, `tip`).

---

## 3. Danh sách sự kiện (PRD-0 mục E)

### Buổi sáng (`gather` — phát bởi `chonoi/sim/gather.py`)

| Sự kiện | `data` | Ghi chú |
|---|---|---|
| `node_regrown` | `{"node_id"}` | Khi `regrow_ticks` từ 1 về 0 (theo thứ tự `id`) |
| `dive` | `{"pos"}` | Đổi từ mặt nước (`d <= surface_depth`) sang dưới nước |
| `surface` | `{"pos"}` | Đổi từ dưới nước sang mặt nước |
| `oxygen_empty` | `{"oxygen_ticks": 0}` | Khi `oxygen_ticks` từ dương xuống 0 |
| `choke` | `{"hp"}` | Khi `zero_oxy_ticks` đạt `choke_interval_ticks`, `-1` HP |
| `faint` | `{"cause": "choke", "lost": [...], "hp": 0}` | `lost` theo thứ tự bỏ LIFO (nhặt sau bỏ trước) |
| `gather` | `{"node_id", "kind", "amount"}` | Hái nút mặt nước thành công |
| `fish_caught` | `{"fish_id", "kind", "yield"}` | Bắt cá dưới nước thành công (đủ sức chứa cho cả `yield`) |
| `hold_full` | `{"action", "node_id" \| "fish_id", "required", "free"}` | `action` là `"gather"` hoặc `"catch"` |
| `fish_spawned` | `{"id", "kind", "pos"}` | Sinh cá theo lịch `phase_tick = 360*k` (v1.1) |
| `monster_hit` | `{"monster_id", "hp", "lost", "pos"}` | Cá Sấu chạm khi `d >= 10`, mất `floor(hold/2)` LIFO, `invuln = 90` (v1.1) |
| `gather_end` | `{"reason", "inventory": {"items": ...}}` | `reason`: `"docked"` / `"time"` / `"fainted"` |

### Vòng ngày (`day`), Pause & Shop (v1.1)

| Sự kiện | `data` | Ghi chú |
|---|---|---|
| `day_start`, `phase_start` | `{}` | Mở Ngày / chuyển pha (`gather` → `quan` → `shop`) |
| `day_plan` | `{"dishes", "ingredients"}` | Công bố kế hoạch D1–D5 ở đầu Ngày |
| `paused`, `resumed` | `{}` | Tạm dừng/tiếp tục (`pause` cạnh lên) |
| `bought` | `{"upgrade", "level", "price", "money"}` | Mua nâng cấp `oxygen` / `hp` trong Shop |
| `buy_failed` | `{"action", "reason"}` | `reason`: `funds` / `max_level` / `out_of_stock` / `unknown` |
| `shop_end` | `{"reason"}` | `reason`: `"done"` / `"time"` |

### Buổi tối (`quan` — phát bởi `chonoi/sim/quan.py`)

| Sự kiện | `data` | Ghi chú |
|---|---|---|
| `customer_arrived` | `{"order_id", "table_id", "dish_id"}` | Khách mới vào bàn trống `id` nhỏ nhất |
| `no_dish` | `{}` | Có bàn trống nhưng không đủ nguyên liệu khả dụng cho món nào |
| `cook_started` | `{"stove_id", "order_id", "dish_id", "items", "base_price"}` | `items` sắp theo `kind` |
| `dish_ready` | `{"stove_id", "order_id", "dish_id"}` | Bếp nấu xong, chuyển `ready` (`ready_ticks = 0`) |
| `dish_picked` | `{"stove_id", "order_id", "dish_id"}` | Nhấc món lên tay trống, bếp về `idle` |
| `served` | `{"order_id", "table_id", "dish_id", "patience_ticks_left", "base_price", "tip"}` | Phục vụ đúng `order_id` |
| `paid` | `{"order_id", "table_id", "base_price", "tip", "amount", "reason"}` | `reason`: `"finished_eating"` / `"closing"` |
| `customer_left` | `{"order_id", "table_id", "reason", "reputation"}` | `reason`: `"patience"` / `"closing"` |
| `quan_end` | `{"reason": "time", "money", "earned", "shift_earned", "reputation"}` | Kết thúc ca tối |
