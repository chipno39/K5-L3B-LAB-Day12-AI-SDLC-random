"""Unit & integration tests cho Phase 2: --mode day, Shop (oxygen/hp), Pause/Resume (Contract v1.1)."""

import unittest

from chonoi.contract import load_contract
from chonoi.inputs import InputPlayer
from chonoi.runner import Session


def run_session(mode, scenario=None, frames=None, ticks=10, seed=1, days=1):
    tuning = load_contract("game.contract.json")["tuning"]
    sess = Session(mode, tuning, scenario or {}, seed, days=days)
    player = InputPlayer(frames or [])
    all_events = list(sess.init_events)
    snaps = {0: sess.snapshot()}
    while sess.tick < ticks and not sess.done:
        inp = player.advance(sess.tick)
        all_events.extend(sess.step(inp))
        snaps[sess.tick] = sess.snapshot()
    return sess, snaps, all_events


def ev_by_name(events, name):
    return [e for e in events if e["name"] == name]


class PauseTests(unittest.TestCase):
    def test_pause_freezes_sim_tick_and_resume_steps_immediately(self):
        sc = {"player": {"pos": [20, 10]}, "fish": [], "monsters": [], "random_fish": False}
        fr = [
            {"tick": 0, "pause": True},
            {"tick": 1, "pause": False, "interact": True},
            {"tick": 4, "pause": True},
            {"tick": 5, "pause": False},
        ]
        sess, snaps, events = run_session("gather", sc, fr, ticks=6)
        # Tick 1: vào pause (sim_tick=0, state=paused)
        self.assertEqual(snaps[1]["state"], "paused")
        self.assertEqual(snaps[1]["sim_tick"], 0)
        self.assertEqual(snaps[4]["sim_tick"], 0)
        # Tick 5 (frame tick 4): resumed + chạy ngay 1 bước gameplay -> sim_tick=1
        self.assertEqual(snaps[5]["state"], "playing")
        self.assertEqual(snaps[5]["sim_tick"], 1)
        self.assertEqual([e["name"] for e in events], ["paused", "resumed"])
        self.assertEqual(events[0]["tick"], 1)
        self.assertEqual(events[1]["tick"], 5)


class DayAndShopTests(unittest.TestCase):
    def test_day_1_full_cycle_dock_quan_shop_buy_and_apply_day_2(self):
        # Bắt đầu với money=200, earned=200; dock ở tick 0, quan chạy 1 tick hết giờ,
        # vào Shop mua oxygen cấp 1 (giá 200 -> còn 0) và đóng shop bằng shop_done -> sang Ngày 2 áp dụng oxy 45s (2700 tick)!
        sc = {
            "day": {"money": 200, "earned": 200},
            "gather": {"hold": ["ca_loc", "bong_sung", "bong_sung"], "random_fish": False, "monsters": []},
            "quan": {"time_left_ticks": 1, "random_customers": False},
        }
        fr = [
            {"tick": 0, "interact": True},                 # step 1: gather docked -> phase_start(quan)
            {"tick": 1, "interact": False},                # step 2: quan ends (time) -> phase_start(shop)
            {"tick": 2, "buy": "oxygen", "shop_done": True},  # step 3: buy oxygen lv1 trước shop_done -> sang Ngày 2
        ]
        sess, snaps, events = run_session("day", sc, fr, ticks=3, days=2)
        self.assertFalse(sess.done)
        self.assertEqual(sess.days_completed, 1)
        self.assertEqual(sess.day, 2)
        self.assertEqual(snaps[0]["day"], 1)
        self.assertEqual(snaps[0]["player"]["oxygen_max_ticks"], 1800)
        self.assertEqual(snaps[2]["phase"], "shop")
        self.assertEqual(snaps[2]["stock"], {"bong_sung": 2, "ca_loc": 1})
        # Ngày 2 đã áp dụng nâng cấp oxygen cấp 1 (45s = 2700 tick) và money giảm còn 0, earned vẫn 200
        self.assertEqual(snaps[3]["day"], 2)
        self.assertEqual(snaps[3]["phase"], "gather")
        self.assertEqual(snaps[3]["money"], 0)
        self.assertEqual(snaps[3]["earned"], 200)
        self.assertEqual(snaps[3]["active_upgrades"], {"oxygen": 1})
        self.assertEqual(snaps[3]["player"]["oxygen_max_ticks"], 2700)

        bought = ev_by_name(events, "bought")
        self.assertEqual(len(bought), 1)
        self.assertEqual(bought[0]["data"], {"upgrade": "oxygen", "level": 1, "price": 200, "money": 0})
        shop_end = ev_by_name(events, "shop_end")
        self.assertEqual(shop_end[0]["data"], {"reason": "done"})

    def test_day_completes_on_shop_timeout_and_buy_failed_funds(self):
        sc = {
            "day": {"money": 50, "earned": 50},
            "gather": {"random_fish": False, "monsters": []},
            "quan": {"time_left_ticks": 1, "random_customers": False},
        }
        fr = [
            {"tick": 0, "interact": True},
            {"tick": 1, "interact": False},
            {"tick": 2, "buy": "hp"},
            {"tick": 3, "buy": "unknown_item"},
        ]
        sess, snaps, events = run_session("day", sc, fr, ticks=700, days=1)
        self.assertTrue(sess.done)
        end = sess.end_row()
        self.assertEqual(end["reason"], "days_complete")
        self.assertEqual(end["days_completed"], 1)
        failed = ev_by_name(events, "buy_failed")
        self.assertEqual(len(failed), 2)
        self.assertEqual(failed[0]["data"], {"action": "hp", "reason": "funds"})
        self.assertEqual(failed[1]["data"], {"action": "unknown_item", "reason": "unknown"})
        self.assertEqual(ev_by_name(events, "shop_end")[0]["data"], {"reason": "time"})


if __name__ == "__main__":
    unittest.main()
