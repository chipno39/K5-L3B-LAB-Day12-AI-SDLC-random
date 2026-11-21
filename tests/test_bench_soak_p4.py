"""Unit tests cho Phase 4 (Contract v1.3): bench_cmd và soak_cmd."""

import json
import unittest

from chonoi.bench import main as bench_main
from chonoi.soak import main as soak_main
from helpers import Workdir


class BenchAndSoakV13Tests(unittest.TestCase):
    def test_bench_outputs_five_required_fields(self):
        with Workdir() as w:
            out = w.path("bench.json")
            code = bench_main(["--seed", "42", "--duration", "0.2", "--warmup", "0.05", "--out", out])
            self.assertEqual(code, 0)
            with open(out, encoding="utf-8") as f:
                data = json.load(f)
            self.assertEqual(set(data.keys()), {"avg_fps", "p1_low_fps", "frames", "measured_s", "load_ms"})
            self.assertGreater(data["frames"], 0)
            self.assertGreater(data["avg_fps"], 0)
            self.assertGreater(data["p1_low_fps"], 0)
            self.assertGreaterEqual(data["load_ms"], 0)

    def test_soak_10_days_deterministic_and_zero_crashes(self):
        with Workdir() as w:
            o1, o2 = w.path("s1.json"), w.path("s2.json")
            self.assertEqual(soak_main(["--seed", "7", "--days", "10", "--out", o1]), 0)
            self.assertEqual(soak_main(["--seed", "7", "--days", "10", "--out", o2]), 0)
            with open(o1, encoding="utf-8") as f1, open(o2, encoding="utf-8") as f2:
                d1, d2 = json.load(f1), json.load(f2)
            self.assertEqual(d1["days"], 10)
            self.assertEqual(d1["days_completed"], 10)
            self.assertEqual(d1["crashes"], 0)
            self.assertEqual(len(d1["results"]), 10)
            self.assertEqual([r["day"] for r in d1["results"]], list(range(1, 11)))
            # So tính lặp lại ở các trường gameplay, bỏ duration_s
            self.assertEqual(d1["results"], d2["results"])


if __name__ == "__main__":
    unittest.main()
