#!/data/data/com.termux/files/usr/bin/bash
# ============================================================
#  NYALAKAN GROWTH ROOM (HP / Termux)
#     bash run_termux.sh
#  Aman dijalankan berulang: mematikan agent lama dulu.
# ============================================================
cd "$(dirname "$0")" || exit 1
echo "== folder: $(pwd)"

if ! command -v python >/dev/null 2>&1; then
  echo "[!!] python belum ada. Jalankan: pkg install -y python"
  exit 1
fi

if [ ! -f "$HOME/.watchdog/rahasia" ]; then
  echo "[!!] kunci belum dipasang -> tab Chat akan bilang 'Kunci AI belum dipasang'"
  echo "     jalankan sekali: bash pasang_kunci.sh"
fi

termux-wake-lock 2>/dev/null
pkill -f agent_termux.py 2>/dev/null
pkill -f dashboard_server.py 2>/dev/null
sleep 1

nohup python agent_termux.py >> "$HOME/.watchdog/agent.log" 2>&1 &
sleep 4

CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8765/index.html 2>/dev/null)
if [ "$CODE" = "200" ]; then
  echo "[OK] Growth Room HIDUP  (HTTP 200)"
  echo "     Buka: http://localhost:8765/index.html"
  echo "     Cek : http://localhost:8765/api/status"
  termux-open-url "http://localhost:8765/index.html" >/dev/null 2>&1 || true
else
  echo "[!!] belum menjawab (HTTP ${CODE:-kosong}). 15 baris log terakhir:"
  tail -n 15 "$HOME/.watchdog/agent.log" 2>/dev/null
fi
