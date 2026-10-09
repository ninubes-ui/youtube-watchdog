# -*- coding: utf-8 -*-
"""
YouTube Growth Watchdog  -  versi GitHub Actions (LIVE)
========================================================
Dijalankan otomatis tiap 12 jam oleh GitHub Actions (gratis, laptop boleh mati).

- Membangun index.html (dashboard gaya GROWTH ROOM) + feed.json (data LIVE).
- Robot/agen mengucapkan pesan sesuai kondisi nyata (balon di atas kepala).
- Kirim Discord HANYA bila ada sinyal (metrik turun / tren baru). Jika tidak: senyap.

Konfigurasi via GitHub Secrets (Settings -> Secrets and variables -> Actions):
  YT_API_KEY          API key YouTube Data API v3 (wajib)
  YT_CHANNEL_ID       Channel ID YouTube (UC..., opsional)
  DISCORD_BOT_TOKEN   token bot Discord
  DISCORD_CHANNEL_ID  ID channel Discord tujuan
"""
import os, sys, json, datetime
import urllib.request, urllib.parse, urllib.error
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
STATE_PATH = os.path.join(HERE, "config_state.json")
DASH_PATH  = os.path.join(HERE, "index.html")
FEED_PATH  = os.path.join(HERE, "feed.json")

YT_API = "https://www.googleapis.com/youtube/v3/"
DISCORD_API = "https://discord.com/api/v10/"
DEFAULT_DISCORD_CHANNEL = "1218606873259937835"

TREND_NEGATIVE = ["mod apk","mod menu","apk","hack","unlimited robux","free robux",
                  "generator","promo code","exploit","aimbot","download"]
TREND_KEYWORDS = ["roblox","steal a brainrot","grow a garden","adopt me","brookhaven",
                  "brainrot","roblox shorts","roblox animation"]
TREND_FEEDS = [
    "https://news.google.com/rss/search?q=Roblox+animation+when:2d&hl=en-US&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=YouTube+Shorts+trend+when:2d&hl=en-US&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=%22Steal+a+Brainrot%22+OR+%22Grow+a+Garden%22+when:3d&hl=en-US&gl=US&ceid=US:en",
]

TEMPLATE = r"""<!DOCTYPE html>
<html lang="id">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>GROWTH ROOM - Kantor Agen (LIVE)</title>
<style>
:root{
  --bg:#070a12; --bg2:#0d1424; --panel:#111a2e; --line:#22304d;
  --neon:#39ff14; --cy:#00e5ff; --am:#ffb300; --pk:#ff2d95; --rd:#ff3b3b;
  --txt:#cfe0ff; --dim:#6f83a8;
}
*{box-sizing:border-box}
html,body{margin:0;padding:0}
body{
  background:
    radial-gradient(1200px 600px at 50% -10%, #16224a 0%, transparent 60%),
    linear-gradient(#070a12,#04060c 70%);
  color:var(--txt);
  font-family:"Consolas","Courier New",monospace;
  min-height:100vh; padding:14px;
}
.crt{position:fixed;inset:0;pointer-events:none;z-index:99;
  background:repeating-linear-gradient(0deg,rgba(0,0,0,.20) 0 1px,transparent 1px 3px);
  mix-blend-mode:multiply;opacity:.5}
.crt:after{content:"";position:absolute;inset:0;
  background:radial-gradient(120% 90% at 50% 50%,transparent 55%,rgba(0,0,0,.65));}
.wrap{max-width:1180px;margin:0 auto}
.hud{display:flex;align-items:center;gap:14px;flex-wrap:wrap;
  padding:10px 14px;background:linear-gradient(#101a30,#0b1322);
  border:3px solid #0a0f1a;box-shadow:0 0 0 3px var(--line),0 6px 0 #060a12;border-radius:10px}
.title{font-size:18px;font-weight:bold;letter-spacing:2px;color:var(--neon);
  text-shadow:0 0 10px rgba(57,255,20,.55)}
.sub{font-size:11px;color:var(--dim)}
.led{width:12px;height:12px;border-radius:50%;background:var(--neon);
  box-shadow:0 0 12px var(--neon);animation:pulse 1.6s infinite}
.led.off{background:var(--rd);box-shadow:0 0 12px var(--rd);animation:none}
.hud .spacer{flex:1}
.chip{font-size:11px;padding:4px 9px;border:2px solid var(--line);border-radius:7px;background:#0a1220}
.chip b{color:#fff}
.chip.live{border-color:var(--neon);color:var(--neon)}
.grid{display:grid;grid-template-columns:250px 1fr 290px;gap:14px;margin-top:14px}
@media(max-width:980px){.grid{grid-template-columns:1fr}}
.panel{background:linear-gradient(#0f1830,#0b1322);border:3px solid #0a0f1a;
  box-shadow:0 0 0 3px var(--line);border-radius:10px;padding:12px}
.ptitle{font-size:11px;letter-spacing:2px;color:var(--cy);margin-bottom:8px;
  text-transform:uppercase;border-bottom:1px dashed var(--line);padding-bottom:6px}
.room{position:relative;height:430px;overflow:hidden;border-radius:10px;
  border:3px solid #0a0f1a;box-shadow:0 0 0 3px var(--line);
  background:
    linear-gradient(#0c1730 0%, #0a1123 55%, #060a14 55%, #04070e 100%);}
.floor{position:absolute;left:0;right:0;bottom:0;height:45%;
  background:repeating-linear-gradient(90deg,transparent 0 39px,rgba(0,229,255,.08) 39px 40px),
             repeating-linear-gradient(0deg,transparent 0 30px,rgba(0,229,255,.08) 30px 31px);
  transform:perspective(340px) rotateX(58deg);transform-origin:bottom center}
.wall{position:absolute;inset:0}
.screenwall{position:absolute;left:50%;top:26px;transform:translateX(-50%);
  width:210px;height:110px;border:4px solid #0a0f1a;border-radius:8px;
  background:linear-gradient(#052033,#021018);box-shadow:0 0 26px rgba(0,229,255,.35);
  display:flex;align-items:center;justify-content:center;font-size:10px;color:#1de9b6;overflow:hidden}
.scan{position:absolute;left:0;right:0;height:16px;background:linear-gradient(transparent,rgba(0,229,255,.25),transparent);
  animation:scan 3.2s linear infinite}
.bars{font-size:9px;line-height:1.35;color:#19c8a3;white-space:pre;opacity:.9}
.npc{position:absolute;left:50%;bottom:26px;transform:translateX(-50%);
  width:130px;height:190px;animation:bob 2.6s ease-in-out infinite}
.npc *{position:absolute}
.ant{left:50%;top:0;transform:translateX(-50%);width:5px;height:22px;background:#8ea3c7}
.ant i{left:50%;top:-9px;transform:translateX(-50%);width:14px;height:14px;border-radius:50%;
  background:var(--cy);box-shadow:0 0 16px var(--cy);animation:pulse 1.3s infinite}
.head{left:50%;top:20px;transform:translateX(-50%);width:100px;height:72px;
  background:linear-gradient(#e7eeff,#aebcdd);border:4px solid #0a0f1a;border-radius:16px}
.eye{top:24px;width:15px;height:15px;border-radius:50%;background:var(--cy);
  box-shadow:0 0 14px var(--cy);animation:blink 4s infinite}
.eye.l{left:18px}.eye.r{right:18px}
.mouth{left:50%;bottom:12px;transform:translateX(-50%);width:34px;height:7px;background:#0a0f1a;border-radius:4px}
.body{left:50%;top:96px;transform:translateX(-50%);width:104px;height:66px;
  background:linear-gradient(#cdd9f2,#8fa1c8);border:4px solid #0a0f1a;border-radius:14px}
.core{left:50%;top:50%;transform:translate(-50%,-50%);width:26px;height:26px;border-radius:50%;
  background:var(--neon);box-shadow:0 0 18px var(--neon);animation:pulse 1.6s infinite}
.arm{top:104px;width:20px;height:52px;background:#9fb0cf;border:4px solid #0a0f1a;border-radius:9px}
.arm.l{left:2px;transform-origin:top center;animation:typeL .5s infinite}
.arm.r{right:2px;transform-origin:top center;animation:typeR .5s infinite}
.leg{top:160px;width:24px;height:30px;background:#8fa1c8;border:4px solid #0a0f1a;border-radius:7px}
.leg.l{left:26px}.leg.r{right:26px}
.bubble{position:absolute;left:50%;top:12px;transform:translateX(-50%);
  background:#0a1220;border:3px solid var(--line);border-radius:12px;padding:8px 12px;
  font-size:12px;max-width:340px;text-align:center;box-shadow:0 0 0 2px #060a12;
  transition:border-color .3s}
.bubble:after{content:"";position:absolute;bottom:-10px;left:50%;transform:translateX(-50%);
  border:9px solid transparent;border-top-color:var(--line)}
.badge{position:absolute;left:50%;bottom:6px;transform:translateX(-50%);
  font-size:11px;letter-spacing:2px;padding:4px 12px;border-radius:20px;
  border:2px solid var(--line);background:#0a1220}
.fx{position:absolute;font-size:22px;opacity:0}
.zzz{right:6px;top:34px}.qm{right:2px;top:30px}.em{left:2px;top:26px}
.s-ISTIRAHAT .npc{animation:bobSlow 4s ease-in-out infinite}
.s-ISTIRAHAT .eye{height:3px;border-radius:2px;animation:none;top:30px}
.s-ISTIRAHAT .core{background:var(--am);box-shadow:0 0 14px var(--am)}
.s-ISTIRAHAT .ant i{background:var(--am);box-shadow:0 0 14px var(--am)}
.s-ISTIRAHAT .zzz{animation:floatUp 3.2s ease-in-out infinite}
.s-ISTIRAHAT .arm{animation:none}
.s-ISTIRAHAT .badge{color:var(--am);border-color:var(--am)}
.s-ISTIRAHAT .bubble{border-color:var(--am)}
.s-BEKERJA .badge{color:var(--neon);border-color:var(--neon)}
.s-BEKERJA .bubble{border-color:var(--neon)}
.s-BEKERJA .eye{animation:blink 4s infinite,glow 1.2s infinite}
.s-SIBUK .npc{animation:shake .18s infinite}
.s-SIBUK .core{background:var(--pk);box-shadow:0 0 22px var(--pk)}
.s-SIBUK .ant i{background:var(--pk);box-shadow:0 0 20px var(--pk)}
.s-SIBUK .em{animation:pop .7s infinite;color:var(--pk)}
.s-SIBUK .badge{color:var(--pk);border-color:var(--pk)}
.s-SIBUK .bubble{border-color:var(--pk)}
.s-SIBUK .screenwall{box-shadow:0 0 40px rgba(255,45,149,.6);border-color:#1a0a12}
.s-BINGUNG .npc{animation:wobble 1.4s ease-in-out infinite;transform:translateX(-50%)}
.s-BINGUNG .eye{background:var(--rd);box-shadow:0 0 14px var(--rd)}
.s-BINGUNG .core{background:var(--rd);box-shadow:0 0 18px var(--rd)}
.s-BINGUNG .qm{animation:pop 1.1s infinite;color:var(--rd)}
.s-BINGUNG .badge{color:var(--rd);border-color:var(--rd)}
.s-BINGUNG .bubble{border-color:var(--rd)}
@keyframes bob{0%,100%{transform:translateX(-50%) translateY(0)}50%{transform:translateX(-50%) translateY(-8px)}}
@keyframes bobSlow{0%,100%{transform:translateX(-50%) translateY(0)}50%{transform:translateX(-50%) translateY(-4px)}}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.35}}
@keyframes blink{0%,92%,100%{transform:scaleY(1)}95%{transform:scaleY(.1)}}
@keyframes glow{0%,100%{filter:none}50%{filter:brightness(1.6)}}
@keyframes shake{0%{transform:translateX(-50%) rotate(-1.5deg)}50%{transform:translateX(-52%) rotate(1.5deg)}100%{transform:translateX(-50%) rotate(-1.5deg)}}
@keyframes wobble{0%,100%{transform:translateX(-50%) rotate(-7deg)}50%{transform:translateX(-50%) rotate(7deg)}}
@keyframes typeL{0%,100%{transform:rotate(6deg)}50%{transform:rotate(-14deg)}}
@keyframes typeR{0%,100%{transform:rotate(-6deg)}50%{transform:rotate(14deg)}}
@keyframes floatUp{0%{opacity:0;transform:translateY(6px)}30%{opacity:1}100%{opacity:0;transform:translateY(-26px)}}
@keyframes pop{0%,100%{opacity:.2;transform:scale(.85)}50%{opacity:1;transform:scale(1.15)}}
@keyframes scan{0%{top:-16px}100%{top:110px}}
.stat{display:flex;justify-content:space-between;font-size:12px;padding:6px 0;border-bottom:1px dashed #1b2740}
.stat span:last-child{color:#fff}
.big{font-size:22px;font-weight:bold;color:var(--neon);text-shadow:0 0 10px rgba(57,255,20,.4)}
.trend{font-size:11.5px;padding:7px 8px;margin-bottom:6px;background:#0a1220;border-left:3px solid var(--cy);border-radius:5px;line-height:1.35}
.trend a{color:var(--txt);text-decoration:none}
.trend:hover{border-left-color:var(--neon)}
.log{height:180px;overflow:auto;font-size:11px;line-height:1.7;background:#05080f;border:2px solid var(--line);border-radius:8px;padding:8px}
.log div:before{content:"> ";color:var(--neon)}
.log div.bad{color:#ffb3b3}.log div.bad:before{color:var(--rd)}
.log div.ok:before{color:var(--neon)}
.log div.warn:before{color:var(--am)}
.foot{margin-top:14px;font-size:10.5px;color:var(--dim);display:flex;justify-content:space-between;flex-wrap:wrap;gap:8px}
.kbd{color:var(--cy)}
.hist{font-size:10.5px;color:var(--dim);max-height:96px;overflow:auto;margin-top:8px;border-top:1px dashed var(--line);padding-top:6px}
.hist div{padding:2px 0}
.newflash{animation:flash .9s}
@keyframes flash{0%{background:#1b3a1b}100%{background:transparent}}
</style>
</head>
<body>
<div class="crt"></div>
<div class="wrap">
  <div class="hud">
    <span class="led" id="live-led"></span>
    <div>
      <div class="title">GROWTH ROOM</div>
      <div class="sub">Kantor Agen &middot; Sutradara Animasi &amp; Analis YouTube</div>
    </div>
    <span class="spacer"></span>
    <span class="chip live" id="live-chip">&#9679; LIVE</span>
    <span class="chip">Shift <b>12 jam</b></span>
    <span class="chip">Status <b id="hud-status">__STATUS_TEXT__</b></span>
    <span class="chip">Jam <b id="clk">--:--</b></span>
  </div>

  <div class="grid">
    <div class="panel">
      <div class="ptitle">Metrik Channel</div>
      <div class="stat"><span>Video terbaru</span></div>
      <div style="font-size:11.5px;color:#fff;margin-bottom:6px" id="m-title">__LASTTITLE__</div>
      <div class="stat"><span>Views terbaru</span><span class="big" id="m-views">__LASTVIEWS__</span></div>
      <div class="stat"><span>Rata-rata 7</span><span id="m-avg">__AVG7__</span></div>
      <div class="stat"><span>Perubahan</span><span id="m-delta">__DELTA__</span></div>
      <div class="ptitle" style="margin-top:14px">Kesehatan Sistem</div>
      <div class="stat"><span>Kunci API</span><span id="k-key">__KEYTXT__</span></div>
      <div class="stat"><span>Channel ID</span><span id="k-ch">__CHTXT__</span></div>
      <div class="stat"><span>Discord</span><span id="k-dc">__DCTXT__</span></div>
      <div class="stat"><span>Run terakhir</span><span style="font-size:11px" id="k-run">__LASTRUN__</span></div>
    </div>

    <div class="room s-__STATE__" id="room">
      <div class="wall"></div>
      <div class="screenwall">
        <div class="scan"></div>
        <div class="bars" id="mon-bars">__SCREEN__</div>
      </div>
      <div class="floor"></div>
      <div class="bubble" id="npc-bubble">__TASK__</div>
      <div class="npc">
        <div class="ant"><i></i></div>
        <div class="head"><span class="eye l"></span><span class="eye r"></span><span class="mouth"></span></div>
        <div class="body"><span class="core"></span></div>
        <div class="arm l"></div><div class="arm r"></div>
        <div class="leg l"></div><div class="leg r"></div>
      </div>
      <div class="fx zzz">z z Z</div>
      <div class="fx qm">?</div>
      <div class="fx em">!</div>
      <div class="badge" id="npc-badge">__STATE__ &middot; __STATEID__</div>
    </div>

    <div class="panel">
      <div class="ptitle">Peluang Tren (live)</div>
      <div style="max-height:400px;overflow:auto" id="trends">__TRENDS__</div>
      <div class="ptitle" style="margin-top:10px">Riwayat Pesan Agen</div>
      <div class="hist" id="hist">__HIST__</div>
    </div>
  </div>

  <div class="panel" style="margin-top:14px">
    <div class="ptitle">Log Aktivitas</div>
    <div class="log" id="log">__LOG__</div>
  </div>

  <div class="foot">
    <span>Live feed: <span class="kbd">feed.json</span> &middot; auto-refresh 8s &middot; cron <span class="kbd">0 */12 * * *</span></span>
    <span>Render: <span id="rendered">__RENDER__</span> &middot; <span id="feed-src">-</span></span>
  </div>
</div>

<script>
function esc(s){return String(s==null?"":s).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;");}
function p2(x){return String(x).padStart(2,"0");}
function tick(){var n=new Date();document.getElementById("clk").textContent=p2(n.getHours())+":"+p2(n.getMinutes())+":"+p2(n.getSeconds());}
setInterval(tick,1000);tick();

var lastTs=0;
function apply(d){
  if(!d||!d.state) return;
  if(d.ts && d.ts<lastTs) return;
  if(d.ts) lastTs=d.ts;
  var room=document.getElementById("room");
  room.className="room s-"+d.state;
  document.getElementById("npc-bubble").innerHTML=esc(d.task||"");
  var badge=document.getElementById("npc-badge");
  badge.innerHTML=esc(d.state)+" \u00b7 "+esc(d.stateid||"ID-01");
  document.getElementById("mon-bars").textContent=d.screen_text||"";
  if(d.status_text) document.getElementById("hud-status").textContent=d.status_text;
  var m=d.metrics||{};
  document.getElementById("m-title").textContent=m.last_title||"(belum ada data)";
  document.getElementById("m-views").textContent=m.last_views!=null?m.last_views:"-";
  document.getElementById("m-avg").textContent=m.avg7!=null?m.avg7:"-";
  document.getElementById("m-delta").textContent=m.delta_pct||"-";
  document.getElementById("k-key").textContent=d.api_key_ok?"VALID":"TIDAK VALID";
  document.getElementById("k-ch").textContent=d.channel_id||"belum diisi";
  var dc=d.discord||{};
  document.getElementById("k-dc").textContent=(dc.channel||"-")+(dc.detail?(" | "+dc.detail):"");
  document.getElementById("k-run").textContent=d.last_run||"-";
  document.getElementById("rendered").textContent=d.rendered||"-";
  document.getElementById("feed-src").textContent=d.source?("sumber: "+d.source):"-";
  if(d.trends&&d.trends.length){
    var h="";for(var i=0;i<d.trends.length;i++){var t=d.trends[i];
      h+='<div class="trend"><a href="'+esc(t.link||"#")+'" target="_blank">'+esc(t.title||"")+'</a></div>';}
    document.getElementById("trends").innerHTML=h;
  }
  if(d.events&&d.events.length){
    var g="";var ev=d.events.slice(-22);
    for(var j=0;j<ev.length;j++){var msg=esc(ev[j].msg||"");var low=msg.toLowerCase();
      var cls=("gagal"in low||"tidak"in low)?"bad":(("terkirim"in low||"valid"in low)?"ok":"warn");
      g+='<div class="'+cls+'">'+esc(ev[j].t||"")+"  "+msg+"</div>";}
    document.getElementById("log").innerHTML=g;
  }
  if(d.messages&&d.messages.length){
    var hh="";var ms=d.messages.slice(-8);
    for(var k=0;k<ms.length;k++){hh+='<div>['+esc(ms[k].t||"")+"] "+esc(ms[k].text||"")+"</div>";}
    document.getElementById("hist").innerHTML=hh;
  }
  var led=document.getElementById("live-led");
  led.className="led"+(d.state==="BINGUNG"?" off":"");
}
function poll(){
  var url="feed.json?t="+Date.now();
  fetch(url,{cache:"no-store"}).then(function(r){return r.json();}).then(apply).catch(function(){});
  fetch("push.json?t="+Date.now(),{cache:"no-store"}).then(function(r){return r.json();}).then(apply).catch(function(){});
}
poll();setInterval(poll,8000);
</script>
</body>
</html>
"""

STATE_META = {
    "ISTIRAHAT": "Agen sedang istirahat",
    "BEKERJA":   "Agen sedang bekerja",
    "SIBUK":     "Agen sedang sibuk",
    "BINGUNG":   "Agen butuh bantuan",
}


def now_utc():
    return datetime.datetime.now(datetime.timezone.utc)


def log(m):
    print("[watchdog] " + str(m))


def load_json(path, default):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return dict(default)


def save_json(path, obj):
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(obj, f, indent=2, ensure_ascii=False)
    except Exception as e:
        log("gagal simpan: " + repr(e))


def http_get(url, timeout=20):
    req = urllib.request.Request(url, headers={"User-Agent": "yt-watchdog/3.0"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", "replace")


def yt_api(ep, params, key):
    p = dict(params); p["key"] = key
    return json.loads(http_get(YT_API + ep + "?" + urllib.parse.urlencode(p)))


def test_api_key(key):
    try:
        yt_api("videos", {"part": "id", "id": "dQw4w9WgXcQ"}, key)
        return True
    except urllib.error.HTTPError as e:
        log("API key HTTP " + str(e.code)); return False
    except Exception as e:
        log("API key err " + repr(e)); return False


def fetch_channel_videos(key, ch_id, maxn=10):
    ch = yt_api("channels", {"part": "contentDetails,statistics", "id": ch_id}, key)
    items = ch.get("items", [])
    if not items:
        raise RuntimeError("Channel tidak ditemukan.")
    uploads = items[0]["contentDetails"]["relatedPlaylists"]["uploads"]
    pl = yt_api("playlistItems", {"part": "contentDetails,snippet",
                                  "playlistId": uploads, "maxResults": maxn}, key)
    vids = [{"id": it["contentDetails"]["videoId"], "title": it["snippet"]["title"]}
            for it in pl.get("items", [])]
    if not vids:
        return []
    ids = ",".join(v["id"] for v in vids)
    vs = yt_api("videos", {"part": "statistics", "id": ids}, key)
    vmap = {v["id"]: v.get("statistics", {}) for v in vs.get("items", [])}
    for v in vids:
        try:
            v["views"] = int(vmap.get(v["id"], {}).get("viewCount", 0))
        except Exception:
            v["views"] = 0
    return vids


def fetch_trends():
    out = []
    for feed in TREND_FEEDS:
        try:
            root = ET.fromstring(http_get(feed))
            for it in root.iter("item"):
                t = (it.findtext("title") or "").strip()
                l = (it.findtext("link") or "").strip()
                low = t.lower()
                if any(k in low for k in TREND_KEYWORDS) and not any(n in low for n in TREND_NEGATIVE):
                    out.append({"title": t, "link": l})
        except Exception as e:
            log("feed gagal " + repr(e))
    seen, uniq = set(), []
    for o in out:
        k = o["title"].lower()[:80]
        if k not in seen:
            seen.add(k); uniq.append(o)
    return uniq[:12]


def discord_send(token, ch_id, content):
    url = DISCORD_API + "channels/" + str(ch_id) + "/messages"
    data = json.dumps({"content": content[:1990]}).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST",
        headers={"Authorization": "Bot " + token, "Content-Type": "application/json",
                 "User-Agent": "yt-watchdog/3.0"})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return r.status in (200, 201), "HTTP " + str(r.status)
    except urllib.error.HTTPError as e:
        return False, "HTTP " + str(e.code) + ": " + e.read().decode("utf-8", "replace")[:160]
    except Exception as e:
        return False, repr(e)


def build_report(metric_alert, trend_alert, metrics):
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    L = ["=" * 55, " LAPORAN KRITIS YOUTUBE  -  " + now, "=" * 55,
         "Dibuat otomatis. Muncul hanya bila ada sinyal penting.", ""]
    if metric_alert:
        L.append(">>> [A] METRIK PENONTON TURUN DRASTIS")
        L += ["    - " + s for s in metric_alert] + [""]
    if trend_alert:
        L.append(">>> [B] PELUANG TREN BARU YANG RELEVAN")
        for t in trend_alert:
            L += ["    * " + t["title"], "      " + t["link"]]
        L.append("")
    L.append("--- RINGKASAN METRIK ---")
    if metrics:
        L += ["    Video terbaru : " + str(metrics.get("last_title", "-")),
              "    Views         : " + str(metrics.get("last_views", "-")),
              "    Rata-rata 7   : " + str(metrics.get("avg7", "-")),
              "    Perubahan     : " + str(metrics.get("delta_pct", "-"))]
    else:
        L.append("    (metrik channel belum aktif: isi YT_CHANNEL_ID)")
    L += ["", "--- AKSI ---",
          "    1. Cek video di Studio pada 0-48 jam tayang.",
          "    2. Bandingkan hook 3 detik vs tren di atas.",
          "    3. Siapkan 1 Shorts 'respon cepat' dari pola tren yang lolos.",
          "", "Generated by run_watchdog.py (GitHub Actions)"]
    return "\n".join(L)


def decide(st):
    say = st.get("say") or {}
    if say.get("text"):
        return (say.get("state") or "BEKERJA", str(say["text"]), say.get("tag") or "PESAN")
    api_ok, ch = bool(st.get("api_key_ok")), (st.get("channel_id") or "").strip()
    al = st.get("alert") or {}
    if not api_ok:
        return "BINGUNG", "Kunci API tidak valid. Aku belum bisa jalan, Bos.", "BUTUH KUNCI API"
    if not ch:
        return "BINGUNG", "Channel ID YouTube belum diisi. Aku belum bisa baca metrik channelmu.", "BUTUH CHANNEL ID"
    if al.get("metric"):
        return "SIBUK", "METRIK TURUN DRASTIS! Aku sedang menyusun laporan kritis.", "ALERT METRIK"
    if al.get("trend"):
        return "BEKERJA", "Ada tren baru yang relevan. Aku riset & siapkan ide.", "RISET TREN"
    if st.get("metrics"):
        return "BEKERJA", "Metrik aman. Aku pantau terus, ada peluang aku catat.", "PANTAU RUTIN"
    return "ISTIRAHAT", "Semua aman. Tidak ada sinyal. Aku ngopi dulu ya, Bos.", "SENYAP - AMAN"


def _e(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def _trends_html(trends):
    h = ""
    for t in (trends or [])[:12]:
        h += ('<div class="trend"><a href="' + _e(t.get("link", "#")) + '" target="_blank">'
              + _e(t.get("title", "")) + "</a></div>")
    return h or '<div style="font-size:11px;color:#6f83a8">Belum ada data tren.</div>'


def _log_html(events):
    h = ""
    for ev in (events or [])[-22:]:
        msg = _e(ev.get("msg", ""))
        low = msg.lower()
        cls = "bad" if ("gagal" in low or "tidak" in low or "bermasalah" in low) else \
              ("ok" if ("terkirim" in low or "valid" in low or "aman" in low) else "warn")
        h += '<div class="' + cls + '">' + _e(ev.get("t", "")) + "  " + msg + "</div>"
    return h or "<div>Menunggu run pertama...</div>"


def _hist_html(messages):
    h = ""
    for m in (messages or [])[-8:]:
        h += "<div>[" + _e(m.get("t", "")) + "] " + _e(m.get("text", "")) + "</div>"
    return h or "<div>Belum ada pesan.</div>"


def build_dashboard(st, path):
    state, task, stateid = decide(st)
    m = st.get("metrics") or {}
    dc = st.get("discord") or {}
    filled = (TEMPLATE
        .replace("__STATE__", state)
        .replace("__STATEID__", stateid)
        .replace("__STATUS_TEXT__", STATE_META.get(state, ""))
        .replace("__TASK__", _e(task))
        .replace("__LASTTITLE__", _e(m.get("last_title", "(belum ada data)")))
        .replace("__LASTVIEWS__", _e(m.get("last_views", "-")))
        .replace("__AVG7__", _e(m.get("avg7", "-")))
        .replace("__DELTA__", _e(m.get("delta_pct", "-")))
        .replace("__KEYTXT__", _e("VALID" if st.get("api_key_ok") else "TIDAK VALID"))
        .replace("__CHTXT__", _e(st.get("channel_id") or "belum diisi"))
        .replace("__DCTXT__", _e((dc.get("channel", "-")) + ((" | " + str(dc.get("detail"))) if dc.get("detail") else "")))
        .replace("__LASTRUN__", _e(st.get("last_run", "-")))
        .replace("__TRENDS__", _trends_html(st.get("trends")))
        .replace("__HIST__", _hist_html(st.get("messages")))
        .replace("__LOG__", _log_html(st.get("events")))
        .replace("__SCREEN__", _e(st.get("screen_text", "[ MONITORING TREN ]")))
        .replace("__RENDER__", datetime.datetime.now().strftime("%Y-%m-%d %H:%M")))
    with open(path, "w", encoding="utf-8") as f:
        f.write(filled)
    return path


def build_feed(st, path, source="watchdog"):
    state, task, stateid = decide(st)
    feed = {
        "ts": int(datetime.datetime.now().timestamp()),
        "rendered": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "source": source, "state": state, "stateid": stateid,
        "status_text": STATE_META.get(state, ""), "task": task,
        "screen_text": st.get("screen_text", ""),
        "api_key_ok": bool(st.get("api_key_ok")),
        "channel_id": st.get("channel_id") or "",
        "last_run": st.get("last_run", "-"),
        "metrics": st.get("metrics") or {}, "discord": st.get("discord") or {},
        "trends": st.get("trends") or [], "events": (st.get("events") or [])[-22:],
        "messages": (st.get("messages") or [])[-12:], "alert": st.get("alert") or {},
    }
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(feed, f, ensure_ascii=False, indent=1)
    os.replace(tmp, path)
    return path


def main():
    st_file = load_json(STATE_PATH, {"events": [], "trends": [], "baseline": {}, "messages": []})
    events = st_file.get("events", [])
    msgs = st_file.get("messages", [])
    trends_prev = st_file.get("trends", [])
    seen_trends = set(st_file.get("seen_trends", []))
    base = st_file.get("baseline", {})
    now = now_utc()

    def ev(m):
        events.append({"t": now.strftime("%m-%d %H:%M"), "msg": m}); log(m)

    api_key = (os.environ.get("YT_API_KEY", "") or "").strip()
    api_ok = bool(api_key) and test_api_key(api_key)
    ev("Cek API key: " + ("VALID" if api_ok else "tidak ada/tidak valid"))

    ch_id = (os.environ.get("YT_CHANNEL_ID", "") or st_file.get("channel_id", "")).strip()

    metric_alert, metrics = [], {}
    drop_pct, min_den = 25.0, 500.0
    first_run = not base.get("last_check_utc")

    if api_ok and ch_id:
        try:
            vids = fetch_channel_videos(api_key, ch_id, 10)
            if vids:
                last = vids[0]
                recent = [v["views"] for v in vids[:7]]
                avg7 = int(sum(recent) / len(recent)) if recent else 0
                delta = "-"
                if not first_run and base.get("avg_views_last_7_videos", 0) > 0:
                    prev = float(base["avg_views_last_7_videos"])
                    if prev >= min_den:
                        chg = (last["views"] - prev) / prev * 100.0
                        delta = "%+.1f%%" % chg
                        if chg <= -drop_pct:
                            metric_alert.append("Video '" + last["title"][:50] +
                                "' hanya " + str(last["views"]) + " views (baseline " +
                                str(int(prev)) + "). Turun " + delta)
                metrics = {"last_title": last["title"][:70], "last_views": last["views"],
                           "avg7": avg7, "delta_pct": delta}
                base.update({"avg_views_last_7_videos": avg7, "last_video_views": last["views"],
                             "last_video_id": last["id"],
                             "last_check_utc": now.strftime("%Y-%m-%dT%H:%MZ")})
                ev("Metrik diperbarui: views=%d avg7=%d" % (last["views"], avg7))
        except Exception as e:
            ev("Metrik dilewati: " + repr(e)[:80])
    else:
        ev("Metrik dilewati (butuh API key valid + channel_id)")

    trend_alert = []
    try:
        trends = fetch_trends()
        fresh = [t for t in trends if t["title"].lower()[:80] not in seen_trends]
        for t in fresh:
            seen_trends.add(t["title"].lower()[:80])
        trend_alert = fresh[:5]
        trends_prev = trends[:12]
        if fresh:
            ev(str(len(fresh)) + " tren baru terdeteksi")
    except Exception as e:
        ev("Cek tren gagal: " + repr(e)[:80])

    token = (os.environ.get("DISCORD_BOT_TOKEN", "") or "").strip()
    d_channel = (os.environ.get("DISCORD_CHANNEL_ID", "") or DEFAULT_DISCORD_CHANNEL).strip()
    d_name = "#general"

    sent_ok, sent_detail, report = None, "-", None
    if metric_alert or trend_alert:
        report = build_report(metric_alert, trend_alert, metrics)
        if token:
            head = "[WATCHDOG] " + ("METRIK TURUN " if metric_alert else "") + ("TREN BARU" if trend_alert else "")
            body = "**" + head.strip() + "**\n```\n" + report[:1750] + "\n```"
            sent_ok, sent_detail = discord_send(token, d_channel, body)
            ev("Discord: " + ("terkirim" if sent_ok else "gagal (" + sent_detail + ")"))
        else:
            sent_detail = "token bot tidak ditemukan"; ev("Discord dilewati: token tidak ada")
    else:
        ev("OK: tidak ada sinyal (senyap)")

    if metric_alert:
        say_text, say_kind, say_state = ("METRIK TURUN: " + metric_alert[0][:120] + "  Laporan sudah kukirim ke Discord.", "alert", "SIBUK")
    elif trend_alert:
        say_text, say_kind, say_state = ("Ada %d tren baru relevan. Ringkasannya sudah kukirim ke Discord." % len(trend_alert), "kerja", "BEKERJA")
    elif not api_ok:
        say_text, say_kind, say_state = ("Kunci API bermasalah. Aku belum bisa jalan, Bos.", "bingung", "BINGUNG")
    elif not ch_id:
        say_text, say_kind, say_state = ("Channel ID YouTube belum diisi. Aku belum bisa baca metrik channelmu.", "tanya", "BINGUNG")
    else:
        say_text, say_kind, say_state = ("Pemeriksaan rutin selesai. Semua aman, tidak ada sinyal.", "aman", "ISTIRAHAT")
    msgs.append({"t": now.strftime("%m-%d %H:%M"), "text": say_text, "kind": say_kind})
    msgs = msgs[-50:]

    if metric_alert:
        screen = "[ !! METRIK TURUN !! ]\n[ MENYUSUN LAPORAN ]\n\n  >> ALERT <<"
    elif trend_alert:
        screen = "[ %d TREN BARU ]\n[ RISET & IDE ]\n\n  STATUS: ANALISIS" % len(trend_alert)
    elif not api_ok:
        screen = "[ KUNCI API ]\n[ BERMASALAH ]\n\n  CEK SECRET"
    elif not ch_id:
        screen = "[ MENUNGGU ]\n[ CHANNEL ID ]\n\n  ISI SECRET"
    else:
        screen = "[ MONITORING TREN ]\n[ MENUNGGU SINYAL ]\n\n  STATUS: OK"

    st = {"api_key_ok": api_ok, "channel_id": ch_id,
          "last_run": now.strftime("%Y-%m-%d %H:%M UTC"),
          "metrics": metrics, "trends": trends_prev, "events": events[-40:],
          "messages": msgs, "say": {"text": say_text, "state": say_state, "tag": say_kind.upper()},
          "discord": {"ok": sent_ok, "channel": d_name, "detail": sent_detail},
          "alert": {"metric": bool(metric_alert), "trend": bool(trend_alert)},
          "screen_text": screen}
    build_dashboard(st, DASH_PATH)
    build_feed(st, FEED_PATH, "github-actions")

    st_file.update({"events": events[-40:], "trends": trends_prev,
                    "seen_trends": list(seen_trends)[-300:], "baseline": base,
                    "channel_id": ch_id, "messages": msgs})
    save_json(STATE_PATH, st_file)

    if report:
        print(report)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        print("FATAL: " + repr(e))
        sys.exit(1)
