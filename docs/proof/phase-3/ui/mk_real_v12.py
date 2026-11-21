"""Dựng snapshot gather v1.2 THẬT (qua LiveGame ở chế độ day) có giỏ nhiều độ tươi và hàng ươn, để chụp UI.

    PYTHONIOENCODING=utf-8 python docs/proof/phase-3/ui/mk_real_v12.py out.json
Sau đó dùng một máy chủ tĩnh trả out.json ở /state (xem serve_snap.py của Phase 2) rồi chụp bằng trình duyệt.
Chuyển sang quan sẽ lỗi cho tới khi quan.py chuyển sang kho cá thể (việc của sim/quan).
"""
import json, sys
sys.path.insert(0, ".")
from chonoi.contract import load_contract
from chonoi.live import LiveGame

hold = [{"id": "I1", "kind": "ca_loc", "fresh": 100}, {"id": "I2", "kind": "ca_linh", "fresh": 75.5},
        {"id": "I3", "kind": "ca_linh", "fresh": 42}, {"id": "I4", "kind": "bong_sung", "fresh": 30.25},
        {"id": "I5", "kind": "ca_keo", "fresh": 30.01}, {"id": "I6", "kind": "keo_neo", "fresh": 12}]
g = LiveGame("day", load_contract()["tuning"], {"gather": {"player": {"pos": [20, 0]}, "hold": hold}}, 1, days=1)
g.advance_screen(); g.advance_screen()
for _ in range(100):
    g._tick_once()
s = json.loads(g.state_json())
print("spoiled:", [(e["data"]["item_id"], e["data"]["location"]) for e in s["events"] if e["name"] == "spoiled"])
json.dump([s], open(sys.argv[1], "w"), ensure_ascii=False)
