"""Vòng tick (Contract B, v1.1): hỗ trợ gather, quan, day (vòng ngày + Shop) và Pause.

Thứ tự ghi: (nếu mode=day: các event mở đầu tick 0) -> snapshot tick 0 -> với mỗi bước:
sự kiện (theo thứ tự xử lý) rồi snapshot (nếu tới lượt hoặc buổi kết thúc) -> dòng 'end'.
Mỗi tick tối đa một snapshot.

`Session` là API bước tick gọn dùng chung cho headless (`run`) và cửa sổ chơi trực tiếp (`chonoi.live`):
cả hai chạy CÙNG một lớp sim, không nhân đôi logic.
"""

import inspect
import math

from .errors import BadInput
from .ids import IdAllocator, sort_by_id
from .inputs import InputPlayer
from .inventory import fresh_num, write_inventory
from .jsonl import JsonlWriter
from .rng import Streams
from .sim.gather import GatherSim
from .sim.quan import QuanSim


def build_sim(mode, tuning, scenario, seed, inventory, day_num=1, active_upgrades=None):
    streams, ids = Streams(seed), IdAllocator()
    if mode == "gather":
        return GatherSim(tuning, scenario, streams, ids, day_num=day_num, active_upgrades=active_upgrades)
    return QuanSim(tuning, scenario, streams, ids, inventory=inventory)


def _calc_score(earned, reputation, tuning):
    mult = tuning["score"]["reputation_multiplier"]
    return earned + mult * math.floor(reputation)


def _build_day_plans(tuning, day_sc):
    plans = {int(p["day"]): {"dishes": dict(p["dishes"]), "ingredients": dict(p["ingredients"])}
             for p in tuning.get("day_plan", [])}
    menu = tuning["menu"]
    for item in day_sc.get("day_plan", []):
        dnum = int(item["day"])
        dishes = dict(item["dishes"])
        ing = {}
        for did, cnt in dishes.items():
            if did not in menu:
                raise BadInput(f"day_plan: món lạ {did!r}")
            for k, q in menu[did]["recipe"].items():
                ing[k] = ing.get(k, 0) + q * cnt
        plans[dnum] = {"dishes": dishes, "ingredients": ing}
    return plans


class Session:
    """Một lượt chơi (gather, quan hoặc day): dựng sim, bước từng tick, hỗ trợ pause & shop."""

    def __init__(self, mode, tuning, scenario, seed, inventory=None, days=1):
        self.mode = mode
        self.tuning = tuning
        self.scenario = scenario or {}
        self.seed = seed
        self.tick = 0
        self.sim_tick = 0
        self.phase_tick = 0
        self.paused = False
        self.init_events = []

        if mode == "day":
            self.target_days = int(days)
            self.days_completed = 0
            self.day = 1
            day_sc = self.scenario.get("day", {})
            self.money = int(day_sc.get("money", 0))
            self.earned = int(day_sc.get("earned", 0))
            self.reputation = float(day_sc.get("reputation", tuning["quan"]["reputation_initial"]))
            self.upgrades = {k: int(v) for k, v in day_sc.get("upgrades", {}).items()}
            self.active_upgrades = dict(self.upgrades)
            self.plans = _build_day_plans(tuning, day_sc)
            self.streams = Streams(seed)
            self.item_ids = IdAllocator()
            self.phase = "gather"
            self.shop_stock = []
            self.shop_time_left = 0
            self._done = False
            self._reason = None
            self._start_day(emit_to=self.init_events, tick_override=0)
        else:
            self.target_days = 1
            self.days_completed = 0
            self.day = 1
            self.sim = build_sim(mode, tuning, self.scenario, seed, inventory)
            self.phase = self.sim.phase
            self._done = False
            self._reason = None

    def _ev(self, name, data, phase=None, tick=None):
        row = {
            "type": "event",
            "tick": self.tick if tick is None else tick,
            "phase": self.phase if phase is None else phase,
            "name": name,
            "data": data,
        }
        if self.mode == "day":
            row["day"] = self.day
        return row

    def _current_plan(self):
        if self.day in self.plans:
            return self.plans[self.day]
        if self.plans:
            cycle_day = ((self.day - 1) % 5) + 1
            if cycle_day in self.plans:
                return self.plans[cycle_day]
        return {"dishes": {}, "ingredients": {}}

    def _start_day(self, emit_to, tick_override=None):
        self.phase = "gather"
        self.phase_tick = 0
        gather_sc = self.scenario.get("gather", {})
        self.sim = GatherSim(
            self.tuning, gather_sc, self.streams, IdAllocator(),
            day_num=self.day, active_upgrades=self.active_upgrades, item_ids=self.item_ids,
        )
        self.sim.money = self.money
        self.sim.earned = self.earned
        self.sim.reputation = self.reputation
        plan = self._current_plan()
        emit_to.append(self._ev("day_start", {}, phase="gather", tick=tick_override))
        emit_to.append(self._ev("day_plan", {"dishes": dict(plan["dishes"]), "ingredients": dict(plan["ingredients"])},
                                phase="gather", tick=tick_override))
        emit_to.append(self._ev("phase_start", {}, phase="gather", tick=tick_override))

    def _start_quan(self, inventory_items, emit_to):
        self.phase = "quan"
        self.phase_tick = 0
        quan_sc = self.scenario.get("quan", {})
        plan_dishes = set(self._current_plan()["dishes"].keys())
        if "dishes" in inspect.signature(QuanSim.__init__).parameters:
            self.sim = QuanSim(self.tuning, quan_sc, self.streams, IdAllocator(),
                               inventory=inventory_items, dishes=plan_dishes)
        else:
            filtered_tuning = dict(self.tuning)
            if plan_dishes:
                filtered_tuning["menu"] = {k: v for k, v in self.tuning["menu"].items() if k in plan_dishes}
            self.sim = QuanSim(filtered_tuning, quan_sc, self.streams, IdAllocator(), inventory=inventory_items)
        self.sim.money = self.money
        self.sim.earned = self.earned
        self.sim.reputation = self.reputation
        emit_to.append(self._ev("phase_start", {}, phase="quan"))

    def _start_shop(self, leftover_stock, emit_to):
        self.phase = "shop"
        self.phase_tick = 0
        if isinstance(leftover_stock, list):
            self.shop_stock = [
                {"id": it["id"], "kind": it["kind"], "fresh": fresh_num(it["fresh"])}
                for it in sort_by_id(leftover_stock)
            ]
        else:
            self.shop_stock = {k: int(v) for k, v in sorted(leftover_stock.items()) if v > 0}
        self.shop_time_left = int(self.tuning.get("shop", {}).get("max_ticks", 600))
        self.sim = None
        emit_to.append(self._ev("phase_start", {}, phase="shop"))

    @property
    def done(self) -> bool:
        if self.mode == "day":
            return self._done
        return self.sim.done

    @property
    def reason(self):
        if self.mode == "day":
            return self._reason if self._done else "tick_limit"
        return self.sim.reason if self.sim.done else "tick_limit"

    def _cur_money(self):
        if self.mode == "day":
            return self.sim.money if self.sim is not None else self.money
        return self.sim.money

    def _cur_earned(self):
        if self.mode == "day":
            return self.sim.earned if self.sim is not None else self.earned
        return self.sim.earned

    def _cur_reputation(self):
        if self.mode == "day":
            return self.sim.reputation if self.sim is not None else self.reputation
        return self.sim.reputation

    def snapshot(self) -> dict:
        if self.done:
            state = "finished"
        elif self.paused:
            state = "paused"
        else:
            state = "playing"
        money = self._cur_money()
        earned = self._cur_earned()
        rep = self._cur_reputation()
        time_left = self.shop_time_left if (self.mode == "day" and self.phase == "shop") else self.sim.time_left_ticks
        s = {
            "type": "snapshot",
            "tick": self.tick,
            "sim_tick": self.sim_tick,
            "mode": self.mode,
            "phase": self.phase,
            "phase_tick": self.phase_tick,
            "state": state,
            "time_left_ticks": time_left,
            "money": money,
            "earned": earned,
            "reputation": rep,
            "score": _calc_score(earned, rep, self.tuning),
        }
        if self.mode == "day":
            plan = self._current_plan()
            s["day"] = self.day
            s["day_plan"] = {"dishes": dict(plan["dishes"]), "ingredients": dict(plan["ingredients"])}
            s["upgrades"] = dict(self.upgrades)
            s["active_upgrades"] = dict(self.active_upgrades)
            if self.phase == "shop":
                s["stock"] = [dict(it) for it in self.shop_stock] if isinstance(self.shop_stock, list) else dict(self.shop_stock)
            else:
                s.update(self.sim.snapshot())
        else:
            s.update(self.sim.snapshot())
        return s

    def _step_shop(self, inp, out_events):
        self.shop_time_left = max(0, self.shop_time_left - 1)
        # Xử lý một buy trước shop_done, kể cả bước cuối
        if inp.buy is not None:
            action = inp.buy
            shop_ups = self.tuning.get("shop", {}).get("upgrades", {})
            if action in shop_ups:
                tiers = shop_ups[action]
                cur = self.upgrades.get(action, 0)
                if cur >= len(tiers):
                    out_events.append(self._ev("buy_failed", {"action": action, "reason": "max_level"}))
                else:
                    nxt = tiers[cur]
                    price = int(nxt["price"])
                    if self.money < price:
                        out_events.append(self._ev("buy_failed", {"action": action, "reason": "funds"}))
                    else:
                        self.money -= price
                        self.upgrades[action] = int(nxt["level"])
                        out_events.append(self._ev("bought", {
                            "upgrade": action,
                            "level": int(nxt["level"]),
                            "price": price,
                            "money": self.money,
                        }))
            else:
                out_events.append(self._ev("buy_failed", {"action": action, "reason": "unknown"}))

        close_reason = None
        if inp.pressed("shop_done"):
            close_reason = "done"
        elif self.shop_time_left <= 0:
            close_reason = "time"

        if close_reason is not None:
            out_events.append(self._ev("shop_end", {"reason": close_reason}, phase="shop"))
            self.days_completed += 1
            if self.days_completed >= self.target_days:
                self._done = True
                self._reason = "days_complete"
            else:
                self.day += 1
                self.active_upgrades = dict(self.upgrades)
                self._start_day(emit_to=out_events)

    def step(self, inp) -> list:
        """Chạy một bước với `inp` (chonoi.inputs.InputState); trả các dòng event (tick = k + 1)."""
        self.tick += 1
        out_events = []

        # Xét cạnh pause trước (TICKET-02 mục 4.2)
        if inp.pressed("pause"):
            if not self.paused:
                self.paused = True
                out_events.append(self._ev("paused", {}))
                return out_events
            else:
                self.paused = False
                out_events.append(self._ev("resumed", {}))
        elif self.paused:
            return out_events

        # Gameplay bước 1 tick
        self.sim_tick += 1
        self.phase_tick += 1

        if self.mode != "day":
            raw = self.sim.step(inp)
            for name, data in raw:
                out_events.append(self._ev(name, data, phase=self.sim.phase))
            return out_events

        # Chế độ day
        if self.phase == "gather":
            raw = self.sim.step(inp)
            for name, data in raw:
                out_events.append(self._ev(name, data, phase="gather"))
            if self.sim.done:
                inv = self.sim.inventory_items()
                self._start_quan(inv, out_events)
        elif self.phase == "quan":
            raw = self.sim.step(inp)
            for name, data in raw:
                out_events.append(self._ev(name, data, phase="quan"))
            if self.sim.done:
                self.money = self.sim.money
                self.earned = self.sim.earned
                self.reputation = self.sim.reputation
                self._start_shop(self.sim.stock, out_events)
        elif self.phase == "shop":
            self._step_shop(inp, out_events)

        return out_events

    def end_row(self) -> dict:
        money = self._cur_money()
        earned = self._cur_earned()
        rep = self._cur_reputation()
        row = {
            "type": "end",
            "ticks": self.tick,
            "sim_tick": self.sim_tick,
            "mode": self.mode,
            "state": "finished" if self.done else ("paused" if self.paused else "playing"),
            "reason": self.reason,
            "money": money,
            "earned": earned,
            "reputation": rep,
            "score": _calc_score(earned, rep, self.tuning),
        }
        if self.mode == "day":
            row["days_completed"] = self.days_completed
        return row

    def write_inventory_if_done(self, inventory_out):
        """File kho: ghi MỘT lần khi có gather_end; chưa kết thúc thì giữ nguyên file đích."""
        if self.mode == "gather" and self.sim.done and inventory_out:
            write_inventory(inventory_out, self.sim.inventory_items())


def run(mode, tuning, scenario, seed, frames, ticks, out_path, snapshot_every,
        inventory=None, inventory_out=None, days=1):
    sess = Session(mode, tuning, scenario, seed, inventory=inventory, days=days)
    player = InputPlayer(frames)
    w = JsonlWriter(out_path)
    try:
        for row in sess.init_events:
            w.write(row)
        w.write(sess.snapshot())  # tick 0: sau khi dựng scenario, trước mọi input
        last_snapped = 0
        while sess.tick < ticks and not sess.done:
            inp = player.advance(sess.tick)  # bước k đọc input có tick == k
            for row in sess.step(inp):
                w.write(row)
            if sess.tick % snapshot_every == 0 or sess.done:
                w.write(sess.snapshot())
                last_snapped = sess.tick
        if last_snapped != sess.tick:
            w.write(sess.snapshot())
        w.write(sess.end_row())
    finally:
        w.close()
    sess.write_inventory_if_done(inventory_out)
    return sess.sim
