"""Buổi sáng — Lặn & Hái (`gather`, Test Contract v1.1).

Mặt cắt dòng sông nhìn NGANG: vị trí `[x, d]` (x sang phải, `d` độ sâu hướng xuống, d = 0 là mặt nước).
`move = [x, d]`: thành phần thứ hai DƯƠNG = bơi xuống. Hướng mặt là góc từ +x, dương = xuống.

Thứ tự xử lý một bước (TICKET-02 mục 4.5):
  1. Đồng hồ (`phase_tick`, `time_left_ticks`), cooldown bắt cá, giảm bất tử (`invuln_ticks`), hồi nút (`node_regrown`).
  2. Bơi, chặn biên, `dive`/`surface`, oxy, `oxygen_empty`, ngạt (`choke`, xuyên bất tử, không rơi hàng); Máu 0 -> `faint("choke")` + `gather_end("fainted")`.
  3. Cập nhật quái (`monsters`) theo id rồi xét tối đa một `monster_hit` -> `recoil`; Máu 0 -> `faint("monster")` + `gather_end("fainted")`.
  4. `interact`: bến trước (`docked`), rồi hái nút mặt nước (`gather`/`hold_full`).
  5. `catch`: bắt cá theo vị trí cá trước khi bơi (`fish_caught`/`hold_full`).
  6. Xét hết giờ (`time_left_ticks == 0` -> `gather_end("time")`).
  7. Nếu còn giờ và `random_fish` bật: cá bơi (đổi hướng bước 120, 240..., phản xạ mép), sau đó sinh cá theo lịch `phase_tick = 360*k` (`fish_spawned`).
"""

from fractions import Fraction
import math

from ..ids import id_key, sort_by_id
from ..inventory import fresh_frac, fresh_num, hold_to_items
from .ramp import ramp_velocity

TICK = 60.0
AXES = ("x", "d")


class GatherSim:
    mode = "gather"
    phase = "gather"

    def __init__(self, tuning, scenario, streams, ids, day_num=1, active_upgrades=None, item_ids=None):
        t = tuning["gather"]
        self.t = t
        self.tuning = tuning
        self.rng = streams
        self.ids = ids
        self.item_ids = item_ids if item_ids is not None else ids
        self.day_num = day_num
        self.phase_tick = 0

        # Cấu hình độ tươi (Contract v1.2)
        fcfg = tuning.get("freshness", {})
        self.fresh_initial = fresh_frac(fcfg.get("initial", 100))
        self.fresh_decay_per_tick = fresh_frac(fcfg.get("gather_decay_per_s", 0.5)) / 60
        self.spoiled_below = fresh_frac(fcfg.get("spoiled_below", 30))

        # Áp dụng nâng cấp có hiệu lực (trong chế độ day)
        ups = active_upgrades or {}
        oxy_s = t["oxygen_max_s"]
        hp_max = int(t["hp_max"])
        shop_ups = tuning.get("shop", {}).get("upgrades", {})
        oxy_lvl = int(ups.get("oxygen", 0))
        if oxy_lvl > 0 and "oxygen" in shop_ups:
            for item in shop_ups["oxygen"]:
                if item["level"] == oxy_lvl:
                    oxy_s = item["oxygen_max_s"]
                    break
        hp_lvl = int(ups.get("hp", 0))
        if hp_lvl > 0 and "hp" in shop_ups:
            for item in shop_ups["hp"]:
                if item["level"] == hp_lvl:
                    hp_max = int(item["hp_max"])
                    break
        self.hp_max = hp_max
        self.oxygen_max = int(round(oxy_s * TICK))

        p = scenario.get("player", {})
        self.pos = [float(c) for c in p.get("pos", t["start_pos"])]
        self.vel = [float(c) for c in p.get("vel", [0.0, 0.0])]
        self._tgt = None
        self._ramp_left = 0
        self.heading = float(p.get("heading_deg", t["start_heading_deg"]))
        self.oxygen_ticks = p.get("oxygen_ticks", self.oxygen_max)
        self.hp = p.get("hp", self.hp_max)
        self.zero_oxy_ticks = p.get("zero_oxy_ticks", 0)
        self.invuln_ticks = p.get("invuln_ticks", 0)
        self.catch_cd_ticks = p.get("catch_cd_ticks", 0)
        # Giỏ cá thể v1.2: thứ tự nhặt, cuối mảng là mới nhất
        self.hold = []
        for raw_it in scenario.get("hold", []):
            if isinstance(raw_it, dict):
                if self.day_num > 1:
                    iid = self.item_ids.new("I")
                else:
                    iid = raw_it["id"]
                    self.item_ids.reserve(iid)
                self.hold.append({
                    "id": iid,
                    "kind": raw_it["kind"],
                    "fresh": fresh_frac(raw_it["fresh"]),
                })
            else:
                iid = self.item_ids.new("I")
                self.hold.append({"id": iid, "kind": raw_it, "fresh": self.fresh_initial})
        self.time_left_ticks = scenario.get("time_left_ticks", int(round(t["duration_s"] * TICK)))

        # Nút hái
        src_nodes = scenario["nodes"] if "nodes" in scenario else t["nodes"]
        self.nodes = [{"id": n["id"], "kind": n["kind"], "pos": [float(c) for c in n["pos"]],
                       "regrow_ticks": n.get("regrow_ticks", 0)} for n in src_nodes]
        for e in self.nodes:
            ids.reserve(e["id"])

        # Đàn cá
        self.random_fish = bool(scenario.get("random_fish", True))
        if "fish" in scenario:
            self.fish = [
                {"id": f["id"], "kind": f["kind"], "pos": [float(c) for c in f["pos"]],
                 "heading_deg": float(f.get("heading_deg", 0.0)), "age_ticks": int(f.get("age_ticks", 0))}
                for f in scenario["fish"]
            ]
            for e in self.fish:
                ids.reserve(e["id"])
        elif self.random_fish:
            fi = t["fish_initial"]
            if isinstance(fi, list):
                self.fish = [
                    {"id": f["id"], "kind": f["kind"], "pos": [float(c) for c in f["pos"]],
                     "heading_deg": float(f.get("heading_deg", 0.0)), "age_ticks": int(f.get("age_ticks", 0))}
                    for f in fi
                ]
                for e in self.fish:
                    ids.reserve(e["id"])
            else:
                self.fish = self._spawn_initial_fish(int(fi))
        else:
            self.fish = []

        # Thủy quái (Cá Sấu Năm Chèo)
        if "monsters" in scenario:
            src_m = scenario["monsters"]
            self.monsters = [
                {
                    "id": m["id"],
                    "kind": m["kind"],
                    "pos": [float(c) for c in m["pos"]],
                    "waypoints": [[float(c) for c in wp] for wp in m["waypoints"]],
                    "target_idx": int(m.get("target_idx", 1)),
                    "state": m.get("state", "patrol"),
                    "state_ticks_left": int(m.get("state_ticks_left", 0)),
                    "recoil_dir": [float(c) for c in m["recoil_dir"]] if m.get("recoil_dir") is not None else None,
                }
                for m in src_m
            ]
        else:
            spawns = t.get("monsters", {}).get("spawns", [])
            self.monsters = [
                {
                    "id": m["id"],
                    "kind": m["kind"],
                    "pos": [float(c) for c in m["pos"]],
                    "waypoints": [[float(c) for c in wp] for wp in m["waypoints"]],
                    "target_idx": 1,
                    "state": "patrol",
                    "state_ticks_left": 0,
                    "recoil_dir": None,
                }
                for m in spawns
                if int(m.get("from_day", 1)) <= self.day_num
            ]
        for m in self.monsters:
            ids.reserve(m["id"])

        self.money = 0
        self.earned = 0
        self.reputation = tuning["quan"]["reputation_initial"]
        self.done = False
        self.reason = None

    # --- giao diện cho runner -------------------------------------------------
    @staticmethod
    def _pub_item(it: dict) -> dict:
        return {"id": it["id"], "kind": it["kind"], "fresh": fresh_num(it["fresh"])}

    def inventory_items(self) -> list:
        return hold_to_items(self.hold)

    def snapshot(self) -> dict:
        return {
            "player": {"pos": list(self.pos), "vel": list(self.vel), "heading_deg": self.heading,
                       "oxygen_ticks": self.oxygen_ticks, "oxygen_max_ticks": self.oxygen_max,
                       "hp": self.hp, "hp_max": self.hp_max, "zero_oxy_ticks": self.zero_oxy_ticks,
                       "invuln_ticks": self.invuln_ticks, "catch_cd_ticks": self.catch_cd_ticks,
                       "at_surface": self._at_surface()},
            "hold": [self._pub_item(it) for it in self.hold], "hold_count": len(self.hold),
            "hold_capacity": self.t["hold_capacity"],
            "nodes": [{"id": n["id"], "pos": list(n["pos"]), "kind": n["kind"],
                       "ready": n["regrow_ticks"] == 0, "regrow_ticks": n["regrow_ticks"]}
                      for n in sort_by_id(self.nodes)],
            "fish": [{"id": f["id"], "pos": list(f["pos"]), "kind": f["kind"],
                      "heading_deg": f["heading_deg"], "age_ticks": f["age_ticks"]}
                     for f in sort_by_id(self.fish)],
            "monsters": [
                {"id": m["id"], "kind": m["kind"], "pos": list(m["pos"]),
                 "waypoints": [list(wp) for wp in m["waypoints"]],
                 "target_idx": m["target_idx"], "state": m["state"],
                 "state_ticks_left": m["state_ticks_left"],
                 "recoil_dir": list(m["recoil_dir"]) if m["recoil_dir"] is not None else None}
                for m in sort_by_id(self.monsters)
            ],
        }

    # --- một bước ---------------------------------------------------------------
    def step(self, inp):
        events = []
        # 1. đồng hồ, cooldown, bất tử và hồi nút
        self.phase_tick += 1
        self.time_left_ticks = max(0, self.time_left_ticks - 1)
        self.invuln_ticks = max(0, self.invuln_ticks - 1)
        self.catch_cd_ticks = max(0, self.catch_cd_ticks - 1)
        for n in sort_by_id(self.nodes):
            if n["regrow_ticks"] > 0:
                n["regrow_ticks"] -= 1
                if n["regrow_ticks"] == 0:
                    events.append(("node_regrown", {"node_id": n["id"]}))
        # Hao độ tươi hàng có sẵn ở đầu bước (phát spoiled theo id)
        for it in sort_by_id(self.hold):
            prev = it["fresh"]
            it["fresh"] = max(Fraction(0), prev - self.fresh_decay_per_tick)
            if prev >= self.spoiled_below and it["fresh"] < self.spoiled_below:
                events.append(("spoiled", {"item_id": it["id"], "kind": it["kind"], "location": "hold"}))

        # 2. bơi + chặn mép + dive/surface + oxy/ngạt/ngất
        was_at_surface = self._at_surface()
        self._move(inp)
        now_at_surface = self._at_surface()
        if was_at_surface and not now_at_surface:
            events.append(("dive", {"pos": list(self.pos)}))
        elif not was_at_surface and now_at_surface:
            events.append(("surface", {"pos": list(self.pos)}))

        if now_at_surface:
            refill = int(self.t["oxygen_refill_per_tick"])
            self.oxygen_ticks = min(self.oxygen_max, self.oxygen_ticks + refill)
            self.zero_oxy_ticks = 0
        else:
            prev_oxy = self.oxygen_ticks
            self.oxygen_ticks = max(0, self.oxygen_ticks - 1)
            if prev_oxy > 0 and self.oxygen_ticks == 0:
                events.append(("oxygen_empty", {"oxygen_ticks": 0}))
            if self.oxygen_ticks == 0:
                self.zero_oxy_ticks += 1
                choke_interval = int(self.t["choke_interval_ticks"])
                if self.zero_oxy_ticks >= choke_interval:
                    self.zero_oxy_ticks = 0
                    self.hp = max(0, self.hp - 1)
                    events.append(("choke", {"hp": self.hp}))
                    if self.hp <= 0:
                        lost = [self._pub_item(it) for it in reversed(self.hold)]
                        self.hold = []
                        events.append(("faint", {"cause": "choke", "lost": lost, "hp": 0}))
                        self._finish("fainted", events)
                        return events

        # 3. cập nhật thủy quái theo id rồi xét tối đa một hit
        if self.monsters:
            fainted = self._step_monsters(events)
            if fainted:
                return events

        # 4. interact: bến trước, rồi hái ở mặt nước
        if inp.pressed("interact"):
            if self._in_dock():
                self._finish("docked", events)
                return events
            if now_at_surface:
                radius = self.t["interact_radius"]
                candidates = [
                    n for n in self.nodes
                    if n["regrow_ticks"] == 0 and math.dist(self.pos, n["pos"]) <= radius
                ]
                if candidates:
                    target = min(candidates, key=lambda n: (math.dist(self.pos, n["pos"]), id_key(n["id"])))
                    required = int(self.t["node_yield"])
                    free = int(self.t["hold_capacity"]) - len(self.hold)
                    if free >= required:
                        for _ in range(required):
                            self.hold.append({
                                "id": self.item_ids.new("I"),
                                "kind": target["kind"],
                                "fresh": self.fresh_initial,
                            })
                        target["regrow_ticks"] = int(round(self.t["regrow_s"] * TICK))
                        events.append(("gather", {"node_id": target["id"], "kind": target["kind"], "amount": required}))
                    else:
                        events.append(("hold_full", {"action": "gather", "node_id": target["id"], "required": required, "free": free}))

        # 5. bắt cá (theo vị trí cá trước khi bơi, dưới nước và hết hồi chiêu)
        if inp.pressed("catch") and self.catch_cd_ticks == 0 and not now_at_surface:
            radius = self.t["catch_radius"]
            candidates = [f for f in self.fish if math.dist(self.pos, f["pos"]) <= radius]
            if candidates:
                target = min(candidates, key=lambda f: (math.dist(self.pos, f["pos"]), id_key(f["id"])))
                required = int(self.t["fish_yield"][target["kind"]])
                free = int(self.t["hold_capacity"]) - len(self.hold)
                if free >= required:
                    for _ in range(required):
                        self.hold.append({
                            "id": self.item_ids.new("I"),
                            "kind": target["kind"],
                            "fresh": self.fresh_initial,
                        })
                    self.fish.remove(target)
                    self.catch_cd_ticks = int(round(self.t["catch_cooldown_s"] * TICK))
                    events.append(("fish_caught", {"fish_id": target["id"], "kind": target["kind"], "yield": required}))
                else:
                    events.append(("hold_full", {"action": "catch", "fish_id": target["id"], "required": required, "free": free}))

        # 6. hết giờ
        if self.time_left_ticks <= 0:
            self._finish("time", events)
            return events

        # 7. cá bơi và sinh thêm theo lịch (khi còn giờ và random_fish bật)
        if self.random_fish:
            self._step_fish()
            spawn_ticks = int(self.t.get("fish_spawn_ticks", 0))
            if spawn_ticks > 0 and self.phase_tick % spawn_ticks == 0:
                self._try_spawn_fish(events)

        return events

    # --- cá bơi & sinh cá -------------------------------------------------------
    def _species_spawn_points(self) -> dict:
        xs = self.t.get("fish_spawn_x", [])
        depths = self.t.get("fish_spawn_depths", {})
        return {k: [(float(x), float(d)) for x in xs for d in depths[k]] for k in sorted(depths)}

    def _weighted_choice_species(self, avail_by_species: dict, rng) -> str:
        weights = self.t.get("fish_weights", {})
        eligible = sorted(k for k, pts in avail_by_species.items() if pts)
        total = sum(float(weights.get(k, 1.0)) for k in eligible)
        r = rng.random() * total
        acc = 0.0
        for k in eligible:
            acc += float(weights.get(k, 1.0))
            if r < acc:
                return k
        return eligible[-1]

    def _spawn_initial_fish(self, count: int) -> list:
        rng = self.rng.get("fish_spawn")
        pts_map = self._species_spawn_points()
        used = set()
        out = []
        for _ in range(count):
            avail = {k: [pt for pt in pts if pt not in used] for k, pts in pts_map.items()}
            if not any(avail.values()):
                break
            kind = self._weighted_choice_species(avail, rng)
            pt = rng.choice(avail[kind])
            used.add(pt)
            heading = rng.uniform(0.0, 360.0)
            out.append({
                "id": self.ids.new("F"),
                "kind": kind,
                "pos": [pt[0], pt[1]],
                "heading_deg": heading,
                "age_ticks": 0,
            })
        return out

    def _step_fish(self):
        speed = float(self.t.get("fish_speed", 0.0))
        if speed <= 0:
            return
        turn_ticks = int(self.t.get("fish_turn_ticks", 120))
        xmin, xmax = self.t["fish_x"]
        depths = self.t["fish_depths"]
        rng = self.rng.get("fish_turn")
        step_dist = speed / TICK
        for f in sort_by_id(self.fish):
            f["age_ticks"] += 1
            if turn_ticks > 0 and f["age_ticks"] % turn_ticks == 0:
                f["heading_deg"] = rng.uniform(0.0, 360.0)
            rad = math.radians(f["heading_deg"])
            vx, vd = math.cos(rad), math.sin(rad)
            nx = f["pos"][0] + vx * step_dist
            nd = f["pos"][1] + vd * step_dist
            dmin, dmax = depths[f["kind"]]
            while nx < xmin or nx > xmax:
                if nx < xmin:
                    nx = xmin + (xmin - nx)
                    vx = -vx
                elif nx > xmax:
                    nx = xmax - (nx - xmax)
                    vx = -vx
            while nd < dmin or nd > dmax:
                if nd < dmin:
                    nd = dmin + (dmin - nd)
                    vd = -vd
                elif nd > dmax:
                    nd = dmax - (nd - dmax)
                    vd = -vd
            f["pos"] = [nx, nd]
            f["heading_deg"] = math.degrees(math.atan2(vd, vx)) % 360.0

    def _try_spawn_fish(self, events):
        fmax = int(self.t.get("fish_max", 12))
        if len(self.fish) >= fmax:
            return
        clearance = float(self.t.get("fish_spawn_clearance", 1.0))
        pts_map = self._species_spawn_points()
        avail = {
            k: [pt for pt in pts if all(math.dist(pt, f["pos"]) > clearance for f in self.fish)]
            for k, pts in pts_map.items()
        }
        if not any(avail.values()):
            return
        rng = self.rng.get("fish_spawn")
        kind = self._weighted_choice_species(avail, rng)
        pt = rng.choice(avail[kind])
        heading = rng.uniform(0.0, 360.0)
        fid = self.ids.new("F")
        self.fish.append({
            "id": fid,
            "kind": kind,
            "pos": [pt[0], pt[1]],
            "heading_deg": heading,
            "age_ticks": 0,
        })
        events.append(("fish_spawned", {"id": fid, "kind": kind, "pos": [pt[0], pt[1]]}))

    # --- thủy quái (Cá Sấu Năm Chèo) -------------------------------------------
    def _move_monster_toward(self, m, target, step_dist, bounds_x, depths):
        dx = target[0] - m["pos"][0]
        dd = target[1] - m["pos"][1]
        dist = math.hypot(dx, dd)
        if dist <= step_dist or dist <= 1e-12:
            nx, nd = target[0], target[1]
            reached = True
        else:
            nx = m["pos"][0] + (dx / dist) * step_dist
            nd = m["pos"][1] + (dd / dist) * step_dist
            reached = False
        m["pos"][0] = max(bounds_x[0], min(bounds_x[1], nx))
        m["pos"][1] = max(depths[0], min(depths[1], nd))
        return reached

    def _step_monsters(self, events) -> bool:
        mcfg = self.t.get("monsters", {})
        species_map = mcfg.get("species", {})
        bounds_x = self.t["bounds"]["x"]
        can_hit_ids = set()

        for m in sort_by_id(self.monsters):
            sp = species_map[m["kind"]]
            depths = sp["depths"]
            d_min = depths[0]
            st = m["state"]
            if st == "recoil":
                step_d = float(sp["recoil_dist"]) / float(sp["recoil_ticks"])
                rdir = m["recoil_dir"] or [1.0, 0.0]
                m["pos"][0] = max(bounds_x[0], min(bounds_x[1], m["pos"][0] + rdir[0] * step_d))
                m["pos"][1] = max(depths[0], min(depths[1], m["pos"][1] + rdir[1] * step_d))
                m["state_ticks_left"] -= 1
                if m["state_ticks_left"] <= 0:
                    m["state"] = "patrol"
                    m["state_ticks_left"] = 0
                    m["recoil_dir"] = None
                continue
            if st == "stunned":
                m["state_ticks_left"] -= 1
                if m["state_ticks_left"] <= 0:
                    m["state"] = "patrol"
                    m["state_ticks_left"] = 0
                    m["recoil_dir"] = None
                continue

            can_hit_ids.add(m["id"])
            dist_p = math.dist(m["pos"], self.pos)
            if st == "patrol":
                if self.pos[1] >= d_min and dist_p <= sp["detect_radius"]:
                    m["state"] = "chase"
                    self._move_monster_toward(m, self.pos, float(sp["chase_speed"]) / TICK, bounds_x, depths)
                else:
                    wp = m["waypoints"][m["target_idx"]]
                    if self._move_monster_toward(m, wp, float(sp["patrol_speed"]) / TICK, bounds_x, depths):
                        m["target_idx"] = 1 - m["target_idx"]
            elif st == "chase":
                if self.pos[1] < d_min or dist_p > sp["exit_radius"]:
                    m["state"] = "patrol"
                    wp = m["waypoints"][m["target_idx"]]
                    if self._move_monster_toward(m, wp, float(sp["patrol_speed"]) / TICK, bounds_x, depths):
                        m["target_idx"] = 1 - m["target_idx"]
                else:
                    self._move_monster_toward(m, self.pos, float(sp["chase_speed"]) / TICK, bounds_x, depths)

        # Xét tối đa một hit
        if self.invuln_ticks == 0 and can_hit_ids:
            eligible = []
            for m in self.monsters:
                if m["id"] not in can_hit_ids:
                    continue
                sp = species_map[m["kind"]]
                if self.pos[1] >= sp["depths"][0] and math.dist(m["pos"], self.pos) <= sp["hit_radius"]:
                    eligible.append(m)
            if eligible:
                attacker = min(eligible, key=lambda m: (math.dist(m["pos"], self.pos), id_key(m["id"])))
                sp = species_map[attacker["kind"]]
                self.hp = max(0, self.hp - 1)
                loss_ratio = float(mcfg.get("loss_ratio", 0.5))
                drop_n = math.floor(len(self.hold) * loss_ratio)
                lost = [self._pub_item(self.hold.pop()) for _ in range(drop_n)]
                self.invuln_ticks = int(mcfg.get("invuln_ticks", 90))

                dx = attacker["pos"][0] - self.pos[0]
                dd = attacker["pos"][1] - self.pos[1]
                dlen = math.hypot(dx, dd)
                rdir = [dx / dlen, dd / dlen] if dlen > 1e-12 else [1.0, 0.0]
                attacker["state"] = "recoil"
                attacker["state_ticks_left"] = int(sp["recoil_ticks"])
                attacker["recoil_dir"] = rdir

                events.append(("monster_hit", {
                    "monster_id": attacker["id"],
                    "hp": self.hp,
                    "lost": lost,
                    "pos": list(self.pos),
                }))
                if self.hp <= 0:
                    rem_lost = [self._pub_item(it) for it in reversed(self.hold)]
                    self.hold = []
                    events.append(("faint", {"cause": "monster", "lost": rem_lost, "hp": 0}))
                    self._finish("fainted", events)
                    return True
        return False

    # --- tiện ích ---------------------------------------------------------------
    def _at_surface(self) -> bool:
        return self.pos[1] <= self.t["surface_depth"]

    def _in_dock(self) -> bool:
        return math.dist(self.pos, self.t["dock_pos"]) <= self.t["dock_radius"]

    def _finish(self, reason, events):
        self.done = True
        self.reason = reason
        events.append(("gather_end", {"reason": reason, "inventory": {"items": self.inventory_items()}}))

    def _move(self, inp):
        speed = self.t["swim_speed"]
        mx, md = inp.move
        self.vel = ramp_velocity(self, (mx * speed, md * speed), int(self.t["ramp_max_ticks"]))
        if (mx, md) != (0.0, 0.0):
            self.heading = math.degrees(math.atan2(md, mx)) % 360
        b = self.t["bounds"]
        for i, axis in enumerate(AXES):
            self.pos[i] += self.vel[i] / TICK
            lo, hi = b[axis]
            if self.pos[i] <= lo:
                self.pos[i] = lo
                self.vel[i] = max(0.0, self.vel[i])
            elif self.pos[i] >= hi:
                self.pos[i] = hi
                self.vel[i] = min(0.0, self.vel[i])
