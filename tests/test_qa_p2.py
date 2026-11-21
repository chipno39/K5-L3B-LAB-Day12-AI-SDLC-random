"""Black box checks for the v1.1 restaurant and day CLI."""

import unittest
from pathlib import Path

from chonoi.contract import load_contract

from helpers import Workdir, events, frames, read_jsonl, run_headless, snapshots, write_json


class Phase2QA(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tuning = load_contract()["tuning"]

    def test_quan_accepts_new_ingredient_and_reserves_recipe(self):
        dish = "ca_keo_nuong"
        recipe = self.tuning["menu"][dish]["recipe"]
        quan = self.tuning["quan"]
        with Workdir() as tmp:
            inventory = write_json(tmp.path("inventory.json"), {"items": recipe})
            log = tmp.path("quan.jsonl")
            code, err = run_headless(
                "--mode", "quan", "--seed", "1",
                "--ticks", str(quan["first_customer_tick"]),
                "--inventory", inventory, "--out", log,
            )
            self.assertEqual(code, 0, err)
            rows = read_jsonl(log)
        arrivals = events(rows, "customer_arrived")
        self.assertEqual(len(arrivals), 1)
        self.assertEqual(arrivals[0]["tick"], quan["first_customer_tick"])
        self.assertEqual(arrivals[0]["data"]["dish_id"], dish)
        final = snapshots(rows)[-1]
        self.assertEqual(final["stock"], recipe)
        self.assertEqual(final["customers"][0]["reserved"], recipe)

    def test_quan_serving_new_dish_pays_once_after_eating(self):
        dish = "ca_keo_nuong"
        quan = self.tuning["quan"]
        tick_hz = self.tuning["tick_hz"]
        table = quan["tables"][0]
        eat_ticks = round(quan["eat_s"] * tick_hz)
        price = self.tuning["menu"][dish]["price"]
        tip = round(price * quan["tip_rate"])
        with Workdir() as tmp:
            scenario = write_json(tmp.path("scenario.json"), {"quan": {
                "player": {"pos": table["pos"]},
                "hand": dish,
                "customers": [{"id": "C1", "table_id": table["id"], "dish_id": dish,
                               "state": "waiting", "order_status": "assigned",
                               "patience_ticks_left": round(quan["patience_s"] * tick_hz)}],
                "random_customers": False,
            }})
            inputs = write_json(tmp.path("inputs.json"), frames({"tick": 0, "interact": True}))
            log = tmp.path("quan.jsonl")
            code, err = run_headless(
                "--mode", "quan", "--seed", "1", "--ticks", str(eat_ticks + 2),
                "--scenario", scenario, "--inputs", inputs, "--out", log,
            )
            self.assertEqual(code, 0, err)
            rows = read_jsonl(log)
        served = events(rows, "served")
        self.assertEqual([(e["tick"], e["data"]["order_id"]) for e in served], [(1, "C1")])
        paid = events(rows, "paid")
        self.assertEqual([(e["tick"], e["data"]["order_id"]) for e in paid], [(eat_ticks + 1, "C1")])
        self.assertEqual(paid[0]["data"]["amount"], price + tip)
        self.assertEqual(paid[0]["data"]["reason"], "finished_eating")
        final = snapshots(rows)[-1]
        self.assertEqual(final["money"], price + tip)
        self.assertEqual(final["customers"], [])
        self.assertIsNone(final["hand"])

    def test_day_cli_is_deterministic_through_shop_and_finishes_one_day(self):
        with Workdir() as tmp:
            scenario = write_json(tmp.path("scenario.json"), {
                "gather": {"random_fish": False, "monsters": []},
                "quan": {"time_left_ticks": 1, "random_customers": False},
            })
            inputs = write_json(tmp.path("inputs.json"), frames(
                {"tick": 0, "interact": True},
                {"tick": 1, "interact": False},
                {"tick": 2, "shop_done": True},
            ))
            logs = [Path(tmp.path(name)) for name in ("first.jsonl", "second.jsonl")]
            for log in logs:
                code, err = run_headless(
                    "--mode", "day", "--days", "1", "--seed", "1", "--ticks", "10",
                    "--scenario", scenario, "--inputs", inputs, "--out", str(log),
                )
                self.assertEqual(code, 0, err)
            self.assertEqual(logs[0].read_bytes(), logs[1].read_bytes())
            rows = read_jsonl(logs[0])
        self.assertEqual([row["phase"] for row in events(rows, "phase_start")],
                         ["gather", "quan", "shop"])
        plan = self.tuning["day_plan"][0]
        self.assertEqual([row["data"] for row in events(rows, "day_plan")],
                         [{key: plan[key] for key in ("dishes", "ingredients")}])
        self.assertEqual(rows[-1]["reason"], "days_complete")
        self.assertEqual(rows[-1]["days_completed"], 1)

    def test_day_cli_rejects_invalid_day_counts_before_writing(self):
        with Workdir() as tmp:
            log = Path(tmp.path("day.jsonl"))
            for mode, days in (("day", "0"), ("day", "6"), ("quan", "1")):
                with self.subTest(mode=mode, days=days):
                    code, err = run_headless(
                        "--mode", mode, "--days", days, "--seed", "1",
                        "--ticks", "0", "--out", str(log),
                    )
                    self.assertEqual(code, 2, err)
                    self.assertFalse(log.exists())
