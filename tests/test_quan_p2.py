"""Unit test `sim/quan` theo Contract v1.1: 2 bếp, 4 bàn, 6 món, lọc thực đơn theo day_plan."""

import unittest

from chonoi.contract import load_contract
from chonoi.errors import BadInput
from chonoi.ids import IdAllocator
from chonoi.inputs import InputPlayer
from chonoi.rng import Streams
from chonoi.sim.quan import QuanSim, filter_menu

RICH_STOCK = {
    "ca_linh": 40, "ca_loc": 40, "ca_keo": 40,
    "bong_dien_dien": 40, "bong_sung": 40, "keo_neo": 40,
}


def make_sim(tuning, scenario=None, inventory=None, dishes=None, seed=1):
    return QuanSim(tuning, scenario or {}, Streams(seed), IdAllocator(), inventory=inventory, dishes=dishes)


def run_idle(sim, ticks):
    inp = InputPlayer([])
    out = []
    for k in range(ticks):
        out.extend(sim.step(inp.advance(k)))
        if sim.done:
            break
    return out


class QuanLayoutV11Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tuning = load_contract()["tuning"]

    def test_two_stoves_and_four_tables_from_contract(self):
        snap = make_sim(self.tuning).snapshot()
        self.assertEqual([s["id"] for s in snap["stoves"]], ["B1", "B2"])
        self.assertEqual([t["id"] for t in snap["tables"]], ["T1", "T2", "T3", "T4"])
        self.assertTrue(all(s["state"] == "idle" for s in snap["stoves"]))

    def test_full_menu_has_six_dishes_without_day_plan(self):
        self.assertEqual(len(make_sim(self.tuning).menu), 6)

    def test_customers_fill_four_tables_then_reuse_freed_table(self):
        sim = make_sim(self.tuning, inventory=RICH_STOCK)
        q = self.tuning["quan"]
        interval = int(round(q["customer_interval_s"] * 60))
        # 4 lượt đầu lấp T1..T4; lượt thứ 5 (tick 120 + 4*900 = 3720) trùng tick khách T1
        # hết kiên nhẫn (120 + 3600) -> customer_left xử lý trước, khách mới vào lại T1.
        ticks = q["first_customer_tick"] + 4 * interval
        events = run_idle(sim, ticks)
        arrived = [d["table_id"] for n, d in events if n == "customer_arrived"]
        self.assertEqual(arrived, ["T1", "T2", "T3", "T4", "T1"])
        names = [n for n, _ in events]
        self.assertLess(names.index("customer_left"), len(names) - 1)
        self.assertEqual(names[-1], "customer_arrived")

    def test_two_stoves_cook_two_orders_in_parallel(self):
        scenario = {
            "random_customers": False,
            "customers": [
                {"id": "C1", "table_id": "T1", "dish_id": "goi_bong_sung"},
                {"id": "C2", "table_id": "T2", "dish_id": "ca_keo_nuong"},
            ],
        }
        sim = make_sim(self.tuning, scenario, inventory=RICH_STOCK)
        # đứng giữa B1 [2,8] và B2 [5,8] lần lượt để bật bếp
        sim.pos = [2.0, 8.0]
        ev1 = sim.step(InputPlayer([{"tick": 0, "interact": True}]).advance(0))
        sim.pos = [5.0, 8.0]
        ev2 = sim.step(InputPlayer([{"tick": 1, "interact": True}]).advance(1))
        started = [(d["stove_id"], d["order_id"]) for n, d in ev1 + ev2 if n == "cook_started"]
        self.assertEqual(started, [("B1", "C1"), ("B2", "C2")])
        states = {s["id"]: s["state"] for s in sim.snapshot()["stoves"]}
        self.assertEqual(states, {"B1": "cooking", "B2": "cooking"})


class QuanDayPlanMenuTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tuning = load_contract()["tuning"]

    def test_filter_menu_keeps_only_plan_dishes(self):
        plan = self.tuning["day_plan"][2]["dishes"]  # D3
        menu = filter_menu(self.tuning["menu"], plan)
        self.assertEqual(sorted(menu), sorted(plan))

    def test_unknown_plan_dish_is_bad_input(self):
        with self.assertRaises(BadInput):
            filter_menu(self.tuning["menu"], {"pho_bo": 1})

    def test_customers_only_order_dishes_in_day_plan(self):
        for plan in self.tuning["day_plan"]:
            with self.subTest(day=plan["day"]):
                sim = make_sim(self.tuning, inventory=RICH_STOCK, dishes=plan["dishes"], seed=plan["day"])
                events = run_idle(sim, 2000)
                ordered = {d["dish_id"] for n, d in events if n == "customer_arrived"}
                self.assertTrue(ordered)
                self.assertTrue(ordered <= set(plan["dishes"]), ordered)

    def test_no_dish_when_stock_only_fits_dishes_outside_plan(self):
        # D1 = ca_loc_nuong_trui + goi_bong_sung; kho chỉ có ca_keo -> không món nào nấu được
        sim = make_sim(self.tuning, inventory={"ca_keo": 10}, dishes=self.tuning["day_plan"][0]["dishes"])
        events = run_idle(sim, self.tuning["quan"]["first_customer_tick"])
        self.assertEqual([n for n, _ in events], ["no_dish"])


class QuanClosingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tuning = load_contract()["tuning"]

    def test_closing_pays_eating_then_waiting_leave_without_reputation_loss(self):
        scenario = {
            "random_customers": False,
            "time_left_ticks": 1,
            "reputation": 3.0,
            "customers": [
                {"id": "C1", "table_id": "T1", "dish_id": "goi_bong_sung"},
                {"id": "C2", "table_id": "T2", "dish_id": "ca_keo_nuong", "state": "eating",
                 "order_status": "eating", "base_price": 70, "tip": 14, "eat_ticks_left": 300},
            ],
        }
        sim = make_sim(self.tuning, scenario, inventory=RICH_STOCK)
        events = run_idle(sim, 1)

        self.assertEqual([n for n, _ in events], ["paid", "customer_left", "quan_end"])
        paid, left, end = (d for _, d in events)
        self.assertEqual((paid["order_id"], paid["reason"], paid["amount"]), ("C2", "closing", 84))
        self.assertEqual((left["order_id"], left["reason"]), ("C1", "closing"))
        self.assertEqual(left["reputation"], 3.0)
        self.assertEqual((end["money"], end["shift_earned"], end["reputation"]), (84, 84, 3.0))
        # quán đóng: không còn khách, stock (kể cả phần từng giữ chỗ) còn nguyên cho Shop
        self.assertEqual(sim.snapshot()["customers"], [])
        self.assertEqual(sim.stock["bong_sung"], RICH_STOCK["bong_sung"])

    def test_empty_shop_closes_with_only_quan_end(self):
        sim = make_sim(self.tuning, {"time_left_ticks": 1, "random_customers": False})
        self.assertEqual([n for n, _ in run_idle(sim, 1)], ["quan_end"])


if __name__ == "__main__":
    unittest.main()
