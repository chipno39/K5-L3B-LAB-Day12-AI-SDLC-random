const fs = require("fs");
const html = fs.readFileSync("chonoi/web/index.html", "utf8");
const js = html.match(/<script>([\s\S]*)<\/script>/)[1];
const snaps = JSON.parse(fs.readFileSync(process.argv[2], "utf8"));
const calls = {};
const mkctx = () => new Proxy({}, {
  get: (t, k) => {
    if (k === "measureText") return (s) => ({ width: String(s).length * 7 });
    if (k === "createLinearGradient") return () => ({ addColorStop() {} });
    if (k in t) return t[k];
    return (...a) => { calls[k] = (calls[k] || 0) + 1; };
  },
  set: (t, k, v) => { t[k] = v; return true; },
});
const ctx = mkctx();
const cv = { width: 0, height: 0, style: {}, getContext: () => ctx };
global.location = { search: process.env.HC === "1" ? "?hc=1" : "" };
let cur = null, rafCb = null, errors = [];
global.document = { getElementById: () => cv };
global.window = global; global.innerWidth = 1100; global.innerHeight = 700; global.devicePixelRatio = 1;
global.addEventListener = () => {};
global.performance = { now: () => 5000 };
global.fetch = async () => ({ json: async () => cur });
global.setTimeout = () => 0;
global.requestAnimationFrame = (cb) => { rafCb = cb; };
const run = new Function(js + "\n;return { frame, setSnap(s){ snap = s; collectToasts(); }, setOffline(v){offline=v} };");
const api = run();
for (const [w, h] of [[1100, 700], [420, 700], [1600, 900]]) {
  global.innerWidth = w; global.innerHeight = h;
  snaps.forEach((s, i) => { try { api.setSnap(s); api.frame(); } catch (e) { errors.push(`snap${i}@${w}: ${e.stack.split("\n").slice(0,3).join(" | ")}`); } });
}
api.setSnap({ tick: 0, mode: "quan", meta: {}, player: null });  // snapshot thiếu gần hết trường
try { api.frame(); } catch (e) { errors.push("minimal quan: " + e.message); }
api.setSnap({ tick: 0, mode: "gather" });
try { api.frame(); } catch (e) { errors.push("minimal gather: " + e.message); }
console.log(errors.length ? errors.join("\n") : "OK: không lỗi runtime", "| draw calls:", Object.keys(calls).length);
