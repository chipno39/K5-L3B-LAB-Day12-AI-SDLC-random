import json, sys, time, subprocess, urllib.request
base = sys.argv[1]; out = sys.argv[2]; edge = sys.argv[3]
def post(path, obj=None):
    req = urllib.request.Request(base + path, data=json.dumps(obj or {}).encode(), method="POST", headers={"Content-Type": "application/json"})
    urllib.request.urlopen(req, timeout=5).read()
def state(): return json.loads(urllib.request.urlopen(base + "/state", timeout=5).read())
def shot(name): subprocess.run([edge, "--headless=new", "--disable-gpu", "--window-size=1200,720", "--virtual-time-budget=2500", f"--screenshot={out}/{name}.png", base + "/"], capture_output=True)
def wait(pred, secs=20):
    t = time.time()
    while time.time() - t < secs:
        s = state()
        if pred(s): return s
        time.sleep(0.05)
    raise SystemExit("timeout; state=" + json.dumps({k: s.get(k) for k in ("tick","hand","stoves","customers","stock")}))
def hold(move, secs):
    post("/input", {"move": move, "interact": False, "catch": False}); time.sleep(secs); post("/input", {"move": [0, 0], "interact": False, "catch": False})
def press(): post("/input", {"move": [0,0], "interact": True, "catch": False}); time.sleep(0.1); post("/input", {"move": [0,0], "interact": False, "catch": False})
s = wait(lambda s: len(s["customers"]) > 0); print("customer:", s["customers"][0]["dish_id"], s["customers"][0]["order_status"], "stock", s["stock"])
shot("1-khach-cho")
hold([-1, 0.5], 1.7); press()                       # tới bếp B1 và nấu
s = wait(lambda s: s["stoves"][0]["state"] == "cooking"); print("cooking:", s["stoves"][0], "stock", s["stock"])
shot("2-dang-nau")
s = wait(lambda s: s["stoves"][0]["state"] == "ready", 15); press()
s = wait(lambda s: s["hand"] is not None); print("hand:", repr(s["hand"]))
shot("3-cam-mon")
hold([1, 0], 1.9); hold([0, -1], 1.6); press()   # ve ban T1 phuc vu
s = wait(lambda s: any(c["state"] == "eating" for c in s["customers"])); print("eating:", s["customers"][0]["state"], s["customers"][0]["order_status"])
shot("4-khach-an")
s = wait(lambda s: s["money"] > 0, 15); print("money:", s["money"], "rep:", s["reputation"], "score:", s["score"])
