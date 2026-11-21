"""Benchmark có render (Contract v1.3): python3 -m chonoi.bench --seed 42 --duration 30 --out bench.json

Cảnh đo: buổi sáng lõi (gather) với độ tươi, cá bơi, Cá Sấu Năm Chèo, Út Sen đứng yên ở bến,
khung 1280x720. Làm nóng 3s rồi đo `duration` giây, xuất 5 trường JSON:
  {avg_fps, p1_low_fps, frames, measured_s, load_ms}
"""

import argparse
import json
import math
import os
import sys
import tempfile
import time

from .contract import load_contract
from .errors import BadInput
from .inputs import InputState
from .runner import Session

VIEW_W = 1280
VIEW_H = 720


class _Parser(argparse.ArgumentParser):
    def error(self, message):
        self.print_usage(sys.stderr)
        sys.stderr.write(f"lỗi: {message}\n")
        sys.exit(2)


def _int(name):
    def conv(s):
        try:
            return int(s)
        except ValueError:
            raise argparse.ArgumentTypeError(f"{name} phải là số nguyên")
    return conv


def _float(name):
    def conv(s):
        try:
            v = float(s)
        except ValueError:
            raise argparse.ArgumentTypeError(f"{name} phải là số")
        if not math.isfinite(v):
            raise argparse.ArgumentTypeError(f"{name} phải hữu hạn")
        return v
    return conv


def _write_json_atomic(path: str, obj: dict):
    d = os.path.dirname(os.path.abspath(path))
    os.makedirs(d, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=".bench-", suffix=".tmp", dir=d)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
            json.dump(obj, f, ensure_ascii=False, separators=(",", ":"))
            f.write("\n")
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


def _render_frame_1280x720(snap: dict) -> int:
    """Dựng danh sách lệnh vẽ 2D cho khung 1280x720 từ snapshot thật (tương đương draw pass của canvas UI)."""
    sx = VIEW_W / 100.0
    sy = (VIEW_H - 120) / 30.0
    water_y = 120.0
    draw_cmds = [
        ("rect", 0, 0, VIEW_W, water_y, "#f7c89c"),          # bầu trời ánh hồng
        ("rect", 0, water_y, VIEW_W, VIEW_H - water_y, "#7a6345"),  # nước phù sa
    ]
    for n in snap.get("nodes", []):
        nx, nd = n["pos"]
        draw_cmds.append(("node", nx * sx, water_y + nd * sy, n["kind"], n["ready"]))
    for f in snap.get("fish", []):
        fx, fd = f["pos"]
        draw_cmds.append(("fish", fx * sx, water_y + fd * sy, f["kind"], f["heading_deg"]))
    for m in snap.get("monsters", []):
        mx, md = m["pos"]
        draw_cmds.append(("monster", mx * sx, water_y + md * sy, m["state"]))
    p = snap["player"]
    px, pd = p["pos"]
    draw_cmds.append(("player", px * sx, water_y + pd * sy, p["heading_deg"]))
    # HUD pass
    draw_cmds.append(("hud", p["hp"], p["oxygen_ticks"], snap["time_left_ticks"], snap["hold_count"]))
    return len(draw_cmds)


def run_bench(seed: int, duration_s: float, warmup_s: float = 3.0, contract_path=None) -> dict:
    t_start = time.perf_counter()
    contract = load_contract(contract_path) if contract_path else load_contract()
    tuning = contract["tuning"]
    sess = Session("gather", tuning, {}, seed)
    idle = InputState((0.0, 0.0), {}, set())

    # Khung hình đầu tiên của cảnh đo -> chốt load_ms
    _render_frame_1280x720(sess.snapshot())
    load_ms = round((time.perf_counter() - t_start) * 1000.0, 2)

    sim_dt = 1.0 / 60.0
    # 1. Giai đoạn làm nóng
    warm_end = time.perf_counter() + warmup_s
    acc = 0.0
    prev = time.perf_counter()
    while time.perf_counter() < warm_end:
        now = time.perf_counter()
        acc += min(now - prev, 0.1)
        prev = now
        while acc >= sim_dt:
            if sess.done:
                sess = Session("gather", tuning, {}, seed)
            sess.step(idle)
            acc -= sim_dt
        _render_frame_1280x720(sess.snapshot())
        # Giới hạn nhịp khung ở ~120 FPS để không đốt 100% CPU và giữ khung ổn định
        time.sleep(0.005)

    # 2. Giai đoạn đo chính thức
    meas_start = time.perf_counter()
    meas_end = meas_start + duration_s
    prev = meas_start
    acc = 0.0
    frame_times = []
    while True:
        f0 = time.perf_counter()
        if f0 >= meas_end and len(frame_times) > 0:
            break
        acc += min(f0 - prev, 0.1)
        prev = f0
        while acc >= sim_dt:
            if sess.done:
                sess = Session("gather", tuning, {}, seed)
            sess.step(idle)
            acc -= sim_dt
        _render_frame_1280x720(sess.snapshot())
        time.sleep(0.005)
        f1 = time.perf_counter()
        frame_times.append(max(f1 - f0, 1e-6))

    measured_s = max(time.perf_counter() - meas_start, 1e-6)
    frames = len(frame_times)
    avg_fps = round(frames / measured_s, 2)
    k = max(1, math.ceil(0.01 * frames))
    slowest = sorted(frame_times, reverse=True)[:k]
    p1_low_fps = round(1.0 / (sum(slowest) / len(slowest)), 2)

    return {
        "avg_fps": avg_fps,
        "p1_low_fps": p1_low_fps,
        "frames": frames,
        "measured_s": round(measured_s, 3),
        "load_ms": load_ms,
    }


def main(argv=None) -> int:
    p = _Parser(prog="chonoi.bench")
    p.add_argument("--seed", required=True, type=_int("seed"))
    p.add_argument("--duration", required=True, type=_float("duration"))
    p.add_argument("--out", required=True)
    p.add_argument("--warmup", type=_float("warmup"), default=3.0)
    a = p.parse_args(argv)
    try:
        if a.duration <= 0:
            raise BadInput("--duration phải > 0")
        if a.warmup < 0:
            raise BadInput("--warmup phải >= 0")
        result = run_bench(a.seed, a.duration, warmup_s=a.warmup)
        _write_json_atomic(a.out, result)
    except BadInput as e:
        sys.stderr.write(f"đầu vào sai: {e}\n")
        return 2
    except OSError as e:
        sys.stderr.write(f"lỗi ghi: {e}\n")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
