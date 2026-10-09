#!/data/data/com.termux/files/usr/bin/bash
# ============================================================
#  SETUP TERMUX - YouTube Growth Watchdog + Dashboard (HP Android)
#  Menjadikan HP Android sebagai "server mini" 24 jam (tanpa VPS).
#  Pakai:  bash SETUP_TERMUX.sh
# ============================================================
set -e
echo "== 1/6  Perbarui paket Termux =="
pkg update -y && pkg upgrade -y

echo "== 2/6  Pasang alat dasar (python, git, curl) =="
pkg install -y python git curl

echo "== 3/6  Ambil proyek dari GitHub =="
cd "$HOME"
if [ -d youtube-watchdog ]; then
  cd youtube-watchdog && git pull --ff-only || true
else
  git clone https://github.com/ninubes-ui/youtube-watchdog.git
  cd youtube-watchdog
fi

echo "== 4/6  Coba pasang Hermes Agent (agar fitur CHAT hidup) =="
echo "   (kalau gagal, lewati saja: watchdog + dashboard tetap jalan, chat saja yang mati)"
if command -v hermes >/dev/null 2>&1; then
  echo "   hermes sudah terpasang."
else
  mkdir -p "$PREFIX/etc/apt/keyrings"
  curl -fsSL https://hermes-assets.nousresearch.com/releases/termux/stable/key.asc \
       -o "$PREFIX/etc/apt/keyrings/hermes-agent.asc" || echo "   (gagal unduh kunci)"
  printf '%s\n' "deb [signed-by=$PREFIX/etc/apt/keyrings/hermes-agent.asc] https://hermes-assets.nousresearch.com/releases/termux/stable hermes-stable main" \
       > "$PREFIX/etc/apt/sources.list.d/hermes-agent.list"
  pkg update -y || true
  pkg install -y hermes-agent || echo "   >>> Paket hermes-agent GAGAL. Tidak masalah, lanjut."
fi

echo "== 5/6  Cegah Android mematikan proses (baterai) =="
termux-wake-lock 2>/dev/null || echo "   (termux-wake-lock tak tersedia; matikan optimasi baterai manual)"

echo "== 6/6  Selesai. Cara menjalankan: =="
cat <<'EOF'

--------------------------------------------------------------
  MENJALANKAN  (tiap kali HP/node baru dibuka):

    cd ~/youtube-watchdog
    termux-wake-lock
    nohup python dashboard_server.py > server.log 2>&1 &

  Lalu buka di browser HP:  http://localhost:8765/index.html

  CHAT: butuh perintah `hermes`. Set provider dulu sekali:
      hermes setup
  (kalau langkah 4 gagal, tab Chat tak bisa dipakai; sisanya jalan)

  AGAR JALAN SENDIRI SAAT HP REBOOT:
    pkg install -y termux-boot        # lalu aktifkan Termux:Boot di app
    mkdir -p ~/.termux/boot
    cat > ~/.termux/boot/start-watchdog.sh <<'SH'
    #!/data/data/com.termux/files/usr/bin/sh
    termux-wake-lock
    cd $HOME/youtube-watchdog
    nohup python dashboard_server.py >> server.log 2>&1 &
    SH
    chmod +x ~/.termux/boot/start-watchdog.sh

  Cek jalan?:
    curl -s http://localhost:8765/feed.json | head -c 200

  Hentikan:
    pkill -f dashboard_server.py
--------------------------------------------------------------
EOF
