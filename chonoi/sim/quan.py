"""Buổi tối — Mở Quán. KHUNG & LUẬT CHƠI (Test Contract v1.2).

Khớp hợp đồng tích hợp tại docs/contracts/README.md và PRD-0 mục E, F.
v1.1: số bếp/bàn/món đọc hoàn toàn từ `tuning` (B1-B2, T1-T4, 6 món); khi chạy `day`,
thực đơn buổi tối chỉ gồm các món trong `day_plan` của Ngày đó (tham số `dishes`).
v1.2 (Độ tươi & Kho cá thể): `stock` là mảng cá thể {"id","kind","fresh"}; hao tươi mỗi tick,
cá thể tụt dưới ngưỡng phát `spoiled`; `reserved` là mảng id (chọn tươi nhất, hòa thì id nhỏ);
khi cá thể đang giữ bị ươn -> nhả và thử giữ lại đúng 1 lần; giá chốt lúc nấu
`base_price = floor(price * avg_fresh / 100)`.
"""

import math
from fractions import Fraction

from ..errors import BadInput
from ..ids import id_key, sort_by_id
from ..inventory import fresh_frac, fresh_num, validate_items
from .ramp import ramp_velocity

TICK = 60.0


def _fresh_cfg(tuning):
    """Mọi số độ tươi của `quan` đọc từ contract tại MỘT chỗ (không hard-code trong luật).
    Dùng Fraction như gather/inventory để so ngưỡng 30 và floor giá chính xác tuyệt đối."""
    f = tuning["freshness"]
    return {
        "decay_per_tick": fresh_frac(f["quan_decay_per_s"]) / int(tuning.get("tick_hz", 60)),
        "spoiled_below": fresh_frac(f["spoiled_below"]),
    }


def _item_sort_key(it):
    """`cook_started.items`: sắp theo kind rồi id."""
    return (it["kind"], id_key(it["id"]))


def _freshest_key(it):
    """Chọn cá thể tươi nhất; hòa độ tươi thì id nhỏ hơn."""
    return (-it["fresh"], id_key(it["id"]))


def normalize_stock(raw):
    """Kho cá thể (mảng, hoặc {"items": [...]}) -> mảng {"id","kind","fresh": Fraction} sắp theo id.
    Kiểm schema bằng `inventory.validate_items` (kho đếm cũ -> BadInput, mã 2)."""
    if isinstance(raw, dict) and set(raw) == {"items"}:
        raw = raw["items"]
    items = validate_items(raw)
    return sort_by_id([{"id": it["id"], "kind": it["kind"], "fresh": fresh_frac(it["fresh"])} for it in items])


def _out_item(it):
    return {"id": it["id"], "kind": it["kind"], "fresh": fresh_num(it["fresh"])}


def filter_menu(menu, dishes):
    """Lọc thực đơn theo danh sách món của kế hoạch ngày (`day_plan[].dishes`).

    `dishes=None` hoặc rỗng -> giữ nguyên cả thực đơn (chế độ `quan` đơn lẻ).
    Món không có trong `tuning.menu` -> BadInput (mã thoát 2).
    """
    if not dishes:
        return dict(menu)
    unknown = sorted(d for d in dishes if d not in menu)
    if unknown:
        raise BadInput(f"day_plan có món không có trong menu: {', '.join(unknown)}")
    wanted = set(dishes)
    return {k: v for k, v in menu.items() if k in wanted}


class QuanSim:
    mode = "quan"
    phase = "quan"

    def __init__(self, tuning, scenario, streams, ids, inventory=None, dishes=None):
        t = tuning["quan"]
        self.t = t
        self.menu = filter_menu(tuning["menu"], dishes)
        self.fresh = _fresh_cfg(tuning)
        self.rng = streams
        self.ids = ids

        p = scenario.get("player", {})
        self.pos = list(p.get("pos", t["start_pos"]))
        self.vel = [float(c) for c in p.get("vel", [0.0, 0.0])]
        self._tgt = None
        self._ramp_left = 0

        # Kho cá thể: --inventory HOẶC scenario.stock
        self.stock = normalize_stock(inventory if inventory is not None else scenario.get("stock", []))
        self.hand = scenario.get("hand")
        self.hand_order_id = scenario.get("hand_order_id")

        self.duration_ticks = int(round(t["duration_s"] * TICK))
        self.time_left_ticks = scenario.get("time_left_ticks", self.duration_ticks)
        self.sim_tick = self.duration_ticks - self.time_left_ticks
        self.reputation = float(scenario.get("reputation", t["reputation_initial"]))

        self.stoves = [
            dict(
                s,
                state=s.get("state", "idle"),
                dish=s.get("dish"),
                order_id=s.get("order_id"),
                cook_ticks_left=s.get("cook_ticks_left", 0),
                ready_ticks=s.get("ready_ticks", 0),
            )
            for s in self._merge(t["stoves"], scenario.get("stoves", []))
        ]
        self.tables = self._merge(t["tables"], scenario.get("tables", []))

        # Khách dựng sẵn từ scenario & suy ra giữ chỗ (reserved)
        self.customers = []
        for c in scenario.get("customers", []):
            item = dict(c)
            dish = item.get("dish_id") or item.get("dish")
            if dish:
                item["dish_id"] = dish
            item.setdefault("order_tick", 0)
            item.setdefault("state", "waiting")
            item.setdefault("order_status", "waiting")
            item.setdefault("patience_ticks_left", int(round(t["patience_s"] * TICK)))
            item.setdefault("eat_ticks_left", int(round(t["eat_s"] * TICK)))
            item.setdefault("base_price", self.menu.get(dish, {}).get("price", 0) if dish else 0)
            item.setdefault("tip", 0)

            item["reserved"] = list(item.get("reserved", []))
            self.customers.append(item)
            ids.reserve(item["id"])

        # Khách chờ dựng sẵn chưa khai reserved -> giữ chỗ tươi nhất theo thứ tự id khách
        for c in sort_by_id(self.customers):
            if c["state"] == "waiting" and not c["reserved"] and c.get("dish_id") in self.menu:
                picked = self._reserve_for(c["dish_id"])
                if picked is None:
                    c["order_status"] = "unfulfillable"
                else:
                    c["reserved"] = picked

        self.random_customers = scenario.get("random_customers", True)

        self.money = 0
        self.earned = 0
        self.shift_earned = 0
        self.done = False
        self.reason = None

    @staticmethod
    def _merge(defaults, updates):
        by_id = {d["id"]: dict(d) for d in defaults}
        for u in updates:
            if u["id"] not in by_id:
                raise BadInput(f"id bếp/bàn không tồn tại: {u['id']}")
            by_id[u["id"]].update(u)
        return sort_by_id(list(by_id.values()))

    def _add_reputation(self, delta):
        self.reputation = round(
            max(self.t["reputation_min"], min(self.t["reputation_max"], self.reputation + delta)), 3
        )

    def _is_spoiled(self, it):
        return it["fresh"] < self.fresh["spoiled_below"]

    def _reserved_ids(self):
        return {iid for c in self.customers for iid in c.get("reserved", [])}

    def _available_items(self):
        """Cá thể khả dụng: còn trong kho, chưa ươn, chưa bị khách nào giữ."""
        taken = self._reserved_ids()
        return [it for it in self.stock if it["id"] not in taken and not self._is_spoiled(it)]

    def _reserve_for(self, dish):
        """Chọn cá thể tươi nhất (hòa -> id nhỏ) cho từng kind của công thức. Thiếu -> None."""
        avail = self._available_items()
        picked = []
        for kind in sorted(self.menu[dish]["recipe"]):
            qty = self.menu[dish]["recipe"][kind]
            pool = sorted((it for it in avail if it["kind"] == kind), key=_freshest_key)
            if len(pool) < qty:
                return None
            picked.extend(it["id"] for it in pool[:qty])
        return sorted(picked, key=id_key)

    def _decay(self, events):
        """Hao tươi mỗi tick (kể cả hàng giữ chỗ); cá thể vừa tụt dưới ngưỡng -> `spoiled`
        theo thứ tự id; rồi đơn đang giữ cá thể đó nhả hết và thử giữ lại đúng 1 lần,
        theo thứ tự (order_tick, table_id)."""
        d, thr = self.fresh["decay_per_tick"], self.fresh["spoiled_below"]
        newly = []
        for it in self.stock:  # stock luôn sắp theo id
            before = it["fresh"]
            it["fresh"] = max(Fraction(0), before - d)
            if before >= thr > it["fresh"]:
                newly.append(it["id"])
                events.append(("spoiled", {"item_id": it["id"], "kind": it["kind"], "location": "stock"}))
        if not newly:
            return
        bad = set(newly)
        hit = [c for c in self.customers
               if c["state"] == "waiting" and bad.intersection(c.get("reserved", []))]
        for c in hit:  # nhả hết trước, rồi mới giữ lại
            c["reserved"] = []
        for c in sorted(hit, key=lambda c: (c.get("order_tick", 0), id_key(c["table_id"]))):
            picked = self._reserve_for(c["dish_id"]) if c.get("dish_id") in self.menu else None
            if picked is None:
                c["order_status"] = "unfulfillable"
            else:
                c["reserved"] = picked

    def _pick_dish_to_cook(self):
        """Khách chờ (id nhỏ nhất) có đủ cá thể đã giữ và chưa được nấu/cầm trên tay."""
        in_progress_orders = set()
        if self.hand_order_id:
            in_progress_orders.add(self.hand_order_id)
        for st in self.stoves:
            if st.get("order_id"):
                in_progress_orders.add(st["order_id"])

        stock_ids = {it["id"] for it in self.stock}
        for cust in sort_by_id(self.customers):
            if cust.get("state") != "waiting" or cust["id"] in in_progress_orders:
                continue
            if cust.get("order_status") == "unfulfillable":
                continue
            dish = cust.get("dish_id")
            if not dish or dish not in self.menu:
                continue
            need = sum(self.menu[dish]["recipe"].values())
            res = cust.get("reserved", [])
            if len(res) == need and all(i in stock_ids for i in res):
                return dish, cust
        return None

    def snapshot(self) -> dict:
        occupied = {c["table_id"]: c["id"] for c in self.customers}
        snap_customers = []
        for c in sort_by_id(self.customers):
            dish = c.get("dish_id")
            base_p = c.get("base_price", self.menu.get(dish, {}).get("price", 0) if dish else 0)
            snap_customers.append({
                "id": c["id"],
                "table_id": c["table_id"],
                "dish_id": dish,
                "order_tick": c.get("order_tick", 0),
                "state": c["state"],
                "patience_ticks_left": c.get("patience_ticks_left", 0),
                "eat_ticks_left": c.get("eat_ticks_left", 0),
                "order_status": c.get("order_status", c["state"]),
                "reserved": sorted(c.get("reserved", []), key=id_key),
                "base_price": base_p,
                "tip": c.get("tip", 0),
            })

        return {
            "player": {"pos": self.pos},
            "stock": [_out_item(it) for it in self.stock],
            "hand": self.hand,
            "stoves": [
                {k: s.get(k) for k in ("id", "pos", "state", "dish", "cook_ticks_left", "ready_ticks")}
                for s in sort_by_id(self.stoves)
            ],
            "tables": [
                {"id": tb["id"], "pos": tb["pos"], "customer_id": occupied.get(tb["id"])}
                for tb in sort_by_id(self.tables)
            ],
            "customers": snap_customers,
        }

    def step(self, inp):
        events = []
        self.time_left_ticks = max(0, self.time_left_ticks - 1)
        self.sim_tick += 1

        # 0. Hao tươi kho cá thể (v1.2) + nhả/giữ lại khi ươn
        self._decay(events)

        # 1. Cập nhật bếp nấu: giảm tick nấu, bếp chín phát dish_ready
        for st in sort_by_id(self.stoves):
            if st["state"] == "cooking":
                st["cook_ticks_left"] = max(0, st.get("cook_ticks_left", 0) - 1)
                if st["cook_ticks_left"] == 0:
                    st["state"] = "ready"
                    st["ready_ticks"] = 0
                    events.append((
                        "dish_ready",
                        {
                            "stove_id": st["id"],
                            "order_id": st.get("order_id"),
                            "dish_id": st["dish"],
                            "dish": st["dish"],
                        },
                    ))
            elif st["state"] == "ready":
                st["ready_ticks"] = st.get("ready_ticks", 0) + 1

        # 2. Cập nhật khách: kiên nhẫn & ăn xong trả tiền
        remaining_customers = []
        for c in sort_by_id(self.customers):
            dish = c.get("dish_id")
            price = c.get("base_price", self.menu.get(dish, {}).get("price", 0) if dish else 0)

            if c["state"] == "waiting":
                c["patience_ticks_left"] = max(0, c.get("patience_ticks_left", 0) - 1)
                if c["patience_ticks_left"] == 0:
                    self._add_reputation(self.t["left_reputation_delta"])
                    events.append((
                        "customer_left",
                        {
                            "order_id": c["id"],
                            "customer_id": c["id"],
                            "table_id": c["table_id"],
                            "reason": "patience",
                            "reputation": self.reputation,
                        },
                    ))
                    continue
            elif c["state"] == "eating":
                c["eat_ticks_left"] = max(0, c.get("eat_ticks_left", 0) - 1)
                if c["eat_ticks_left"] == 0:
                    tip = c.get("tip", 0)
                    total = price + tip
                    self.money += total
                    self.earned += total
                    self.shift_earned += total
                    events.append((
                        "paid",
                        {
                            "order_id": c["id"],
                            "customer_id": c["id"],
                            "table_id": c["table_id"],
                            "dish": dish,
                            "dish_id": dish,
                            "base_price": price,
                            "price": price,
                            "tip": tip,
                            "amount": total,
                            "money": self.money,
                            "reason": "finished_eating",
                        },
                    ))
                    continue
            remaining_customers.append(c)
        self.customers = remaining_customers

        # 3. Di chuyển người chơi
        self._move(inp)

        # 4. Tương tác người chơi (tối đa 1 interact mỗi tick)
        if inp.pressed("interact"):
            self._handle_interact(events)

        # 5. Khách mới theo lịch
        if self.random_customers:
            first_tick = self.t.get("first_customer_tick", 120)
            interval = int(round(self.t.get("customer_interval_s", 15) * TICK))
            if self.sim_tick >= first_tick and (self.sim_tick - first_tick) % interval == 0:
                self._spawn_customer(events)

        # 6. Hết giờ ca làm: đóng quán (clarify #7) rồi mới phát quan_end
        if self.time_left_ticks <= 0:
            self.done = True
            self.reason = "time"
            self._close_shift(events)
            events.append((
                "quan_end",
                {
                    "reason": "time",
                    "money": self.money,
                    "earned": self.earned,
                    "shift_earned": self.shift_earned,
                    "reputation": self.reputation,
                },
            ))

        return events

    def _close_shift(self, events):
        """Đóng quán: khách đang ăn trả tiền ngay (`paid` reason `closing`), sau đó khách
        còn chờ rời đi (`customer_left` reason `closing`, KHÔNG trừ uy tín, nhả reserved).
        Mỗi nhóm xử lý theo thứ tự id khách."""
        ordered = sort_by_id(self.customers)
        for c in ordered:
            if c["state"] != "eating":
                continue
            dish = c.get("dish_id")
            price = c.get("base_price", self.menu.get(dish, {}).get("price", 0) if dish else 0)
            tip = c.get("tip", 0)
            total = price + tip
            self.money += total
            self.earned += total
            self.shift_earned += total
            events.append((
                "paid",
                {
                    "order_id": c["id"],
                    "customer_id": c["id"],
                    "table_id": c["table_id"],
                    "dish": dish,
                    "dish_id": dish,
                    "base_price": price,
                    "price": price,
                    "tip": tip,
                    "amount": total,
                    "money": self.money,
                    "reason": "closing",
                },
            ))
        for c in ordered:
            if c["state"] != "waiting":
                continue
            c["reserved"] = []
            events.append((
                "customer_left",
                {
                    "order_id": c["id"],
                    "customer_id": c["id"],
                    "table_id": c["table_id"],
                    "reason": "closing",
                    "reputation": self.reputation,
                },
            ))
        self.customers = []

    def _handle_interact(self, events):
        radius = self.t["interact_radius"]
        candidates = []
        for st in self.stoves:
            d = math.dist(self.pos, st["pos"])
            if d <= radius:
                candidates.append((d, 0, id_key(st["id"]), "stove", st))
        for tb in self.tables:
            d = math.dist(self.pos, tb["pos"])
            if d <= radius:
                candidates.append((d, 1, id_key(tb["id"]), "table", tb))
        if not candidates:
            return

        candidates.sort(key=lambda x: (x[0], x[1], x[2]))
        _, _, _, target_type, target_obj = candidates[0]

        if target_type == "stove":
            st = target_obj
            if st["state"] == "ready":
                if self.hand is None:
                    dish = st["dish"]
                    order_id = st.get("order_id")
                    self.hand = dish
                    self.hand_order_id = order_id
                    st["state"] = "idle"
                    st["dish"] = None
                    st["order_id"] = None
                    st["cook_ticks_left"] = 0
                    st["ready_ticks"] = 0
                    events.append((
                        "dish_picked",
                        {
                            "stove_id": st["id"],
                            "order_id": order_id,
                            "dish_id": dish,
                            "dish": dish,
                        },
                    ))
            elif st["state"] == "idle":
                pick = self._pick_dish_to_cook()
                if pick:
                    dish, cust = pick
                    use = set(cust["reserved"])
                    used = sorted((it for it in self.stock if it["id"] in use), key=_item_sort_key)
                    items = [_out_item(it) for it in used]
                    self.stock = [it for it in self.stock if it["id"] not in use]
                    cust["reserved"] = []
                    avg_fresh = sum((it["fresh"] for it in used), Fraction(0)) / len(used)
                    base_price = math.floor(self.menu[dish]["price"] * avg_fresh / 100)
                    cust["base_price"] = base_price
                    st["state"] = "cooking"
                    st["dish"] = dish
                    st["order_id"] = cust["id"]
                    st["cook_ticks_left"] = int(round(self.menu[dish]["cook_s"] * TICK))
                    st["ready_ticks"] = 0
                    cust["order_status"] = "cooking"
                    events.append((
                        "cook_started",
                        {
                            "stove_id": st["id"],
                            "order_id": cust["id"],
                            "dish_id": dish,
                            "dish": dish,
                            "items": items,
                            "base_price": base_price,
                        },
                    ))

        elif target_type == "table":
            tb = target_obj
            cust = next((c for c in self.customers if c["table_id"] == tb["id"]), None)
            if cust and cust["state"] == "waiting":
                if self.hand is not None and self.hand == cust["dish_id"]:
                    dish = self.hand
                    self.hand = None
                    self.hand_order_id = None
                    cust["state"] = "eating"
                    cust["order_status"] = "eating"
                    cust["eat_ticks_left"] = int(round(self.t["eat_s"] * TICK))
                    max_pat = int(round(self.t["patience_s"] * TICK))
                    tipped = (cust.get("patience_ticks_left", 0) / max_pat) >= self.t["tip_min_patience_ratio"]
                    price = cust.get("base_price", self.menu[dish]["price"])  # giá đã chốt lúc nấu
                    tip = int(round(price * self.t["tip_rate"])) if tipped else 0
                    if tipped:
                        self._add_reputation(self.t["tip_reputation"])
                    cust["tip"] = tip
                    cust["base_price"] = price
                    cust["reserved"] = []
                    events.append((
                        "served",
                        {
                            "order_id": cust["id"],
                            "customer_id": cust["id"],
                            "table_id": tb["id"],
                            "dish_id": dish,
                            "dish": dish,
                            "patience_ticks_left": cust.get("patience_ticks_left", 0),
                            "base_price": price,
                            "tip": tip,
                        },
                    ))

    def _spawn_customer(self, events):
        occupied = {c["table_id"] for c in self.customers}
        free_tables = sort_by_id([tb for tb in self.tables if tb["id"] not in occupied])
        if not free_tables:
            return

        target_table = free_tables[0]
        cookable = [dish for dish in sorted(self.menu.keys()) if self._reserve_for(dish) is not None]
        if not cookable:
            self._add_reputation(self.t["left_reputation_delta"])
            events.append(("no_dish", {}))
            return

        chosen_dish = self.rng.get("customer").choice(cookable)
        new_id = self.ids.new("C")
        new_cust = {
            "id": new_id,
            "table_id": target_table["id"],
            "dish_id": chosen_dish,
            "order_tick": self.sim_tick,
            "state": "waiting",
            "order_status": "waiting",
            "patience_ticks_left": int(round(self.t["patience_s"] * TICK)),
            "eat_ticks_left": int(round(self.t["eat_s"] * TICK)),
            "base_price": self.menu[chosen_dish]["price"],
            "tip": 0,
            "reserved": self._reserve_for(chosen_dish),
        }
        self.customers.append(new_cust)
        events.append((
            "customer_arrived",
            {
                "order_id": new_id,
                "customer_id": new_id,
                "table_id": target_table["id"],
                "dish_id": chosen_dish,
                "dish": chosen_dish,
            },
        ))

    def _move(self, inp):
        speed = self.t["walk_speed"]
        mx, mz = inp.move
        self.vel = ramp_velocity(self, (mx * speed, mz * speed), int(self.t.get("ramp_max_ticks", 6)))
        b = self.t["bounds"]
        for i, axis in enumerate(("x", "z")):
            self.pos[i] += self.vel[i] / TICK
            lo, hi = b[axis]
            if self.pos[i] <= lo:
                self.pos[i], self.vel[i] = lo, max(0.0, self.vel[i])
            elif self.pos[i] >= hi:
                self.pos[i], self.vel[i] = hi, min(0.0, self.vel[i])
