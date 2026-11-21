"""Unit tests cho luật Gather (Lát 1 & Lát 2 — PRD-0 mục E, F, G)."""

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


class GatherSlice1OxygenAndFaint(unittest.TestCase):
    def test_dive_and_surface_events(self):
        sc = {"player": {"pos": [20, 0.4]}}
        fr = [
            {"tick": 0, "move": [0, 1]},
            {"tick": 30, "move": [0, -1]},
        ]
        _, _, events = run_gather(sc, fr, ticks=80)
        dives = ev_by_name(events, "dive")
        surfaces = ev_by_name(events, "surface")
        self.assertEqual(len(dives), 1)
        self.assertGreater(dives[0]["data"]["pos"][1], 0.5)
        self.assertEqual(len(surfaces), 1)
        self.assertLessEqual(surfaces[0]["data"]["pos"][1], 0.5)

    def test_oxygen_empty_and_choke_at_t_plus_59(self):
        # Oxy = 1 ở dưới nước: tick 1 chạm 0 (oxygen_empty, zero_oxy_ticks=1),
        # tick 1+59 = 60 đạt 60 -> choke (-1 HP, zero_oxy_ticks=0).
        sc = {"player": {"pos": [20, 10], "oxygen_ticks": 1, "hp": 3, "zero_oxy_ticks": 0}}
        _, snaps, events = run_gather(sc, ticks=65)
        empties = ev_by_name(events, "oxygen_empty")
        chokes = ev_by_name(events, "choke")
        self.assertEqual(len(empties), 1)
        self.assertEqual(empties[0]["tick"], 1)
        self.assertEqual(empties[0]["data"], {"oxygen_ticks": 0})
        self.assertEqual(len(chokes), 1)
        self.assertEqual(chokes[0]["tick"], 60)
        self.assertEqual(chokes[0]["data"], {"hp": 2})
        self.assertEqual(snaps[60]["player"]["hp"], 2)
        self.assertEqual(snaps[60]["player"]["zero_oxy_ticks"], 0)

    def test_surface_on_choke_tick_prevents_choke_and_refills(self):
        # Đang ở sát mặt nước (d=0.51), zero_oxy_ticks=59, oxygen_ticks=0, bơi lên -> nổi lên đúng tick 1
        sc = {"player": {"pos": [20, 0.51], "vel": [0, -4.0], "oxygen_ticks": 0, "hp": 3, "zero_oxy_ticks": 59}}
        fr = [{"tick": 0, "move": [0, -1]}]
        _, snaps, events = run_gather(sc, fr, ticks=2)
        self.assertEqual(len(ev_by_name(events, "surface")), 1)
        self.assertEqual(len(ev_by_name(events, "choke")), 0)
        self.assertEqual(snaps[1]["player"]["hp"], 3)
        self.assertEqual(snaps[1]["player"]["oxygen_ticks"], 6)
        self.assertEqual(snaps[1]["player"]["zero_oxy_ticks"], 0)

    def test_faint_drops_hold_lifo_and_ends_with_empty_inventory(self):
        sc = {
            "player": {"pos": [20, 10], "oxygen_ticks": 0, "hp": 1, "zero_oxy_ticks": 59},
            "hold": ["ca_loc", "bong_sung", "ca_linh"],
        }
        sess, snaps, events = run_gather(sc, ticks=10)
        self.assertTrue(sess.done)
        self.assertEqual(sess.tick, 1)
        self.assertEqual(sess.sim.reason, "fainted")
        names = [e["name"] for e in events]
        self.assertEqual(names, ["choke", "faint", "gather_end"])
        faint = ev_by_name(events, "faint")[0]["data"]
        self.assertEqual(faint["cause"], "choke")
        self.assertEqual(faint["hp"], 0)
        self.assertEqual([it["kind"] for it in faint["lost"]], ["ca_linh", "bong_sung", "ca_loc"])
        end = ev_by_name(events, "gather_end")[0]["data"]
        self.assertEqual(end, {"reason": "fainted", "inventory": {"items": []}})
        self.assertEqual(snaps[1]["hold"], [])
        self.assertEqual(sess.sim.inventory_items(), [])


class GatherSlice2HarvestAndCatch(unittest.TestCase):
    def test_gather_nearest_tiebreak_by_id_and_regrow(self):
        sc = {
            "player": {"pos": [20, 0]},
            "nodes": [
                {"id": "N10", "kind": "bong_sung", "pos": [21, 0]},
                {"id": "N2", "kind": "bong_dien_dien", "pos": [19, 0]},
            ],
            "fish": [],
            "random_fish": False,
        }
        fr = [{"tick": 0, "interact": True}]
        _, snaps, events = run_gather(sc, fr, ticks=1201)
        gathers = ev_by_name(events, "gather")
        self.assertEqual(len(gathers), 1)
        self.assertEqual(gathers[0]["tick"], 1)
        self.assertEqual(gathers[0]["data"], {"node_id": "N2", "kind": "bong_dien_dien", "amount": 1})
        self.assertEqual([it["kind"] for it in snaps[1]["hold"]], ["bong_dien_dien"])
        regrows = ev_by_name(events, "node_regrown")
        self.assertEqual(len(regrows), 1)
        self.assertEqual(regrows[0]["tick"], 1201)
        self.assertEqual(regrows[0]["data"], {"node_id": "N2"})

    def test_gather_hold_full_keeps_node_ready(self):
        sc = {
            "player": {"pos": [20, 0]},
            "hold": ["ca_loc"] * 12,
            "nodes": [{"id": "N1", "kind": "bong_sung", "pos": [20, 0]}],
            "fish": [],
            "random_fish": False,
        }
        fr = [{"tick": 0, "interact": True}]
        _, snaps, events = run_gather(sc, fr, ticks=1)
        fulls = ev_by_name(events, "hold_full")
        self.assertEqual(len(fulls), 1)
        self.assertEqual(fulls[0]["data"], {"action": "gather", "node_id": "N1", "required": 1, "free": 0})
        self.assertTrue(snaps[1]["nodes"][0]["ready"])

    def test_dock_priority_over_gather(self):
        sc = {
            "player": {"pos": [2, 0]},
            "nodes": [{"id": "N1", "kind": "bong_sung", "pos": [2, 0]}],
            "fish": [],
            "random_fish": False,
        }
        fr = [{"tick": 0, "interact": True}]
        sess, _, events = run_gather(sc, fr, ticks=1)
        self.assertTrue(sess.done)
        self.assertEqual(sess.sim.reason, "docked")
        self.assertEqual(len(ev_by_name(events, "gather")), 0)

    def test_catch_underwater_tiebreak_and_cooldown(self):
        sc = {
            "player": {"pos": [20, 10]},
            "nodes": [],
            "fish": [
                {"id": "F10", "kind": "ca_loc", "pos": [21, 10]},
                {"id": "F2", "kind": "ca_linh", "pos": [19, 10]},
            ],
        }
        # Catch lần 1 ở tick 0 (event tick 1, cd=30 -> dùng lại được ở step 30 -> event tick 31)
        # Thử catch ở tick 29 (đang hồi -> bỏ qua), rồi tick 30 (hết hồi -> bắt F10)
        fr = [
            {"tick": 0, "catch": True},
            {"tick": 1, "catch": False},
            {"tick": 29, "catch": True},
            {"tick": 30, "catch": False},
            {"tick": 31, "catch": True},
        ]
        _, snaps, events = run_gather(sc, fr, ticks=33)
        caught = ev_by_name(events, "fish_caught")
        self.assertEqual(len(caught), 2)
        self.assertEqual(caught[0]["tick"], 1)
        self.assertEqual(caught[0]["data"], {"fish_id": "F2", "kind": "ca_linh", "yield": 3})
        self.assertEqual(caught[1]["tick"], 32)
        self.assertEqual(caught[1]["data"], {"fish_id": "F10", "kind": "ca_loc", "yield": 1})
        self.assertEqual([it["kind"] for it in snaps[32]["hold"]], ["ca_linh", "ca_linh", "ca_linh", "ca_loc"])

    def test_catch_cooldown_usable_at_exact_t_plus_L(self):
        sc = {
            "player": {"pos": [20, 10]},
            "nodes": [],
            "fish": [
                {"id": "F1", "kind": "ca_loc", "pos": [20, 10]},
                {"id": "F2", "kind": "ca_loc", "pos": [20, 10]},
            ],
        }
        # Bắt ở step 0 -> event tick 1, đặt cd=30. Ở step 30 (event tick 31 = 1 + 30) phải bắt được!
        fr = [
            {"tick": 0, "catch": True},
            {"tick": 1, "catch": False},
            {"tick": 30, "catch": True},
        ]
        _, _, events = run_gather(sc, fr, ticks=32)
        caught = ev_by_name(events, "fish_caught")
        self.assertEqual([e["tick"] for e in caught], [1, 31])

    def test_catch_hold_full_keeps_fish_and_no_cooldown(self):
        sc = {
            "player": {"pos": [20, 10]},
            "hold": ["ca_loc"] * 10,  # chỉ còn 2 ô trống
            "nodes": [],
            "fish": [
                {"id": "F1", "kind": "ca_linh", "pos": [20, 10]},  # cần 3 ô (gần hơn)
                {"id": "F2", "kind": "ca_loc", "pos": [21, 10]},   # cần 1 ô (không được thử)
            ],
        }
        fr = [{"tick": 0, "catch": True}]
        _, snaps, events = run_gather(sc, fr, ticks=1)
        self.assertEqual(len(ev_by_name(events, "fish_caught")), 0)
        fulls = ev_by_name(events, "hold_full")
        self.assertEqual(len(fulls), 1)
        self.assertEqual(fulls[0]["data"], {"action": "catch", "fish_id": "F1", "required": 3, "free": 2})
        self.assertEqual(snaps[1]["player"]["catch_cd_ticks"], 0)
        self.assertEqual(len(snaps[1]["fish"]), 2)

    def test_catch_ignored_at_surface(self):
        sc = {
            "player": {"pos": [20, 0.5]},
            "nodes": [],
            "fish": [{"id": "F1", "kind": "ca_loc", "pos": [20, 1.0]}],
        }
        fr = [{"tick": 0, "catch": True}]
        _, snaps, events = run_gather(sc, fr, ticks=1)
        self.assertEqual(events, [])
        self.assertEqual(len(snaps[1]["fish"]), 1)

    def test_last_tick_gather_included_in_time_end_inventory(self):
        sc = {
            "player": {"pos": [20, 0]},
            "time_left_ticks": 1,
            "nodes": [{"id": "N1", "kind": "bong_sung", "pos": [20, 0]}],
            "fish": [],
            "random_fish": False,
        }
        fr = [{"tick": 0, "interact": True}]
        sess, _, events = run_gather(sc, fr, ticks=5)
        self.assertTrue(sess.done)
        self.assertEqual([e["name"] for e in events], ["gather", "gather_end"])
        end = ev_by_name(events, "gather_end")[0]["data"]
        self.assertEqual(end, {"reason": "time", "inventory": {"items": [{"id": "I1", "kind": "bong_sung", "fresh": 100}]}})


if __name__ == "__main__":
    unittest.main()
