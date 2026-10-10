#!/data/data/com.termux/files/usr/bin/bash
# ==========================================================
#  PENJAGA.sh -- menyalakan ulang agent kalau mati. 24/7.
#  Dijalankan sebagai:  bash penjaga.sh
#  Berhenti:  pkill -f penjaga.sh
# ==========================================================
DIR="$HOME/youtube-watchdog"
LOG="$HOME/.watchdog/agent.log"
mkdir -p "$HOME/.watchdog"
echo "$(date '+%d-%m %H:%M:%S')  [penjaga] mulai" >> "$LOG"
while true; do
  CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 6 http://localhost:8765/api/status 2>/dev/null)
  if [ "$CODE" != "200" ]; then
    echo "$(date '+%d-%m %H:%M:%S')  [penjaga] agent tidak menjawab (${CODE:-kosong}) -> dinyalakan ulang" >> "$LOG"
    pkill -f agent_termux.py 2>/dev/null
    sleep 1
    cd "$DIR" 2>/dev/null && nohup python agent_termux.py >> "$LOG" 2>&1 &
  fi
  sleep 45
done
