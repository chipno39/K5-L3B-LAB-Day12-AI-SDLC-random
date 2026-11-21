"""Nạp và kiểm scenario (Contract D). Trả về dict của đúng khối theo mode.

KHUNG: kiểm cú pháp, id trùng, bộ đếm âm, khoang vượt sức chứa, trường lạ.
TODO(nhóm): bổ sung kiểm mâu thuẫn mức luật mà nhóm cần (khách giữ chỗ quá kho, đơn assigned
phải có đúng một món, khách eating thiếu giá/tip...) — xem PRD-0 mục D và 'Mâu thuẫn -> mã 2'.
"""

import json

from .errors import BadInput
from .inventory import KINDS_V11, validate_items

GATHER_KEYS = {"player", "hold", "nodes", "fish", "monsters", "random_fish", "time_left_ticks"}
GATHER_PLAYER_KEYS = {"pos", "vel", "heading_deg", "hp", "oxygen_ticks", "zero_oxy_ticks",
                      "invuln_ticks", "catch_cd_ticks"}
NODE_KINDS = ("bong_dien_dien", "bong_sung", "keo_neo")
FISH_KINDS = ("ca_linh", "ca_loc", "ca_keo")
MONSTER_STATES = ("patrol", "chase", "recoil", "stunned")
QUAN_PLAYER_KEYS = {"pos", "vel"}
QUAN_KEYS = {"player", "stock", "hand", "stoves", "tables", "customers", "random_customers",
             "reputation", "time_left_ticks"}
DAY_KEYS = {"money", "earned", "reputation", "upgrades", "day_plan"}


def _check_ids(name, arr):
    if not isinstance(arr, list):
        raise BadInput(f"{name} phải là mảng")
    seen = set()
    for e in arr:
        if not isinstance(e, dict) or not isinstance(e.get("id"), str) or not e["id"]:
            raise BadInput(f"{name}: mỗi phần tử cần id (chuỗi khác rỗng)")
        if e["id"] in seen:
            raise BadInput(f"{name}: id trùng {e['id']}")
        seen.add(e["id"])


def load_scenario(path, mode: str, tuning: dict) -> dict:
    if path is None:
        return {}
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError) as e:
        raise BadInput(f"không đọc được scenario {path}: {e}")
    if not isinstance(data, dict) or not set(data) <= {"gather", "quan", "day"}:
        raise BadInput("scenario chỉ được có khối 'gather', 'quan' hoặc 'day'")
    if mode == "day":
        out = {}
        if "day" in data:
            if not isinstance(data["day"], dict):
                raise BadInput("khối day phải là object")
            _validate_day(data["day"], tuning)
            out["day"] = data["day"]
        if "gather" in data:
            if not isinstance(data["gather"], dict):
                raise BadInput("khối gather phải là object")
            _validate_mode_block(data["gather"], "gather", tuning)
            out["gather"] = data["gather"]
        if "quan" in data:
            if not isinstance(data["quan"], dict):
                raise BadInput("khối quan phải là object")
            if "stock" in data["quan"] or "reputation" in data["quan"]:
                raise BadInput("cấm khai quan.stock và quan.reputation khi chạy --mode day")
            _validate_mode_block(data["quan"], "quan", tuning)
            out["quan"] = data["quan"]
        return out
    if set(data) - {mode}:
        raise BadInput(f"khối sai mode: chạy --mode {mode} chỉ nhận khối '{mode}'")
    block = data.get(mode, {})
    if not isinstance(block, dict):
        raise BadInput(f"khối {mode} phải là object")
    _validate_mode_block(block, mode, tuning)
    return block


def _validate_mode_block(block: dict, mode: str, tuning: dict):
    allowed = GATHER_KEYS if mode == "gather" else QUAN_KEYS
    extra = set(block) - allowed
    if extra:
        raise BadInput(f"trường lạ/chưa hỗ trợ trong {mode}: {sorted(extra)}")
    dur = int(round(tuning[mode]["duration_s"] * 60))
    if "time_left_ticks" in block:
        t = block["time_left_ticks"]
        if isinstance(t, bool) or not isinstance(t, int) or not (1 <= t <= dur):
            raise BadInput(f"time_left_ticks phải là số nguyên trong [1, {dur}]")
    if mode == "gather":
        _validate_gather(block, tuning)
    else:
        _validate_quan(block, tuning)


def _validate_day(d: dict, tuning: dict):
    extra = set(d) - DAY_KEYS
    if extra:
        raise BadInput(f"trường lạ/chưa hỗ trợ trong day: {sorted(extra)}")
    money = d.get("money", 0)
    earned = d.get("earned", 0)
    if ("money" in d) != ("earned" in d) and (money != 0 or earned != 0):
        raise BadInput("khi có tiền đầu kỳ phải khai cả money và earned")
    _nonneg_int("day.money", money)
    _nonneg_int("day.earned", earned)
    if money > earned:
        raise BadInput("day.money không được lớn hơn day.earned")
    if "reputation" in d:
        rep = d["reputation"]
        q = tuning["quan"]
        if not _num(rep) or not (q["reputation_min"] <= rep <= q["reputation_max"]):
            raise BadInput("day.reputation ngoài dải hợp lệ")
    if "upgrades" in d:
        u = d["upgrades"]
        if not isinstance(u, dict):
            raise BadInput("day.upgrades phải là object")
        shop_ups = tuning.get("shop", {}).get("upgrades", {})
        for k, lvl in u.items():
            if k not in shop_ups:
                raise BadInput(f"day.upgrades: loại nâng cấp không hợp lệ {k!r}")
            _nonneg_int(f"day.upgrades.{k}", lvl)
            if lvl > len(shop_ups[k]):
                raise BadInput(f"day.upgrades.{k} vượt cấp tối đa")
    if "day_plan" in d:
        dp = d["day_plan"]
        if not isinstance(dp, list):
            raise BadInput("day.day_plan phải là mảng")
        menu = tuning["menu"]
        for item in dp:
            if not isinstance(item, dict) or not isinstance(item.get("day"), int) or not (1 <= item["day"] <= 5):
                raise BadInput("day.day_plan: mỗi mục cần day nguyên trong [1, 5]")
            dishes = item.get("dishes")
            if not isinstance(dishes, dict) or not dishes:
                raise BadInput("day.day_plan: mỗi mục cần dishes không rỗng")
            calc = {}
            for did, cnt in dishes.items():
                if did not in menu:
                    raise BadInput(f"day.day_plan: món lạ {did!r}")
                if isinstance(cnt, bool) or not isinstance(cnt, int) or cnt <= 0:
                    raise BadInput(f"day.day_plan: số suất {did} phải nguyên dương")
                for ing, qty in menu[did]["recipe"].items():
                    calc[ing] = calc.get(ing, 0) + qty * cnt
            if "ingredients" in item and item["ingredients"] != calc:
                raise BadInput("day.day_plan: ingredients không khớp tổng công thức × số suất")


def _num(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _nonneg_int(name, v):
    if isinstance(v, bool) or not isinstance(v, int) or v < 0:
        raise BadInput(f"{name} phải là số nguyên không âm")


def _pos(name, pos, bounds, axes=("x", "d")):
    if not (isinstance(pos, list) and len(pos) == 2 and all(_num(c) for c in pos)):
        raise BadInput(f"{name} phải là [{axes[0]}, {axes[1]}]")
    for c, axis in zip(pos, axes):
        lo, hi = bounds[axis]
        if not (lo <= c <= hi):
            raise BadInput(f"{name} nằm ngoài vùng nước ({axis} ∈ [{lo}, {hi}])")


def _validate_gather(b, tuning):
    g = tuning["gather"]
    bounds = g["bounds"]
    for arr in ("nodes", "fish", "monsters"):
        if arr in b:
            _check_ids(arr, b[arr])
    if "random_fish" in b and not isinstance(b["random_fish"], bool):
        raise BadInput("random_fish phải là boolean")
    if "hold" in b:
        h = validate_items(b["hold"], KINDS_V11)
        if len(h) > g["hold_capacity"]:
            raise BadInput("hold vượt sức chứa")
    p = b.get("player", {})
    if not isinstance(p, dict):
        raise BadInput("player phải là object")
    extra = set(p) - GATHER_PLAYER_KEYS
    if extra:
        raise BadInput(f"trường lạ/chưa hỗ trợ trong gather.player: {sorted(extra)}")
    if "pos" in p:
        _pos("player.pos", p["pos"], bounds)
    if "vel" in p and not (isinstance(p["vel"], list) and len(p["vel"]) == 2 and all(_num(c) for c in p["vel"])):
        raise BadInput("player.vel phải là [x, d]")
    if "heading_deg" in p and not _num(p["heading_deg"]):
        raise BadInput("player.heading_deg phải là số")
    for key in ("invuln_ticks", "catch_cd_ticks", "zero_oxy_ticks", "oxygen_ticks", "hp"):
        if key in p:
            _nonneg_int(f"player.{key}", p[key])
    omax = int(round(g["oxygen_max_s"] * 60))
    if "oxygen_ticks" in p and p["oxygen_ticks"] > omax:
        raise BadInput("player.oxygen_ticks vượt oxy tối đa")
    if "hp" in p and not (1 <= p["hp"] <= g["hp_max"]):
        raise BadInput("player.hp phải trong [1, hp_max]")
    if "zero_oxy_ticks" in p:
        pos = p.get("pos", g["start_pos"])
        oxy = p.get("oxygen_ticks", omax)
        if p["zero_oxy_ticks"] > 59:
            raise BadInput("player.zero_oxy_ticks phải trong [0, 59]")
        if p["zero_oxy_ticks"] > 0 and not (oxy == 0 and pos[1] > g["surface_depth"]):
            raise BadInput("player.zero_oxy_ticks > 0 chỉ khi oxy = 0 và đang dưới nước")
    for n in b.get("nodes", []):
        if n.get("kind") not in NODE_KINDS:
            raise BadInput(f"nodes.{n['id']}: kind phải là một trong {NODE_KINDS}")
        _pos(f"nodes.{n['id']}.pos", n.get("pos"), bounds)
        if n["pos"][1] != 0:
            raise BadInput(f"nodes.{n['id']}: nút hái nằm ở mặt nước (d = 0)")
        if "regrow_ticks" in n:
            _nonneg_int(f"nodes.{n['id']}.regrow_ticks", n["regrow_ticks"])
    for f in b.get("fish", []):
        if f.get("kind") not in FISH_KINDS:
            raise BadInput(f"fish.{f['id']}: kind phải là một trong {FISH_KINDS}")
        _pos(f"fish.{f['id']}.pos", f.get("pos"), bounds)
        if f["pos"][1] <= g["surface_depth"]:
            raise BadInput(f"fish.{f['id']}: đàn cá phải ở dưới nước")
        if "heading_deg" in f and not _num(f["heading_deg"]):
            raise BadInput(f"fish.{f['id']}.heading_deg phải là số")
        if "age_ticks" in f:
            _nonneg_int(f"fish.{f['id']}.age_ticks", f["age_ticks"])
    species = g.get("monsters", {}).get("species", {})
    for m in b.get("monsters", []):
        if m.get("kind") not in species:
            raise BadInput(f"monsters.{m['id']}: kind không hợp lệ {m.get('kind')!r}")
        _pos(f"monsters.{m['id']}.pos", m.get("pos"), bounds)
        wps = m.get("waypoints")
        if not isinstance(wps, list) or len(wps) != 2:
            raise BadInput(f"monsters.{m['id']}: waypoints phải có đúng 2 điểm")
        for idx, wp in enumerate(wps):
            _pos(f"monsters.{m['id']}.waypoints[{idx}]", wp, bounds)
        tidx = m.get("target_idx", 1)
        if tidx not in (0, 1) or isinstance(tidx, bool):
            raise BadInput(f"monsters.{m['id']}: target_idx phải là 0 hoặc 1")
        st = m.get("state", "patrol")
        if st not in MONSTER_STATES:
            raise BadInput(f"monsters.{m['id']}: state không hợp lệ {st!r}")
        stl = m.get("state_ticks_left", 0)
        _nonneg_int(f"monsters.{m['id']}.state_ticks_left", stl)
        if st in ("recoil", "stunned") and stl <= 0:
            raise BadInput(f"monsters.{m['id']}: trạng thái {st} cần state_ticks_left > 0")
        rdir = m.get("recoil_dir")
        if st == "recoil":
            if not (isinstance(rdir, list) and len(rdir) == 2 and all(_num(c) for c in rdir)):
                raise BadInput(f"monsters.{m['id']}: recoil cần recoil_dir [dx, dd]")
        elif rdir is not None:
            raise BadInput(f"monsters.{m['id']}: recoil_dir phải là null ngoài trạng thái recoil")


def _validate_quan(b, tuning):
    for arr in ("stoves", "tables", "customers"):
        if arr in b:
            _check_ids(arr, b[arr])
    stock_by_id = None
    if "stock" in b:
        items = validate_items(b["stock"], KINDS_V11)
        stock_by_id = {it["id"]: it for it in items}
    p = b.get("player", {})
    if not isinstance(p, dict) or set(p) - QUAN_PLAYER_KEYS:
        raise BadInput("quan.player chỉ có pos và vel")
    qb = tuning["quan"]["bounds"]
    if "pos" in p:
        _pos("player.pos", p["pos"], qb, axes=("x", "z"))
    if "vel" in p and not (isinstance(p["vel"], list) and len(p["vel"]) == 2 and all(_num(c) for c in p["vel"])):
        raise BadInput("player.vel phải là [x, z]")
    table_ids = [c.get("table_id") for c in b.get("customers", [])]
    known = {t["id"] for t in tuning["quan"]["tables"]} | {t.get("id") for t in b.get("tables", [])}
    spoiled_below = tuning.get("freshness", {}).get("spoiled_below", 30)
    used_reserved = set()
    for c in b.get("customers", []):
        if not isinstance(c.get("table_id"), str) or c["table_id"] not in known:
            raise BadInput(f"customers.{c['id']}: table_id phải là bàn có thật")
        if "reserved" in c and c["reserved"] is not None:
            res = c["reserved"]
            if not isinstance(res, list) or any(not isinstance(x, str) or not x for x in res):
                raise BadInput(f"customers.{c['id']}.reserved phải là mảng id cá thể (v1.2)")
            if len(res) != len(set(res)):
                raise BadInput(f"customers.{c['id']}.reserved có id trùng")
            for iid in res:
                if iid in used_reserved:
                    raise BadInput(f"customers.{c['id']}.reserved dùng chung id {iid!r} với đơn khác")
                used_reserved.add(iid)
                if stock_by_id is not None:
                    if iid not in stock_by_id:
                        raise BadInput(f"customers.{c['id']}.reserved trỏ tới id không có trong stock: {iid!r}")
                    if stock_by_id[iid]["fresh"] < spoiled_below:
                        raise BadInput(f"customers.{c['id']}.reserved trỏ tới cá thể đã ươn: {iid!r}")
    if len(table_ids) != len(set(table_ids)):
        raise BadInput("hai khách cùng bàn")
