"""Buổi tối — Mở Quán. KHUNG & LUẬT CHƠI (Lát 3 & Lát 4 — Test Contract v1.0).

Khớp hoàn toàn hợp đồng tích hợp tại docs/contracts/README.md và PRD-0 mục E, F.
"""

import math

from ..ids import id_key, sort_by_id
from .ramp import ramp_velocity

TICK = 60.0


class QuanSim:
    mode = "quan"
    phase = "quan"

    def __init__(self, tuning, scenario, streams, ids, inventory=None):
        t = tuning["quan"]
        self.t = t
        self.menu = tuning["menu"]
        self.rng = streams
        self.ids = ids

        p = scenario.get("player", {})
        self.pos = list(p.get("pos", t["start_pos"]))
        self.vel = [float(c) for c in p.get("vel", [0.0, 0.0])]
        self._tgt = None
        self._ramp_left = 0

        # Kho: --inventory HOẶC scenario.stock
        self.stock = dict(inventory if inventory is not None else scenario.get("stock", {}))
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

            if item.get("state") == "waiting":
                if "reserved" not in item and dish in self.menu:
                    item["reserved"] = dict(self.menu[dish]["recipe"])
                else:
                    item.setdefault("reserved", {})
            else:
                item.setdefault("reserved", {})
            self.customers.append(item)
            ids.reserve(item["id"])

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
                from ..errors import BadInput
                raise BadInput(f"id bếp/bàn không tồn tại: {u['id']}")
            by_id[u["id"]].update(u)
        return sort_by_id(list(by_id.values()))

    def _add_reputation(self, delta):
        self.reputation = round(
            max(self.t["reputation_min"], min(self.t["reputation_max"], self.reputation + delta)), 3
        )

    def _available_stock(self):
        """Kho khả dụng = stock hiện tại trừ đi nguyên liệu đã bị khách giữ chỗ."""
        reserved_sum = {}
        for c in self.customers:
            for k, v in c.get("reserved", {}).items():
                reserved_sum[k] = reserved_sum.get(k, 0) + v
        return {k: max(0, self.stock.get(k, 0) - reserved_sum.get(k, 0)) for k in self.stock}

    def _pick_dish_to_cook(self):
        """Tìm món và khách đang chờ cần nấu cho một bếp trống."""
        in_progress_orders = set()
        if self.hand_order_id:
            in_progress_orders.add(self.hand_order_id)
        for st in self.stoves:
            if st.get("order_id"):
                in_progress_orders.add(st["order_id"])

        for cust in sort_by_id(self.customers):
            if cust.get("state") != "waiting":
                continue
            if cust["id"] in in_progress_orders:
                continue
            dish = cust.get("dish_id")
            if not dish or dish not in self.menu:
                continue
            recipe = self.menu[dish]["recipe"]
            if all(self.stock.get(k, 0) >= qty for k, qty in recipe.items()):
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
                "reserved": {k: c["reserved"][k] for k in sorted(c.get("reserved", {})) if c["reserved"][k] > 0},
                "base_price": base_p,
                "tip": c.get("tip", 0),
            })

        return {
            "player": {"pos": self.pos},
            "stock": {k: self.stock[k] for k in sorted(self.stock) if self.stock[k] > 0},
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

        # 6. Hết giờ ca làm
        if self.time_left_ticks <= 0:
            self.done = True
            self.reason = "time"
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
                    recipe = self.menu[dish]["recipe"]
                    for ing, qty in recipe.items():
                        self.stock[ing] = self.stock.get(ing, 0) - qty
                        if ing in cust.get("reserved", {}):
                            cust["reserved"][ing] = max(0, cust["reserved"][ing] - qty)
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
                            "items": {k: recipe[k] for k in sorted(recipe)},
                            "base_price": self.menu[dish]["price"],
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
                    price = self.menu[dish]["price"]
                    tip = int(round(price * self.t["tip_rate"])) if tipped else 0
                    if tipped:
                        self._add_reputation(self.t["tip_reputation"])
                    cust["tip"] = tip
                    cust["base_price"] = price
                    cust["reserved"] = {}
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
        avail = self._available_stock()
        cookable = [
            dish
            for dish in sorted(self.menu.keys())
            if all(avail.get(k, 0) >= qty for k, qty in self.menu[dish]["recipe"].items())
        ]
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
            "reserved": dict(self.menu[chosen_dish]["recipe"]),
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
