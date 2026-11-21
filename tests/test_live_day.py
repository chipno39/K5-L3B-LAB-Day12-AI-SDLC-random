"""Test lớp live ở chế độ `day` (màn chờ, pause, shop). Chỉ dành cho starter Python (cùng chỗ với test_live.py).

Màn chờ chỉ là lớp UI: khi đang hiện thì sim KHÔNG bước. Test dùng ca ngắn (time_left_ticks) để chạy nhanh.
"""

import json
import time
import unittest
import urllib.error
import urllib.request

from chonoi.contract import load_contract
from chonoi.live import LiveGame, LiveServer


def _get(url):
    with urllib.request.urlopen(url, timeout=5) as r:
        return json.loads(r.read())


def _post(url, obj=None):
    req = urllib.request.Request(url, data=json.dumps(obj or {}).encode(), method="POST",
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=5) as r:
            return r.status
    except urllib.error.HTTPError as e:
        e.close()
        return e.code


def _wait(base, pred, secs=5):
    deadline = time.time() + secs
    while time.time() < deadline:
        s = _get(base + "/state")
        if pred(s):
            return s
        time.sleep(0.02)
    raise AssertionError("hết giờ chờ; screen=%r phase=%r tick=%r" % (s.get("screen"), s.get("phase"), s.get("tick")))


class LiveDayTest(unittest.TestCase):
    def setUp(self):
        tuning = load_contract()["tuning"]
        scenario = {"gather": {"time_left_ticks": 5}, "quan": {"time_left_ticks": 5}}
        self.server = LiveServer(LiveGame("day", tuning, scenario, 1, days=1), port=0)
        self.server.start()
        self.base = f"http://127.0.0.1:{self.server.port}"

    def tearDown(self):
        self.server.stop()

    def test_toan_bo_vong_ngay(self):
        b = self.base
        s = _get(b + "/state")
        self.assertEqual((s["screen"], s["mode"], s["phase"], s["days_target"]), ("menu", "day", "gather", 1))
        self.assertIn("monsters", s)        # quái có trong snapshot gather v1.1
        self.assertIn("day_plan", s)
        t0 = s["tick"]
        time.sleep(0.3)
        self.assertEqual(_get(b + "/state")["tick"], t0, "menu: sim không được bước")

        self.assertEqual(_post(b + "/continue"), 200)
        self.assertEqual(_get(b + "/state")["screen"], "day_intro")
        time.sleep(0.2)
        self.assertEqual(_get(b + "/state")["tick"], t0, "giới thiệu ngày: sim vẫn đứng yên")

        _post(b + "/continue")
        s = _wait(b, lambda s: s["screen"] == "evening_intro")
        self.assertEqual(s["phase"], "quan")
        self.assertEqual(s["last_gather_end"]["reason"], "time")
        t1 = s["tick"]
        time.sleep(0.2)
        self.assertEqual(_get(b + "/state")["tick"], t1, "giới thiệu buổi tối: sim đứng yên")

        _post(b + "/continue")
        s = _wait(b, lambda s: s["screen"] == "day_result")
        self.assertEqual(s["phase"], "shop")
        self.assertIsNotNone(s["shop"])
        self.assertIn("day_stats", s)

        _post(b + "/continue")
        self.assertIsNone(_get(b + "/state")["screen"])
        self.assertEqual(_post(b + "/input", {"buy": "oxygen"}), 200)           # tiền 0: mua không đủ
        _wait(b, lambda s: any(e["name"] == "buy_failed" and e["data"]["reason"] == "funds" for e in s["events"]))
        self.assertEqual(_post(b + "/input", {"shop_done": True}), 200)
        s = _wait(b, lambda s: s["screen"] == "summary")
        self.assertTrue(s["finished"])
        self.assertEqual(s["reason"], "days_complete")

        _post(b + "/continue")            # tổng kết -> về menu (chơi lại)
        s = _get(b + "/state")
        self.assertEqual(s["screen"], "menu")
        self.assertEqual(s["tick"], 0)

    def test_pause_va_input_hop_le(self):
        b = self.base
        _post(b + "/continue"); _post(b + "/continue")
        _wait(b, lambda s: s["screen"] in ("evening_intro", None))
        self.assertEqual(_post(b + "/input", {"pause": True}), 200)
        self.assertEqual(_post(b + "/input", {"buy": ""}), 400)
        self.assertEqual(_post(b + "/input", {"buy": 5}), 400)
        self.assertEqual(_post(b + "/input", {"pause": "yes"}), 400)

    def test_restart_ve_menu(self):
        b = self.base
        _post(b + "/continue"); _post(b + "/continue")
        _wait(b, lambda s: s["screen"] == "evening_intro")
        self.assertEqual(_post(b + "/restart"), 200)
        s = _get(b + "/state")
        self.assertEqual((s["screen"], s["tick"], s["phase"]), ("menu", 0, "gather"))


if __name__ == "__main__":
    unittest.main()
