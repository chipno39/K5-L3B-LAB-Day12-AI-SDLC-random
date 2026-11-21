import json, sys
sys.path.insert(0, ".")
from chonoi.contract import load_contract
from chonoi.live import LiveGame
from chonoi.inputs import InputState
t = load_contract()["tuning"]
out = []
def snap(g, label):
    s = json.loads(g.state_json()); out.append(s); print(f"{label:16} screen={s['screen']!s:14} phase={s['phase']:7} state={s['state']:8} tick={s['tick']}")
    return s
# 1) ngày 1: gather gần quái (đuổi), rồi cập bến ngay để sang quán
sc = {"gather": {"player": {"pos": [58, 22]}, "hold": ["ca_loc", "ca_loc", "bong_sung", "bong_sung", "ca_linh"]},
      "quan": {"customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui", "order_status": "reserved", "state": "waiting", "patience_ticks_left": 2000},
                              {"id": "C2", "table_id": "T3", "dish_id": "goi_bong_sung", "order_status": "reserved", "state": "waiting", "patience_ticks_left": 900}],
               "time_left_ticks": 400}}
g = LiveGame("day", t, sc, 1, days=2)
snap(g, "menu")
g.advance_screen(); snap(g, "day_intro")
g.advance_screen()
for _ in range(120): g._tick_once()
snap(g, "gather+quai")
g.session.paused = True; snap(g, "paused"); g.session.paused = False
# kết thúc gather nhanh: ép hết giờ
g.session.sim.time_left_ticks = 1
g._tick_once(); snap(g, "evening_intro")
g.advance_screen()
for _ in range(90): g._tick_once()
snap(g, "quan 2 bep 4 ban")
g.session.sim.time_left_ticks = 1
g._tick_once(); snap(g, "day_result")
g.advance_screen(); g.session.money = 300; snap(g, "shop")
g.session.shop_time_left = 1; g._tick_once(); snap(g, "day_intro ngay2")
g.advance_screen(); g.session.sim.time_left_ticks = 1; g._tick_once(); g.advance_screen(); g.session.sim.time_left_ticks = 1; g._tick_once(); g.advance_screen()
g.session.shop_time_left = 1; g._tick_once(); snap(g, "summary")
json.dump(out, open(sys.argv[1], "w"))
