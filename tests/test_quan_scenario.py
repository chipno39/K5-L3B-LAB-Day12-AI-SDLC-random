"""Focused unit tests for implemented quan behavior and its scenario input contract."""

from helpers import item_units

import unittest

from chonoi.contract import load_contract
from chonoi.errors import BadInput
from chonoi.inputs import InputPlayer
from chonoi.runner import Session
from chonoi.scenario import load_scenario

from helpers import Workdir, write_json


class QuanSimulationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tuning = load_contract()["tuning"]

    def test_walk_reaches_contract_speed_and_respects_bounds(self):
        start_x = 8.0
        session = Session("quan", self.tuning, {"player": {"pos": [start_x, 5]}}, seed=1)
        inputs = InputPlayer([{"tick": 0, "move": [1, 0]}])

        for tick in range(6):
            session.step(inputs.advance(tick))
        after_ramp_x = session.sim.pos[0]
        for tick in range(6, 66):
            session.step(inputs.advance(tick))

        speed = self.tuning["quan"]["walk_speed"]
        # Compare 60 ticks after the six-tick ramp: contract speed * 1 second.
        self.assertAlmostEqual(session.sim.pos[0] - after_ramp_x, speed, places=6)
        self.assertEqual(session.sim.pos[1], 5)

    def test_player_is_clamped_at_room_edge_and_velocity_stops(self):
        session = Session(
            "quan", self.tuning,
            {"player": {"pos": [15.99, 5], "vel": [4, 0]}},
            seed=1,
        )
        session.step(InputPlayer([{"tick": 0, "move": [1, 0]}]).advance(0))

        self.assertEqual(session.sim.pos[0], self.tuning["quan"]["bounds"]["x"][1])
        self.assertEqual(session.sim.vel[0], 0)

    def test_default_shift_timer_uses_contract_duration(self):
        session = Session("quan", self.tuning, {}, seed=1)
        ticks = round(self.tuning["quan"]["duration_s"] * self.tuning["tick_hz"])
        self.assertEqual(session.snapshot()["time_left_ticks"], ticks)

    def test_shift_end_emits_time_event_once_at_last_tick(self):
        session = Session("quan", self.tuning, {"time_left_ticks": 1}, seed=1)
        inp = InputPlayer([])

        events = session.step(inp.advance(0))

        self.assertTrue(session.done)
        self.assertEqual(session.sim.reason, "time")
        self.assertEqual([event["name"] for event in events], ["quan_end"])
        self.assertEqual(events[0]["data"]["reason"], "time")


class QuanScenarioTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tuning = load_contract()["tuning"]

    def load_fixture(self, block):
        with Workdir() as workdir:
            path = write_json(workdir.path("scenario.json"), {"quan": block})
            return load_scenario(path, "quan", self.tuning)

    def test_valid_quan_fixture_accepts_stock_player_and_customer(self):
        fixture = {
            "player": {"pos": [8, 5], "vel": [0, 0]},
            "stock": item_units("ca_loc", "ca_loc", "bong_sung"),
            "customers": [{"id": "C1", "table_id": "T1"}],
            "time_left_ticks": 90,
        }

        self.assertEqual(self.load_fixture(fixture), fixture)

    def test_unknown_scenario_field_is_rejected(self):
        with self.assertRaises(BadInput):
            self.load_fixture({"debug": True})

    def test_player_position_outside_contract_bounds_is_rejected(self):
        with self.assertRaises(BadInput):
            self.load_fixture({"player": {"pos": [17, 5]}})

    def test_malformed_player_velocity_is_rejected(self):
        for vel in ([1], [1, True], [0, "fast"]):
            with self.subTest(vel=vel), self.assertRaises(BadInput):
                self.load_fixture({"player": {"vel": vel}})

    def test_invalid_stock_item_or_freshness_is_rejected(self):
        for stock in (item_units("mystery_item"), item_units("ca_loc", fresh=-1), item_units("ca_loc", fresh=True)):
            with self.subTest(stock=stock), self.assertRaises(BadInput):
                self.load_fixture({"stock": stock})

    def test_duplicate_customer_ids_and_table_assignments_are_rejected(self):
        cases = [
            {"customers": [
                {"id": "C1", "table_id": "T1"},
                {"id": "C1", "table_id": "T2"},
            ]},
            {"customers": [
                {"id": "C1", "table_id": "T1"},
                {"id": "C2", "table_id": "T1"},
            ]},
        ]
        for fixture, message in zip(cases, ("id trùng", "hai khách cùng bàn")):
            with self.subTest(fixture=fixture), self.assertRaisesRegex(BadInput, message):
                self.load_fixture(fixture)

    def test_time_left_must_be_integer_inside_shift(self):
        duration = int(self.tuning["quan"]["duration_s"] * 60)
        for value in (0, duration + 1, True, 1.5):
            with self.subTest(value=value), self.assertRaises(BadInput):
                self.load_fixture({"time_left_ticks": value})


if __name__ == "__main__":
    unittest.main()
