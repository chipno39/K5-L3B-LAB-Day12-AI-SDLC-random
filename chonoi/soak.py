"""Soak headless (Contract v1.3): python3 -m chonoi.soak --seed 7 --days 10 --out soak.json

Chạy N Ngày liên tiếp (mặc định 10 Ngày, lặp kế hoạch D1-D5 ở Ngày 6-10) trong một tiến trình
bằng bot tất định, giữ tiền/earned/uy tín/nâng cấp/id cá thể xuyên suốt.
Xuất soak.json: {days, days_completed, crashes, results: [{day, earned, reputation, score}], duration_s}.
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


def _write_json_atomic(path: str, obj: dict):
    d = os.path.dirname(os.path.abspath(path))
    os.makedirs(d, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=".soak-", suffix=".tmp", dir=d)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
            json.dump(obj, f, ensure_ascii=False, separators=(",", ":"))
            f.write("\n")
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


def _bot_input(sess: Session, tick_in_phase: int) -> InputState:
    """Bot tất định: buổi sáng bơi hái N1 rồi cập bến; tối đứng gần bếp/bàn tương tác; Shop mua nâng cấp rồi đóng."""
    phase = sess.phase
    move = (0.0, 0.0)
    edges = set()
    buy = None

    if phase == "gather":
        sim = sess.sim
        px, pd = sim.pos
        # Nếu đã có hàng trong giỏ thì quay về bến [2, 0] và bấm interact để cập bến
        if len(sim.hold) >= 2:
            if math.dist(sim.pos, sim.t["dock_pos"]) <= sim.t["dock_radius"]:
                edges.add("interact")
            else:
                move = (-1.0, 0.0) if px > 2.5 else (0.0, -1.0 if pd > 0.2 else 0.0)
        else:
            # Bơi tới N1 ([12, 0]) hái 1 lần rồi N2 hoặc về bến sớm
            target_x = 12.0 if len(sim.hold) == 0 else 28.0
            if tick_in_phase >= 600:
                if math.dist(sim.pos, sim.t["dock_pos"]) <= sim.t["dock_radius"]:
                    edges.add("interact")
                else:
                    move = (-1.0, 0.0)
            elif abs(px - target_x) <= 1.5 and pd <= 0.5:
                edges.add("interact")
            else:
                move = (1.0 if px < target_x else -1.0, 0.0)
    elif phase == "quan":
        # Đứng yên hoặc tương tác định kỳ; ca tối kết thúc tự nhiên theo timer
        if tick_in_phase % 60 == 30:
            edges.add("interact")
    elif phase == "shop":
        # Thử mua nâng cấp nếu đủ tiền ở tick đầu của Shop, sau đó đóng Shop ngay
        if tick_in_phase == 0:
            if sess.upgrades.get("oxygen", 0) < 2 and sess.money >= 200:
                buy = "oxygen"
            elif sess.upgrades.get("hp", 0) < 2 and sess.money >= 250:
                buy = "hp"
            edges.add("shop_done")
        else:
            edges.add("shop_done")

    return InputState(move, {}, edges, buy=buy)


def run_soak(seed: int, days: int, contract_path=None) -> dict:
    t0 = time.perf_counter()
    contract = load_contract(contract_path) if contract_path else load_contract()
    tuning = contract["tuning"]
    sess = Session("day", tuning, {}, seed, days=days)

    results = []
    crashes = 0
    last_phase = sess.phase
    tick_in_phase = 0
    max_steps = days * 25_000  # trần an toàn tránh lặp vô hạn

    try:
        steps = 0
        while not sess.done and steps < max_steps:
            if sess.phase != last_phase:
                last_phase = sess.phase
                tick_in_phase = 0
            inp = _bot_input(sess, tick_in_phase)
            day_before = sess.day
            events = sess.step(inp)
            tick_in_phase += 1
            steps += 1
            for ev in events:
                if ev["name"] == "shop_end":
                    snap = sess.snapshot()
                    results.append({
                        "day": day_before,
                        "earned": snap["earned"],
                        "reputation": round(float(snap["reputation"]), 3),
                        "score": snap["score"],
                    })
    except Exception:
        crashes += 1

    duration_s = round(time.perf_counter() - t0, 3)
    return {
        "days": days,
        "days_completed": sess.days_completed,
        "crashes": crashes,
        "results": results,
        "duration_s": duration_s,
    }


def main(argv=None) -> int:
    p = _Parser(prog="chonoi.soak")
    p.add_argument("--seed", required=True, type=_int("seed"))
    p.add_argument("--days", required=True, type=_int("days"))
    p.add_argument("--out", required=True)
    a = p.parse_args(argv)
    try:
        if a.days < 1:
            raise BadInput("--days phải >= 1")
        result = run_soak(a.seed, a.days)
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
