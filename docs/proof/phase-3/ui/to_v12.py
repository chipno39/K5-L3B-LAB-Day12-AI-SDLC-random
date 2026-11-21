import json, sys
snaps = json.load(open(sys.argv[1], encoding="utf-8"))
fresh_cycle = [100, 82, 64, 45, 28, 12]
def mk(kinds, start=1):
    return [{"id": f"I{start+i}", "kind": k, "fresh": fresh_cycle[i % len(fresh_cycle)]} for i, k in enumerate(kinds)]
out = []
for s in snaps:
    s = json.loads(json.dumps(s))
    if isinstance(s.get("hold"), list) and (not s["hold"] or isinstance(s["hold"][0], str)):
        s["hold"] = mk(s["hold"]); s["hold_count"] = len(s["hold"])
    if isinstance(s.get("stock"), dict):
        kinds = [k for k, n in sorted(s["stock"].items()) for _ in range(n)]
        s["stock"] = mk(kinds, 10)
        by = {}
        for it in s["stock"]: by.setdefault(it["kind"], []).append(it["id"])
        for c in s.get("customers", []):
            rc = (s.get("menu", {}).get(c.get("dish_id"), {}) or {}).get("recipe", {})
            c["reserved"] = [by.get(k, []).pop(0) for k, n in rc.items() for _ in range(n) if by.get(k)]
    if s.get("last_gather_end"):
        inv = s["last_gather_end"].get("inventory", {}).get("items")
        if isinstance(inv, dict): s["last_gather_end"]["inventory"]["items"] = mk([k for k, n in sorted(inv.items()) for _ in range(n)], 1)
    s["freshness"] = {"spoiled_below": 30}
    out.append(s)
json.dump(out, open(sys.argv[2], "w"), ensure_ascii=False)
print("ok", len(out))
