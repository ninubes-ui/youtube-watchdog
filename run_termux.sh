#!/data/data/com.termux/files/usr/bin/bash
# ============================================================
#  JALANKAN DASHBOARD (HP / Termux)  ->  bash run_termux.sh
#  Aman dijalankan berulang: mematikan server lama dulu.
# ============================================================
cd "$(dirname "$0")" || exit 1
echo "== folder: $(pwd)"

if ! command -v python >/dev/null 2>&1; then
  echo "[!!] python belum ada. Jalankan: pkg install -y python"
  exit 1
fi

termux-wake-lock 2>/dev/null

pkill -f dashboard_server.py 2>/dev/null
sleep 1

nohup python dashboard_server.py > server.log 2>&1 &
sleep 3

CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8765/index.html 2>/dev/null)
if [ "$CODE" = "200" ]; then
  echo "[OK] server hidup (HTTP 200)"
  echo "     Buka: http://localhost:8765/index.html"
else
  echo "[!!] server belum menjawab (HTTP ${CODE:-kosong}). 12 baris log terakhir:"
  tail -n 12 server.log 2>/dev/null
  echo "     Cek: python dashboard_server.py  (jalankan langsung untuk lihat error)"
fi
