#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
agent_termux.py -- SATU FILE untuk HP (Termux).  Versi 3.0
  * server dashboard di http://localhost:8765  (tab Kantor & Rekomendasi)
  * tab CHAT -> langsung ke router AI (TIDAK butuh paket hermes yang rapuh)
  * KENDALI JARAK JAUH: membaca 'kendali/antrian.json' dari GitHub, menjalankan
    perintahnya, lalu mengunggah hasilnya kembali ke repo. Jadi BOS NINU bisa
    mengatur HP ini dari laptop tanpa menyentuh HP.
Jalankan:  python agent_termux.py
"""
import os, sys, json, time, socket, base64, threading, subprocess
import urllib.request, urllib.error, urllib.parse
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

VERSI      = "3.0"
HERE       = os.path.dirname(os.path.abspath(__file__))
HOME       = os.path.expanduser("~")
CONF       = os.path.join(HOME, ".watchdog")
RAHASIA    = os.path.join(CONF, "rahasia")
LOG        = os.path.join(CONF, "agent.log")
SIDIK      = os.path.join(CONF, "sudah_dijalankan.json")
PORT       = 8765

REPO       = "ninubes-ui/youtube-watchdog"
BRANCH     = "main"
RAW        = "https://raw.githubusercontent.com/%s/%s/" % (REPO, BRANCH)
GHAPI      = "https://api.github.com/repos/%s" % REPO
PAGES      = "https://ninubes-ui.github.io/youtube-watchdog/"
ANTRIAN    = "kendali/antrian.json"
HASILDIR   = "kendali/hasil"

CHAT_STORE = os.path.join(HERE, "chat_history.json")
CHAT_MAX   = 40
CHAT_LOCK  = threading.Lock()

SISTEM = ("Kamu Agen Ninu di dashboard GROWTH ROOM milik BOS NINU. Channel YouTube: "
          "NINU BES (@ninubes-1), animasi Roblox lucu, fokus YouTube Shorts, "
          "bahasa Jawa/Indonesia. Jawab Bahasa Indonesia santai tapi TO THE POINT. "
          "Maksimal 4 baris pendek (maks 6 baris kalau diminta daftar). Tanpa pembuka, "
          "tanpa mengulang pertanyaan, tanpa markdown tebal. Kalau daftar pakai tanda - "
          "maksimal 5 baris. Kalau tidak tahu, bilang singkat.")

try:
    os.makedirs(CONF, exist_ok=True)
except Exception:
    pass


def log(msg):
    baris = "%s  %s" % (time.strftime("%d-%m %H:%M:%S"), msg)
    try:
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(baris + "\n")
    except Exception:
        pass
    try:
        print(baris)
    except Exception:
        pass


def rahasia():
    d = {"AI_KEY": "", "AI_BASE": "https://modelrouter.id/v1",
         "AI_MODEL": "mr-vip", "GH_TOKEN": ""}
    try:
        with open(RAHASIA, encoding="utf-8") as f:
            for ln in f:
                ln = ln.strip()
                if ln and not ln.startswith("#") and "=" in ln:
                    k, v = ln.split("=", 1)
                    d[k.strip()] = v.strip()
    except Exception:
        pass
    if not d["AI_KEY"]:
        d["AI_KEY"] = os.environ.get("AI_KEY", "")
    if not d["GH_TOKEN"]:
        d["GH_TOKEN"] = os.environ.get("GH_TOKEN", "")
    return d


def _chat(prompt):
    R = rahasia()
    if not R["AI_KEY"]:
        return 1, ("Kunci AI belum dipasang. Jalankan sekali: "
                   "bash ~/youtube-watchdog/pasang_kunci.sh")
    sysmsg = SISTEM + " Waktu sekarang: " + time.strftime("%d-%m-%Y %H:%M") + " WIB."
    body = json.dumps({
        "model": R["AI_MODEL"],
        "messages": [{"role": "system", "content": sysmsg},
                     {"role": "user", "content": prompt}],
        "max_tokens": 900, "temperature": 0.7,
    }).encode("utf-8")
    req = urllib.request.Request(
        R["AI_BASE"].rstrip("/") + "/chat/completions", data=body,
        headers={"Authorization": "Bearer " + R["AI_KEY"],
                 "Content-Type": "application/json",
                 "User-Agent": "agent-termux"})
    try:
        with urllib.request.urlopen(req, timeout=180) as r:
            j = json.loads(r.read().decode("utf-8", "replace"))
        m = ((j.get("choices") or [{}])[0].get("message") or {})
        txt = (m.get("content") or "").strip() or (m.get("reasoning") or "").strip()
        return 0, (txt or "(jawaban kosong dari model)")
    except urllib.error.HTTPError as e:
        if e.code in (401, 403):
            return 1, "Kunci AI ditolak (HTTP %s). Kunci salah atau limit habis." % e.code
        return 1, "Gagal hubungi AI (HTTP %s)." % e.code
    except Exception as e:
        return 1, "Gagal hubungi AI: %s" % e


def _chat_load():
    try:
        with open(CHAT_STORE, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"history": []}


def _chat_save(d):
    try:
        with open(CHAT_STORE, "w", encoding="utf-8") as f:
            json.dump(d, f, ensure_ascii=False, indent=1)
    except Exception:
        pass


def _shorten(s, max_lines=9, max_chars=900):
    lines = [ln.strip() for ln in (s or "").splitlines()]
    lines = [ln for ln in lines if ln]
    out = "\n".join(lines[:max_lines])
    if len(lines) > max_lines:
        out += "\n... (dipotong)"
    if len(out) > max_chars:
        out = out[:max_chars].rstrip() + " ..."
    return out or "\u2026"


# ------------------------------------------------------- KENDALI JARAK JAUH
def _unduh(url, timeout=25):
    req = urllib.request.Request(url, headers={"User-Agent": "agent-termux",
                                               "Cache-Control": "no-cache"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", "replace")


def _sidik_load():
    try:
        with open(SIDIK, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def _sidik_save(a):
    try:
        with open(SIDIK, "w", encoding="utf-8") as f:
            json.dump(a[-300:], f)
    except Exception:
        pass


def _gh_tulis(path, teks, pesan):
    R = rahasia()
    tok = R.get("GH_TOKEN", "")
    if not tok:
        return False, "tanpa token GitHub"
    url = "%s/contents/%s" % (GHAPI, urllib.parse.quote(path))
    sha = None
    try:
        req = urllib.request.Request(url + "?ref=" + BRANCH,
                                     headers={"Authorization": "Bearer " + tok,
                                              "User-Agent": "agent-termux"})
        with urllib.request.urlopen(req, timeout=30) as r:
            sha = json.loads(r.read().decode()).get("sha")
    except Exception:
        pass
    body = {"message": pesan, "branch": BRANCH,
            "content": base64.b64encode(teks.encode("utf-8")).decode()}
    if sha:
        body["sha"] = sha
    req = urllib.request.Request(url, data=json.dumps(body).encode("utf-8"),
                                 method="PUT",
                                 headers={"Authorization": "Bearer " + tok,
                                          "User-Agent": "agent-termux",
                                          "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.status in (200, 201), "ok"
    except urllib.error.HTTPError as e:
        return False, "HTTP %s %s" % (e.code, e.read().decode("utf-8", "replace")[:150])
    except Exception as e:
        return False, str(e)[:120]


def _jalankan(cmd):
    try:
        p = subprocess.run(["bash", "-lc", cmd], capture_output=True, text=True,
                           timeout=240, encoding="utf-8", errors="replace")
        out = (p.stdout or "") + (("\n[stderr]\n" + p.stderr) if p.stderr else "")
        return p.returncode, out.strip()[:6000]
    except subprocess.TimeoutExpired:
        return 124, "(perintah lebih dari 240 detik, dihentikan)"
    except Exception as e:
        return 1, "gagal jalankan: %s" % e


def _pembaruan():
    try:
        baru = _unduh(RAW + "agent_termux.py")
        if "agent_termux.py" not in baru[:600]:
            return "isi berkas repo tidak masuk akal, dibatalkan"
        lama = open(os.path.abspath(__file__), encoding="utf-8").read()
        if baru.strip() == lama.strip():
            return "sudah versi terbaru"
        with open(os.path.abspath(__file__), "w", encoding="utf-8", newline="\n") as f:
            f.write(baru)
        log("[pembaruan] agent diperbarui, menghidupkan ulang...")
        time.sleep(1)
        os.execv(sys.executable, [sys.executable, os.path.abspath(__file__)])
    except Exception as e:
        return "gagal: %s" % e


def _poller():
    log("[kendali] pemantau perintah aktif (tiap 20 detik)")
    sudah = _sidik_load()
    pertama = True
    while True:
        try:
            teks = _unduh(RAW + ANTRIAN + "?t=%d" % int(time.time()))
            j = json.loads(teks)
            for item in (j.get("perintah") or []):
                pid = str(item.get("id") or "").strip()
                cmd = (item.get("cmd") or "").strip()
                if not pid or not cmd or pid in sudah:
                    continue
                if not pertama:
                    log("[kendali] perintah %s -> %s" % (pid, cmd[:90]))
                    if cmd == "__update__":
                        hasil, kode = _pembaruan(), 0
                    elif cmd == "__versi__":
                        hasil, kode = "agent %s siap" % VERSI, 0
                    else:
                        kode, hasil = _jalankan(cmd)
                    _gh_tulis("%s/%s.json" % (HASILDIR, pid),
                              json.dumps({"id": pid, "cmd": cmd, "rc": kode, "out": hasil,
                                          "waktu": time.strftime("%d-%m-%Y %H:%M:%S")},
                                         ensure_ascii=False, indent=1),
                              "hasil perintah " + pid)
                    sudah.append(pid)
                    _sidik_save(sudah)
            pertama = False
        except Exception:
            pass
        time.sleep(20)


# --------------------------------------------------------------- SERVER
class H(SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def end_headers(self):
        buf = getattr(self, "_headers_buffer", None) or []
        if not any(b"Cache-Control" in h for h in buf):
            self.send_header("Cache-Control", "no-store, no-cache, must-revalidate")
            self.send_header("Pragma", "no-cache")
            self.send_header("Expires", "0")
        super().end_headers()

    def _json(self, obj, code=200):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _baru(self, name):
        lokal = None
        try:
            with open(os.path.join(HERE, name), encoding="utf-8") as f:
                lokal = json.load(f)
        except Exception:
            pass
        jauh = None
        try:
            req = urllib.request.Request(
                PAGES + name + "?t=%d" % int(time.time()),
                headers={"User-Agent": "agent-termux", "Cache-Control": "no-cache"})
            with urllib.request.urlopen(req, timeout=8) as r:
                jauh = json.loads(r.read().decode("utf-8"))
        except Exception:
            pass
        if lokal and jauh:
            return jauh if (jauh.get("ts", 0) > lokal.get("ts", 0)) else lokal
        return lokal or jauh

    def do_GET(self):
        path = self.path.split("?")[0]
        if path == "/chat_history.json":
            return self._json(_chat_load())
        if path == "/api/status":
            R = rahasia()
            return self._json({
                "ok": True, "agent": VERSI,
                "waktu": time.strftime("%d-%m-%Y %H:%M:%S"),
                "folder": HERE, "port": PORT,
                "chat_siap": bool(R["AI_KEY"]),
                "kendali_siap": bool(R["GH_TOKEN"]),
                "model": R["AI_MODEL"],
                "python": sys.version.split()[0],
            })
        if path == "/api/log":
            try:
                with open(LOG, encoding="utf-8", errors="replace") as f:
                    return self._json({"ok": True, "log": f.read().splitlines()[-40:]})
            except Exception as e:
                return self._json({"ok": False, "log": ["(belum ada log: %s)" % e]})
        if path in ("/feed.json", "/push.json", "/rekomendasi.json", "/config_state.json"):
            dd = self._baru(path.lstrip("/"))
            if dd is not None:
                return self._json(dd)
            self.send_error(404, "belum ada data")
            return
        return super().do_GET()

    def do_POST(self):
        if self.path.split("?")[0] != "/api/chat":
            return self._json({"ok": False, "error": "tidak ada"}, 404)
        try:
            n = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(n).decode("utf-8") or "{}")
        except Exception:
            return self._json({"ok": False, "error": "json rusak"}, 400)
        prompt = (body.get("message") or "").strip()
        if not prompt:
            return self._json({"ok": False, "error": "pesan kosong"}, 400)
        store = _chat_load()
        store["history"].append({"role": "user", "text": prompt, "ts": int(time.time())})
        store["history"] = store["history"][-CHAT_MAX:]
        _chat_save(store)
        with CHAT_LOCK:
            rc, out = _chat(prompt)
        out = _shorten(out)
        store = _chat_load()
        store["history"].append({"role": "bot", "text": out, "ts": int(time.time())})
        store["history"] = store["history"][-CHAT_MAX:]
        _chat_save(store)
        return self._json({"ok": rc == 0, "reply": out})


def _sudah_jalan():
    s = socket.socket()
    s.settimeout(1)
    try:
        s.connect(("127.0.0.1", PORT))
        return True
    except Exception:
        return False
    finally:
        s.close()


def main():
    url = "http://localhost:%d/index.html" % PORT
    if _sudah_jalan():
        log("dashboard SUDAH berjalan di %s" % url)
        return
    os.chdir(HERE)
    try:
        srv = ThreadingHTTPServer(("127.0.0.1", PORT), H)
    except OSError as e:
        log("port %d tidak bisa dipakai: %s" % (PORT, e))
        return
    R = rahasia()
    log("agent %s jalan di %s | chat:%s | kendali:%s" % (
        VERSI, url, "siap" if R["AI_KEY"] else "belum ada kunci",
        "siap" if R["GH_TOKEN"] else "tanpa token"))
    threading.Thread(target=_poller, daemon=True).start()
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
