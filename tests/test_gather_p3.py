"""Unit tests cho Phase 3 (Contract v1.2 — Độ tươi & kho cá thể trong Gather, Inventory, Scenario)."""

import json
import unittest

from chonoi.contract import load_contract
from chonoi.errors import BadInput
from chonoi.inputs import InputPlayer
from chonoi.inventory import read_inventory, validate_items, write_inventory
from chonoi.runner import Session
from chonoi.scenario import load_scenario
from helpers import Workdir, write_json


def run_gather(scenario=None, frames=None, ticks=1, seed=1):
    tuning = load_contract("game.contract.json")["tuning"]
    sess = Session("gather", tuning, scenario or {}, seed)
    player = InputPlayer(frames or [])
    all_events = []
    snaps = {0: sess.snapshot()}
    while sess.tick < ticks and not sess.done:
        inp = player.advance(sess.tick)
        all_events.extend(sess.step(inp))
        snaps[sess.tick] = sess.snapshot()
    return sess, snaps, all_events


def ev_by_name(events, name):
    return [e for e in events if e["name"] == name]


class FreshnessV12Tests(unittest.TestCase):
    def test_spoiled_at_exact_threshold_30_once(self):
        # Fixture chuẩn từ TICKET-03: fresh=30 -> ươn ở tick 1, chỉ phát spoiled 1 lần
        sc = {
            "hold": [{"id": "I1", "kind": "ca_linh", "fresh": 30}],
            "random_fish": False,
            "monsters": [],
        }
        _, snaps, events = run_gather(sc, ticks=3)
        spoiled = ev_by_name(events, "spoiled")
        self.assertEqual(len(spoiled), 1)
        self.assertEqual(spoiled[0]["tick"], 1)
        self.assertEqual(spoiled[0]["data"], {"item_id": "I1", "kind": "ca_linh", "location": "hold"})
        self.assertLess(snaps[1]["hold"][0]["fresh"], 30)

    def test_multiple_spoiled_emitted_in_id_order(self):
        sc = {
            "hold": [
                {"id": "I10", "kind": "ca_loc", "fresh": 30},
                {"id": "I2", "kind": "bong_sung", "fresh": 30},
            ],
            "random_fish": False,
            "monsters": [],
        }
        _, _, events = run_gather(sc, ticks=1)
        spoiled = ev_by_name(events, "spoiled")
        self.assertEqual([e["data"]["item_id"] for e in spoiled], ["I2", "I10"])

    def test_new_item_starts_at_100_and_decays_from_next_tick(self):
        sc = {
            "player": {"pos": [20, 0]},
            "nodes": [{"id": "N1", "kind": "bong_sung", "pos": [20, 0]}],
            "fish": [],
            "monsters": [],
            "random_fish": False,
        }
        fr = [{"tick": 0, "interact": True}, {"tick": 1, "interact": False}]
        _, snaps, _ = run_gather(sc, fr, ticks=121)
        # Tick 1 vừa hái: fresh = 100 (chưa hao ở tick hái)
        self.assertEqual(snaps[1]["hold"], [{"id": "I1", "kind": "bong_sung", "fresh": 100}])
        # Sau 120 tick (2 giây * 0.5/s = 1.0 điểm tươi): tick 121 fresh == 99 chính xác
        self.assertEqual(snaps[121]["hold"][0]["fresh"], 99)

    def test_pause_freezes_freshness_decay(self):
        sc = {
            "hold": [{"id": "I1", "kind": "ca_linh", "fresh": 30}],
            "random_fish": False,
            "monsters": [],
        }
        fr = [
            {"tick": 0, "pause": True},
            {"tick": 1, "pause": False},
            {"tick": 5, "pause": True},
        ]
        _, snaps, events = run_gather(sc, fr, ticks=6)
        self.assertEqual(snaps[1]["hold"][0]["fresh"], 30)
        self.assertEqual(snaps[5]["hold"][0]["fresh"], 30)
        # Tick 6 (resume ở frame tick 5): mới bắt đầu hao và phát spoiled
        spoiled = ev_by_name(events, "spoiled")
        self.assertEqual(len(spoiled), 1)
        self.assertEqual(spoiled[0]["tick"], 6)

    def test_monster_hit_and_faint_lost_are_individual_items_lifo(self):
        sc = {
            "player": {"pos": [60, 24], "hp": 1},
            "hold": [
                {"id": "I1", "kind": "ca_loc", "fresh": 100},
                {"id": "I2", "kind": "bong_sung", "fresh": 80},
                {"id": "I3", "kind": "ca_linh", "fresh": 50},
            ],
            "fish": [],
            "random_fish": False,
        }
        sess, _, events = run_gather(sc, ticks=5)
        self.assertTrue(sess.done)
        hit = ev_by_name(events, "monster_hit")[0]["data"]
        faint = ev_by_name(events, "faint")[0]["data"]
        end = ev_by_name(events, "gather_end")[0]["data"]
        self.assertEqual([it["id"] for it in hit["lost"]], ["I3"])
        self.assertEqual([it["id"] for it in faint["lost"]], ["I2", "I1"])
        self.assertEqual(end, {"reason": "fainted", "inventory": {"items": []}})

    def test_inventory_v12_roundtrip_and_rejects_old_count_schema(self):
        with Workdir() as w:
            # Kho đếm kiểu cũ bị từ chối mã 2 (BadInput)
            old_inv = write_json(w.path("old.json"), {"items": {"ca_loc": 1}})
            with self.assertRaises(BadInput):
                read_inventory(old_inv)
            with self.assertRaises(BadInput):
                validate_items({"ca_loc": 1})

            # Ghi & đọc lại giữ chính xác nhánh < 30 sau 1 bước gather từ 30
            sc = {
                "player": {"pos": [2, 0]},
                "hold": [{"id": "I2", "kind": "ca_linh", "fresh": 30}, {"id": "I1", "kind": "ca_loc", "fresh": 100}],
                "random_fish": False,
                "monsters": [],
            }
            sess, _, _ = run_gather(sc, [{"tick": 0, "interact": True}], ticks=1)
            inv_path = w.path("v12.json")
            write_inventory(inv_path, sess.sim.inventory_items())
            loaded = read_inventory(inv_path)
            self.assertEqual([it["id"] for it in loaded], ["I1", "I2"])
            self.assertLess(loaded[1]["fresh"], 30)
            self.assertGreater(loaded[0]["fresh"], 99.9)

    def test_scenario_rejects_old_string_hold_and_spoiled_reserved(self):
        tuning = load_contract("game.contract.json")["tuning"]
        with Workdir() as w:
            p1 = write_json(w.path("bad_hold.json"), {"gather": {"hold": ["ca_loc"]}})
            with self.assertRaises(BadInput):
                load_scenario(p1, "gather", tuning)
            p2 = write_json(w.path("bad_res.json"), {
                "quan": {
                    "stock": [{"id": "I1", "kind": "ca_loc", "fresh": 29}],
                    "customers": [{"id": "C1", "table_id": "T1", "reserved": ["I1"]}],
                }
            })
            with self.assertRaises(BadInput):
                load_scenario(p2, "quan", tuning)


if __name__ == "__main__":
    unittest.main()
