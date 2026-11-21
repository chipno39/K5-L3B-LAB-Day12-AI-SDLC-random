"""Headless checks for inventory compatibility and restaurant freshness in v1.2."""

import math
import unittest
from pathlib import Path

from chonoi.contract import load_contract

from helpers import Workdir, events, frames, item_units, read_jsonl, run_headless, snapshots, write_json


class LegacyInventoryTests(unittest.TestCase):
    def test_count_inventory_exits_two_without_writing_output(self):
        with Workdir() as tmp:
            inventory = write_json(tmp.path("old.json"), {"items": {"ca_loc": 1}})
            log = Path(tmp.path("out.jsonl"))
            code, err = run_headless("--mode", "quan", "--seed", "1", "--ticks", "0",
                                     "--inventory", inventory, "--out", str(log))
            self.assertEqual(code, 2, err)
            self.assertFalse(log.exists())


class QuanFreshnessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tuning = load_contract()["tuning"]

    def run_quan(self, stock, dish, reserved, ticks, cook=False):
        quan = self.tuning["quan"]
        with Workdir() as tmp:
            scenario = write_json(tmp.path("scenario.json"), {"quan": {
                "player": {"pos": quan["stoves"][0]["pos"]},
                "stock": stock,
                "customers": [{"id": "C1", "table_id": quan["tables"][0]["id"],
                               "dish_id": dish, "state": "waiting",
                               "order_status": "reserved", "reserved": reserved}],
                "random_customers": False,
            }})
            inputs = write_json(tmp.path("inputs.json"),
                                frames(*([{"tick": 0, "interact": True}] if cook else [])))
            log = tmp.path("out.jsonl")
            code, err = run_headless("--mode", "quan", "--seed", "1", "--ticks", str(ticks),
                                     "--scenario", scenario, "--inputs", inputs,
                                     "--snapshot-every", "1", "--out", log)
            self.assertEqual(code, 0, err)
            return read_jsonl(log)

    def test_threshold_and_replacement_of_spoiled_reservation(self):
        threshold = self.tuning["freshness"]["spoiled_below"]
        for replacement in (False, True):
            with self.subTest(replacement=replacement):
                stock = item_units("ca_loc", fresh=threshold)
                if replacement:
                    stock += [{"id": "I3", "kind": "ca_loc", "fresh": 80},
                              {"id": "I2", "kind": "ca_loc", "fresh": 80}]
                rows = self.run_quan(stock, "ca_loc_nuong_trui", ["I1"], ticks=3)
                state = snapshots(rows)
                self.assertEqual(state[0]["customers"][0]["reserved"], ["I1"])
                self.assertEqual(state[0]["stock"][0]["fresh"], threshold)
                spoiled = events(rows, "spoiled")
                self.assertEqual([(r["tick"], r["data"]) for r in spoiled],
                                 [(1, {"item_id": "I1", "kind": "ca_loc", "location": "stock"})])
                for snap in state[1:]:
                    customer = snap["customers"][0]
                    self.assertEqual(customer["reserved"], ["I2"] if replacement else [])
                    if not replacement:
                        self.assertEqual(customer["order_status"], "unfulfillable")

    def test_cook_price_uses_average_freshness_and_floor(self):
        dish = "goi_bong_sung"
        stock = item_units("bong_sung", "bong_sung", fresh=65)
        stock[1]["fresh"] = 80
        rows = self.run_quan(stock, dish, ["I1", "I2"], ticks=1, cook=True)
        started = events(rows, "cook_started")
        self.assertEqual(len(started), 1)
        data = started[0]["data"]
        self.assertEqual(data["dish_id"], dish)
        decay = self.tuning["freshness"]["quan_decay_per_s"] / self.tuning["tick_hz"]
        average = sum(item["fresh"] - decay for item in stock) / len(stock)
        self.assertEqual(data["base_price"], math.floor(self.tuning["menu"][dish]["price"] * average / 100))
        self.assertEqual(data["items"], [dict(item, fresh=round(item["fresh"] - decay, 3)) for item in stock])
