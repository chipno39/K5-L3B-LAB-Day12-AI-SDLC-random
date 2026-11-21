"""Unit test `sim/quan` theo Contract v1.2: Độ tươi & Kho cá thể."""

import copy
import unittest

from chonoi.contract import load_contract
from chonoi.errors import BadInput
from chonoi.ids import IdAllocator
from chonoi.inputs import InputPlayer
from chonoi.rng import Streams
from chonoi.sim.quan import QuanSim

from test_quan_p2 import tuning_v12


def item(iid, kind, fresh):
    return {"id": iid, "kind": kind, "fresh": fresh}


def make_sim(tuning, scenario=None, inventory=None, seed=1):
    return QuanSim(tuning, scenario or {}, Streams(seed), IdAllocator(), inventory=inventory)


def step(sim, k=0, interact=False):
    fr = [{"tick": k, "interact": True}] if interact else []
    return sim.step(InputPlayer(fr).advance(k))


def one_customer(dish, reserved=None, cid="C1", table="T1"):
    c = {"id": cid, "table_id": table, "dish_id": dish}
    if reserved is not None:
        c["reserved"] = reserved
    return c


class FreshnessDecayTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tuning = tuning_v12(load_contract()["tuning"])
        cls.f = cls.tuning["freshness"]

    def test_stock_decays_quan_rate_per_second(self):
        sim = make_sim(self.tuning, {"random_customers": False}, inventory=[item("I1", "ca_loc", 100)])
        for k in range(60):
            step(sim, k)
        self.assertAlmostEqual(sim.stock[0]["fresh"], 100 - self.f["quan_decay_per_s"], places=4)

    def test_spoiled_emitted_once_when_crossing_threshold(self):
        thr = self.f["spoiled_below"]
        inv = [item("I1", "ca_loc", thr), item("I2", "ca_loc", thr - 1)]  # I2 đã ươn từ đầu
        sim = make_sim(self.tuning, {"random_customers": False}, inventory=inv)
        first = step(sim, 0)
        self.assertEqual([(n, d["item_id"]) for n, d in first], [("spoiled", "I1")])
        self.assertEqual([n for n, _ in step(sim, 1)], [])

    def test_count_based_stock_is_rejected(self):
        with self.assertRaises(BadInput):
            make_sim(self.tuning, inventory={"ca_loc": 2})


class FreshReservationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tuning = tuning_v12(load_contract()["tuning"])
        cls.thr = cls.tuning["freshness"]["spoiled_below"]

    def test_reserve_freshest_tie_smallest_id(self):
        inv = [item("I1", "ca_loc", 80), item("I3", "ca_loc", 90), item("I2", "ca_loc", 90)]
        sim = make_sim(self.tuning, {"random_customers": False,
                                     "customers": [one_customer("ca_loc_nuong_trui")]}, inventory=inv)
        self.assertEqual(sim.snapshot()["customers"][0]["reserved"], ["I2"])

    def test_spoiled_items_are_never_reserved(self):
        inv = [item("I1", "ca_loc", self.thr - 0.5)]
        sim = make_sim(self.tuning, {"random_customers": False,
                                     "customers": [one_customer("ca_loc_nuong_trui")]}, inventory=inv)
        c = sim.snapshot()["customers"][0]
        self.assertEqual((c["reserved"], c["order_status"]), ([], "unfulfillable"))

    def test_reserved_item_spoils_then_rereserved_once(self):
        inv = [item("I1", "ca_loc", self.thr), item("I2", "ca_loc", 50)]
        sim = make_sim(self.tuning, {"random_customers": False,
                                     "customers": [one_customer("ca_loc_nuong_trui", reserved=["I1"])]},
                       inventory=inv)
        step(sim, 0)
        c = sim.snapshot()["customers"][0]
        self.assertEqual((c["reserved"], c["order_status"]), (["I2"], "waiting"))

    def test_reserved_item_spoils_without_replacement_becomes_unfulfillable(self):
        inv = [item("I1", "ca_loc", self.thr), item("I2", "ca_keo", 90)]
        sc = {"random_customers": False, "player": {"pos": [2, 8]},
              "customers": [one_customer("ca_loc_nuong_trui", reserved=["I1"])]}
        sim = make_sim(self.tuning, sc, inventory=inv)
        step(sim, 0)
        c = sim.snapshot()["customers"][0]
        self.assertEqual((c["reserved"], c["order_status"]), ([], "unfulfillable"))
        # chỉ thử giữ lại 1 lần: thêm cá tươi sau đó cũng không tự giữ lại, bếp không nấu
        sim.stock.append(item("I9", "ca_loc", 95))
        evs = step(sim, 1, interact=True)
        self.assertNotIn("cook_started", [n for n, _ in evs])
        self.assertEqual(sim.snapshot()["customers"][0]["reserved"], [])

    def test_no_dish_when_only_spoiled_stock(self):
        inv = [item("I1", "bong_sung", self.thr - 1), item("I2", "bong_sung", self.thr - 1)]
        sim = make_sim(self.tuning, inventory=inv)
        evs = []
        for k in range(self.tuning["quan"]["first_customer_tick"]):
            evs.extend(step(sim, k))
        self.assertIn("no_dish", [n for n, _ in evs])
        self.assertNotIn("customer_arrived", [n for n, _ in evs])


class FreshPriceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        base = tuning_v12(load_contract()["tuning"])
        cls.tuning = copy.deepcopy(base)
        cls.tuning["freshness"]["quan_decay_per_s"] = 0  # cố định độ tươi để kiểm giá chính xác

    def test_cook_started_items_sorted_kind_then_id_and_price_by_avg_fresh(self):
        inv = [item("I3", "ca_linh", 80), item("I1", "ca_linh", 70), item("I2", "ca_linh", 90),
               item("I4", "bong_dien_dien", 60)]
        sc = {"random_customers": False, "player": {"pos": [2, 8]},
              "customers": [one_customer("lau_ca_linh_dien_dien")]}
        sim = make_sim(self.tuning, sc, inventory=inv)
        evs = dict(step(sim, 0, interact=True))
        cs = evs["cook_started"]
        self.assertEqual([i["id"] for i in cs["items"]], ["I4", "I1", "I2", "I3"])
        price = self.tuning["menu"]["lau_ca_linh_dien_dien"]["price"]
        self.assertEqual(cs["base_price"], price * 75 // 100)  # avg = (70+90+80+60)/4 = 75
        self.assertEqual(sim.stock, [])
        self.assertEqual(sim.snapshot()["customers"][0]["base_price"], cs["base_price"])

    def test_tip_and_paid_use_fresh_price(self):
        inv = [item("I1", "ca_loc", 50)]
        sc = {"random_customers": False, "player": {"pos": [2, 8]},
              "customers": [one_customer("ca_loc_nuong_trui")]}
        sim = make_sim(self.tuning, sc, inventory=inv)
        step(sim, 0, interact=True)
        cust = sim.customers[0]
        menu_price = self.tuning["menu"]["ca_loc_nuong_trui"]["price"]
        self.assertEqual(cust["base_price"], menu_price // 2)
        # bỏ qua thời gian nấu: đặt món lên tay rồi mang ra bàn T1 [9,2]
        sim.hand, sim.hand_order_id = "ca_loc_nuong_trui", "C1"
        sim.stoves[0].update(state="idle", dish=None, order_id=None)
        sim.pos = [9.0, 2.0]
        served = dict(step(sim, 1, interact=True))["served"]
        rate = self.tuning["quan"]["tip_rate"]
        self.assertEqual((served["base_price"], served["tip"]),
                         (menu_price // 2, int(round(menu_price // 2 * rate))))


if __name__ == "__main__":
    unittest.main()
