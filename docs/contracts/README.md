# Hợp đồng tích hợp — Nhóm `random` (Test Contract v1.2)

> Cập nhật lên **Contract v1.2 (Phase 3 — Mùa Nước Nổi)** giữa 4 module (`sim/gather`, `sim/quan`, `client/ui`, `qa`).

---

## 1. Phân tích tác động & Thứ tự tích hợp đổi schema (v1.1 → v1.2)

**Quyết định đổi schema:** Chuyển toàn bộ kho (`inventory`, `gather.hold`, `quan.stock`, `shop.stock`) từ map đếm sang mảng cá thể `{id, kind, fresh}` với `IdAllocator` giữ xuyên pha/Ngày (`I1, I2, ...`) và dùng `fractions.Fraction` (độ chính xác tuyệt đối ở ngưỡng `30` và phép `floor`).

**Thứ tự tích hợp để `main` luôn chạy được:**
1. **Bước 1 (Adapter + Gather + Runner — nhánh `feat/p3-freshness-v12`):** Cập nhật `game.contract.json`, `inventory.py`, `scenario.py`, `sim/gather.py`, `runner.py`, `docs/contracts/`, `CHANGELOG.md`.
2. **Bước 2 (Song song trên nhánh từ Bước 1):** `sim/quan` chuyển sang kho cá thể + giữ chỗ theo ID + chốt `base_price`; `client/ui` đọc mảng cá thể & hiển thị độ tươi/hàng ươn; `qa` cập nhật fixture test cũ + bổ sung test ngưỡng 30, giữ lại khi ươn, giá theo tươi & từ chối kho đếm mã `2`.
3. **Bước 3 (Bật v1.2 trên `main`):** Gộp cả 2 đầu bàn giao (`gather` + `quan` + `ui` + `qa`), chạy smoke hai tiến trình & `day`, chạy toàn bộ regression rồi đẩy tag `phase-3`.

| Module | File cần đổi | Test bị ảnh hưởng | Người phụ trách |
|---|---|---|---|
| Adapter & Day | `game.contract.json`, `chonoi/inventory.py`, `chonoi/scenario.py`, `chonoi/runner.py` | `test_smoke_p1.py`, `test_day_pause_shop.py` | Đạt (`chipno39`) |
| Lặn & Hái | `chonoi/sim/gather.py` | `test_gather_rules.py`, `test_gather_p2.py`, thêm `test_gather_p3.py` | Đạt (`chipno39`) |
| Mở Quán | `chonoi/sim/quan.py`, `docs/clarify.md` | `test_quan_p2.py`, thêm `test_quan_p3.py` | Huy (`Zellsed`) |
| HUD / UI | `chonoi/web/index.html`, `chonoi/live.py`, `docs/plan/phase-3.md` | `test_live_day.py`, ảnh proof UI P3 | Duy (`vuduy21`) |
| QA & Proof | `tests/test_smoke_p1.py`, `tests/test_quan_scenario.py`, `tests/test_qa_p2.py`, `tests/test_qa_p3.py`, `docs/verification/phase-3.md` | Regression P1–P2 + test v1.2 mới | Đức Anh (`ldlda`) |

---

## 2. Schema file kho v1.2 (`gather` → `quan`)

Khớp TICKET-03 mục 1, dùng mẫu hợp lệ tại [`inventory.sample.json`](inventory.sample.json):

```json
{"items":[{"id":"I1","kind":"ca_linh","fresh":100},{"id":"I2","kind":"ca_loc","fresh":97.5}]}
```

* Chỉ có 1 khóa gốc `"items"`: mảng cá thể `{"id": str, "kind": str, "fresh": number ∈ [0, 100]}`. Kho rỗng là `{"items":[]}`.
* 6 `kind` hợp lệ: `ca_loc`, `ca_linh`, `ca_keo`, `bong_dien_dien`, `bong_sung`, `keo_neo`.
* Cấp `id` dạng `I1, I2, ...` tăng dần xuyên pha và xuyên Ngày (không tái sử dụng).
* Bên ghi xuất mảng sắp theo `id`, đủ độ chính xác float để giữ nhánh ở ngưỡng `30`, ghi nguyên tử (file tạm cùng thư mục → `os.replace`).
* Bên đọc (`contract_version: "1.2"`) **từ chối file kho đếm cũ**, sai schema, `kind` lạ, `id` trùng hoặc `fresh` ngoài `[0, 100]` (mã thoát `2`).

---

## 3. Quy tắc Độ tươi & Sự kiện mới (v1.2)

* `fresh = 100` lúc bắt/hái, hao từ bước sau: giỏ `-0.5/s` (`-1/120` mỗi tick), kho quán `-0.25/s` (`-1/240` mỗi tick, kể cả hàng giữ chỗ). Pause dừng hao; món chín & Shop không hao.
* Ươn khi `fresh < 30` (so trước làm tròn): phát `spoiled` (`{"item_id", "kind", "location": "hold"|"stock"}`) đúng 1 lần theo thứ tự `id`.
* `customers[].reserved`: mảng ID cá thể `["I1", ...]`. Giữ cá thể chưa ươn tươi nhất, hòa theo `id`. Nếu có cá thể giữ vừa ươn → nhả hết phần giữ của đơn, thử giữ lại đúng 1 lần (theo `order_tick` rồi `table_id`), thiếu → `unfulfillable`.
* `cook_started.data.items`: mảng cá thể sắp theo `(kind, id)`. `base_price = floor(giá niêm yết × trung bình fresh / 100)`.
* `monster_hit.data.lost` và `faint.data.lost`: mảng cá thể theo thứ tự bỏ LIFO.
