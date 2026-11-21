"""Unit tests cho Phase 2 Gather (Contract v1.1): cá bơi/phản xạ/sinh theo lịch, Cá Sấu Năm Chèo, nâng cấp oxy/HP."""

import math
import unittest

from chonoi.contract import load_contract
from chonoi.inputs import InputPlayer
from chonoi.runner import Session


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


class GatherP2FishSwimAndSpawn(unittest.TestCase):
    def test_initial_8_distinct_fish_and_6_nodes_and_1_monster(self):
        _, snaps, _ = run_gather(ticks=0, seed=42)
        s0 = snaps[0]
        self.assertEqual(len(s0["fish"]), 8)
        pts = {tuple(f["pos"]) for f in s0["fish"]}
        self.assertEqual(len(pts), 8)
        self.assertEqual(len(s0["nodes"]), 6)
        self.assertEqual({n["kind"] for n in s0["nodes"]}, {"bong_dien_dien", "bong_sung", "keo_neo"})
        self.assertEqual([m["id"] for m in s0["monsters"]], ["M1"])

    def test_fish_swim_turn_and_reflect_boundary(self):
        # Đặt cá linh sát mép phải x=95.99 hướng 0° (+x) -> bước 1 phản xạ ngược lại hướng 180°
        sc = {
            "player": {"pos": [2, 0]},
            "fish": [{"id": "F1", "kind": "ca_linh", "pos": [95.99, 6.0], "heading_deg": 0.0, "age_ticks": 0}],
            "monsters": [],
            "random_fish": True,
        }
        _, snaps, _ = run_gather(sc, ticks=1, seed=7)
        f1 = snaps[1]["fish"][0]
        self.assertLessEqual(f1["pos"][0], 96.0)
        self.assertAlmostEqual(f1["pos"][0], 96.0 - (1.5 / 60.0 - 0.01), places=4)
        self.assertAlmostEqual(f1["heading_deg"], 180.0, places=3)
        self.assertEqual(f1["age_ticks"], 1)

    def test_fish_scheduled_spawn_at_360_and_cap_12(self):
        sc = {"player": {"pos": [2, 0]}, "monsters": []}
        _, snaps, events = run_gather(sc, ticks=360, seed=5)
        spawns = ev_by_name(events, "fish_spawned")
        self.assertEqual(len(spawns), 1)
        self.assertEqual(spawns[0]["tick"], 360)
        self.assertEqual(len(snaps[360]["fish"]), 9)

    def test_random_fish_false_freezes_fish_and_disables_spawn(self):
        sc = {
            "player": {"pos": [2, 0]},
            "fish": [{"id": "F1", "kind": "ca_keo", "pos": [50, 25], "heading_deg": 0.0}],
            "monsters": [],
            "random_fish": False,
        }
        _, snaps, events = run_gather(sc, ticks=365, seed=1)
        self.assertEqual(snaps[365]["fish"][0]["pos"], [50.0, 25.0])
        self.assertEqual(len(ev_by_name(events, "fish_spawned")), 0)

    def test_catch_ca_keo_yield_2_and_keo_neo_harvest(self):
        sc = {
            "player": {"pos": [50, 25]},
            "fish": [{"id": "F1", "kind": "ca_keo", "pos": [50, 25]}],
            "monsters": [],
            "random_fish": False,
        }
        _, snaps, events = run_gather(sc, [{"tick": 0, "catch": True}], ticks=1)
        caught = ev_by_name(events, "fish_caught")
        self.assertEqual(len(caught), 1)
        self.assertEqual(caught[0]["data"], {"fish_id": "F1", "kind": "ca_keo", "yield": 2})
        self.assertEqual(snaps[1]["hold"], ["ca_keo", "ca_keo"])


class GatherP2MonstersAndFaint(unittest.TestCase):
    def test_monster_patrol_chase_hit_recoil_and_invuln(self):
        # Đặt người chơi ở [60, 24] trùng vị trí M1 với 5 món trong giỏ -> hit mất 1 HP, mất floor(5/2)=2 món LIFO,
        # invuln=90, M1 vào recoil 60 bước theo +x (trùng tâm).
        sc = {
            "player": {"pos": [60, 24], "hp": 3},
            "hold": ["ca_loc", "bong_sung", "ca_linh", "ca_keo", "keo_neo"],
            "fish": [],
            "random_fish": False,
        }
        _, snaps, events = run_gather(sc, ticks=65)
        hits = ev_by_name(events, "monster_hit")
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0]["tick"], 1)
        self.assertEqual(hits[0]["data"]["monster_id"], "M1")
        self.assertEqual(hits[0]["data"]["hp"], 2)
        self.assertEqual(hits[0]["data"]["lost"], ["keo_neo", "ca_keo"])
        self.assertEqual(snaps[1]["hold"], ["ca_loc", "bong_sung", "ca_linh"])
        self.assertEqual(snaps[1]["player"]["invuln_ticks"], 90)
        m1_t1 = snaps[1]["monsters"][0]
        self.assertEqual(m1_t1["state"], "recoil")
        self.assertEqual(m1_t1["state_ticks_left"], 60)
        self.assertEqual(m1_t1["recoil_dir"], [1.0, 0.0])
        # Sau 60 bước recoil (tại tick 61), M1 về patrol và đã lùi ~2m theo +x
        m1_t61 = snaps[61]["monsters"][0]
        self.assertEqual(m1_t61["state"], "patrol")
        self.assertAlmostEqual(m1_t61["pos"][0], 62.0, places=2)

    def test_monster_hit_causes_faint_with_remaining_hold_lifo(self):
        sc = {
            "player": {"pos": [60, 24], "hp": 1},
            "hold": ["ca_loc", "bong_sung", "ca_linh"],
            "fish": [],
            "random_fish": False,
        }
        sess, snaps, events = run_gather(sc, ticks=5)
        self.assertTrue(sess.done)
        self.assertEqual(sess.tick, 1)
        self.assertEqual([e["name"] for e in events], ["monster_hit", "faint", "gather_end"])
        # floor(3/2)=1 mất lúc hit ("ca_linh"), còn 2 món mất LIFO lúc faint (["bong_sung", "ca_loc"])
        self.assertEqual(events[0]["data"]["lost"], ["ca_linh"])
        self.assertEqual(events[1]["data"], {"cause": "monster", "lost": ["bong_sung", "ca_loc"], "hp": 0})
        self.assertEqual(events[2]["data"], {"reason": "fainted", "inventory": {"items": {}}})
        self.assertEqual(snaps[1]["hold"], [])

    def test_monster_ignores_player_above_depth_10(self):
        sc = {
            "player": {"pos": [60, 9.5], "hp": 3},
            "monsters": [
                {"id": "M1", "kind": "ca_sau", "pos": [60, 10.5], "waypoints": [[60, 10.5], [64, 10.5]]}
            ],
            "fish": [],
            "random_fish": False,
        }
        _, snaps, events = run_gather(sc, ticks=5)
        self.assertEqual(len(ev_by_name(events, "monster_hit")), 0)
        self.assertEqual(snaps[5]["monsters"][0]["state"], "patrol")

    def test_choke_pierces_invuln_and_keeps_hold(self):
        sc = {
            "player": {"pos": [20, 10], "oxygen_ticks": 0, "hp": 2, "zero_oxy_ticks": 59, "invuln_ticks": 50},
            "hold": ["ca_loc", "bong_sung"],
            "monsters": [],
            "fish": [],
            "random_fish": False,
        }
        _, snaps, events = run_gather(sc, ticks=1)
        self.assertEqual(len(ev_by_name(events, "choke")), 1)
        self.assertEqual(snaps[1]["player"]["hp"], 1)
        self.assertEqual(snaps[1]["hold"], ["ca_loc", "bong_sung"])


if __name__ == "__main__":
    unittest.main()
