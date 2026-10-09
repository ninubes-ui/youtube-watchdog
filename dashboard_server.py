#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DASHBOARD SERVER (GROWTH ROOM)
Menyajikan dashboard di http://localhost:8765/index.html
Bonus: /feed.json otomatis digabung dengan versi TERBARU dari GitHub Pages,
sehingga dashboard selalu LIVE walau laptop baru dinyalakan.
"""
import os, sys, json, time, socket, webbrowser, urllib.request, urllib.error, subprocess, threading, re
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

HERE   = os.path.dirname(os.path.abspath(__file__))
CHAT_SESSION = {"id": None, "lock": threading.Lock()}
CHAT_STORE  = os.path.join(HERE, "chat_history.json")

HERE   = os.path.dirname(os.path.abspath(__file__))
PORT   = 8765
REMOTE = "https://ninubes-ui.github.io/youtube-watchdog/"
REPO_PUSH = "https://raw.githubusercontent.com/ninubes-ui/youtube-watchdog/main/"
CHAT_MAX  = 40
BREVIS = ("Kamu Agen Ninu di dashboard GROWTH ROOM. Jawab Bahasa Indonesia, santai tapi TO THE POINT. WAJIB maksimal 4 baris pendek (maks 6 baris kalau diminta daftar). Tanpa pembuka, tanpa mengulang pertanyaan, tanpa markdown. Kalau daftar pakai \"-\" maksimal 5 baris. Kalau tidak tahu, bilang singkat. ")

def _read_local(name):
    p = os.path.join(HERE, name)
    try:
        with open(p, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None

def _read_remote(name):
    try:
        req = urllib.request.Request(REMOTE + name + "?t=%d" % int(time.time()),
                                     headers={"User-Agent": "growth-room", "Cache-Control": "no-cache"})
        with urllib.request.urlopen(req, timeout=8) as r:
            return json.loads(r.read().decode("utf-8"))
    except Exception:
        return None

def _newest(name):
    a, b = _read_local(name), _read_remote(name)
    if a and b:
        return b if (b.get("ts", 0) > a.get("ts", 0)) else a
    return a or b

def _chat_load():
    try:
        with open(CHAT_STORE, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"history": []}

def _chat_save(d):
    with open(CHAT_STORE, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=1)

_ANSI = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")

def _clean(raw):
    """Buang blok 'Reasoning' (baris redup ANSI) + kode ANSI dari output hermes."""
    raw = raw or ""
    out, started = [], False
    for ln in raw.split("\n"):
        if not started:
            if not ln.strip():
                continue
            if ln.startswith("\x1b[2;3m") or "\u250c\u2500" in ln or "\u2502" in ln:
                continue
            started = True
        out.append(ln)
    s = _ANSI.sub("", "\n".join(out))
    s = re.sub(r"[\u2500\u2502\u250c\u2510\u2514\u2518\u251c\u2524\u252c\u2534\u253c\u2550\u2554\u2557\u255a\u255d\u2560\u2563]+", "", s)
    s = re.sub(r"\n{3,}", "\n\n", s)
    return s.strip()

def _shorten(s, max_lines=9, max_chars=900):
    lines = [ln.strip() for ln in (s or "").splitlines()]
    lines = [ln for ln in lines if ln]
    out = "\n".join(lines[:max_lines])
    if len(lines) > max_lines:
        out += "\n... (dipotong)"
    if len(out) > max_chars:
        out = out[:max_chars].rstrip() + " ..."
    return out or "\u2026"

def _chat_run(prompt):
    """Jalankan hermes chat (non-interaktif) + resume sesi; balasan dibersihkan."""
    try:
        with CHAT_SESSION["lock"]:
            full = BREVIS + "Pesan dari BOS: " + prompt + "\n(Jawab singkat & to the point.)"
            cmd = ["hermes", "chat", "-q", full, "-Q"]
            if CHAT_SESSION["id"]:
                cmd += ["--resume", CHAT_SESSION["id"]]
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=280,
                               encoding="utf-8", errors="replace")
            sid = CHAT_SESSION["id"]
            m = re.search(r"session_id:\s*(\S+)", r.stderr or "")
            if m:
                sid = m.group(1)
                CHAT_SESSION["id"] = sid
            return r.returncode, _clean(r.stdout or ""), sid
    except Exception as e:
        return 1, "Error server: %s" % e, CHAT_SESSION.get("id")

def _wg_log(q, a):
    try:
        p = os.path.join(HERE, "messages.json")
        try:
            with open(p, encoding="utf-8") as f: arr = json.load(f)
        except Exception: arr = []
        if not isinstance(arr, list): arr = []
        t = time.strftime("%m-%d %H:%M")
        arr.append({"t": t, "text": "BOS: " + q.replace("\n"," ")[:80], "kind": "chat"})
        arr.append({"t": t, "text": "Agen: " + a.replace("\n"," ")[:120], "kind": "chat"})
        with open(p, "w", encoding="utf-8") as f:
            json.dump(arr[-40:], f, ensure_ascii=False, indent=1)
    except Exception:
        pass

class H(SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass
    def _json(self, obj, code=200):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = self.path.split("?")[0]
        if path == "/chat_history.json":
            return self._json(_chat_load())
        if path in ("/feed.json", "/push.json"):
            d = _newest(path.lstrip("/"))
            if d is not None:
                return self._json(d)
            self.send_error(404, "belum ada data"); return
        return super().do_GET()

    def do_POST(self):
        path = self.path.split("?")[0]
        if path == "/api/chat":
            try:
                n = int(self.headers.get("Content-Length", 0))
                body = json.loads(self.rfile.read(n).decode("utf-8") or "{}")
            except Exception:
                return self._json({"ok": False, "error": "bad json"}, 400)
            prompt = (body.get("message") or "").strip()
            if not prompt:
                return self._json({"ok": False, "error": "pesan kosong"}, 400)
            store = _chat_load()
            store["history"].append({"role": "user", "text": prompt,
                                     "ts": int(time.time())})
            if len(store["history"]) > CHAT_MAX:
                store["history"] = store["history"][-CHAT_MAX:]
            _chat_save(store)
            rc, out, _sid = _chat_run(prompt)
            out = _shorten(out)
            store = _chat_load()
            store["history"].append({"role": "bot", "text": out,
                                     "ts": int(time.time())})
            if len(store["history"]) > CHAT_MAX:
                store["history"] = store["history"][-CHAT_MAX:]
            _chat_save(store)
            _wg_log(prompt, out)
            return self._json({"ok": rc == 0, "reply": out})
        return self._json({"ok": False, "error": "not found"}, 404)

def _already_running():
    s = socket.socket(); s.settimeout(1)
    try:
        s.connect(("127.0.0.1", PORT)); return True
    except Exception:
        return False
    finally:
        s.close()

def main():
    url = "http://localhost:%d/index.html" % PORT
    if _already_running():
        print("Dashboard SUDAH berjalan.")
        print("Buka: %s" % url)
        try: webbrowser.open(url)
        except Exception: pass
        return
    os.chdir(HERE)
    try:
        srv = ThreadingHTTPServer(("127.0.0.1", PORT), H)
    except OSError as e:
        print("Tidak bisa menyalakan server di port %d: %s" % (PORT, e))
        return
    print("GROWTH ROOM server jalan di %s" % url)
    print("Tekan Ctrl+C (atau tutup jendela ini) untuk mematikan.")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    main()
