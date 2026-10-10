#!/data/data/com.termux/files/usr/bin/bash
# ============================================================
#  SETUP TERMUX v2 - YouTube Growth Watchdog + Dashboard (HP Android)
#  TAHAN-GAGAL: tiap langkah dicek sendiri. Satu langkah gagal
#  TIDAK menghentikan sisanya (ini penyebab error "mentok" sebelumnya).
#  Pakai:   bash setup.sh
# ============================================================
say()  { printf '\n== %s ==\n' "$1"; }
ok()   { printf '   [OK] %s\n' "$1"; }
warn() { printf '   [!!] %s\n' "$1"; }

say "0/6 Cek lingkungan"
if [ -z "${PREFIX:-}" ]; then warn "PREFIX kosong -> ini bukan Termux standar"; else ok "PREFIX=$PREFIX"; fi
ok "arsitektur: $(uname -m)"

say "1/6 Perbarui indeks paket (tidak wajib sukses)"
if pkg update -y >/dev/null 2>&1; then ok "pkg update selesai"; else warn "pkg update gagal/dilewati (tidak fatal)"; fi

say "2/6 Pasang alat dasar: python git curl gnupg termux-api"
for p in python git curl gnupg termux-api; do
  if pkg install -y "$p" >/dev/null 2>&1; then ok "$p terpasang"
  else warn "$p GAGAL dipasang"; fi
done

say "3/6 Ambil proyek dari GitHub"
cd "$HOME" || exit 1
if [ -d "$HOME/youtube-watchdog/.git" ]; then
  cd "$HOME/youtube-watchdog" || exit 1
  if git pull --ff-only >/dev/null 2>&1; then ok "repo di-update"; else warn "git pull gagal (lanjut versi lama)"; fi
elif [ -d "$HOME/youtube-watchdog" ]; then
  cd "$HOME/youtube-watchdog" || exit 1; ok "folder sudah ada"
else
  if git clone --depth 1 https://github.com/ninubes-ui/youtube-watchdog.git "$HOME/youtube-watchdog" >/dev/null 2>&1; then
    cd "$HOME/youtube-watchdog" || exit 1; ok "repo di-clone"
  else
    warn "git clone GAGAL (cek internet / 'pkg install git')"
  fi
fi
if [ -f "$HOME/youtube-watchdog/dashboard_server.py" ]; then ok "dashboard_server.py ADA"; else warn "dashboard_server.py TIDAK ada"; fi

say "4/6 Hermes Agent (fitur CHAT) -> pakai channel CANARY"
# Catatan: channel 'stable' saat ini KOSONG (404). Canary tersedia & ter-update.
if command -v hermes >/dev/null 2>&1; then
  ok "hermes sudah terpasang"
else
  mkdir -p "$PREFIX/etc/apt/keyrings"
  if curl -fsSL https://hermes-assets.nousresearch.com/releases/termux/canary/key.asc -o "$PREFIX/etc/apt/keyrings/hermes-agent.asc"; then
    ok "kunci repo diunduh"
    FP=$(gpg --show-keys --with-fingerprint "$PREFIX/etc/apt/keyrings/hermes-agent.asc" 2>/dev/null | grep -oE '([0-9A-F]{4} ){9}[0-9A-F]{4}' | head -1)
    if [ -n "$FP" ]; then ok "fingerprint: $FP"; else warn "fingerprint tak terbaca"; fi
    printf '%s\n' "deb [signed-by=$PREFIX/etc/apt/keyrings/hermes-agent.asc] https://hermes-assets.nousresearch.com/releases/termux/canary hermes-canary main" > "$PREFIX/etc/apt/sources.list.d/hermes-agent.list"
    ok "repo hermes (canary) ditambahkan"
    pkg update -y >/dev/null 2>&1
    if pkg install -y hermes-agent; then ok "hermes-agent TERPASANG (chat hidup)"; else warn "hermes-agent GAGAL -> chat mati, watchdog & dashboard tetap jalan"; fi
  else
    warn "gagal unduh kunci repo -> lewati Hermes (chat mati, sisanya jalan)"
  fi
fi

say "5/6 Cegah Android mematikan proses"
if termux-wake-lock 2>/dev/null; then ok "wake-lock aktif"; else warn "termux-wake-lock tak tersedia (pasang app Termux:API dari F-Droid)"; fi
warn "Matikan juga 'Optimasi baterai' untuk Termux di Setelan Android."

say "6/6 SELESAI. Cara menjalankan:"
cat <<'EOF'

  cd ~/youtube-watchdog
  bash run_termux.sh

  lalu buka di browser HP:   http://localhost:8765/index.html

  Kalau tab Chat perlu provider (sekali saja):
      hermes setup

  AUTO-JALAN saat HP reboot (opsional):
      pkg install -y termux-boot
      mkdir -p ~/.termux/boot
      printf '#!/data/data/com.termux/files/usr/bin/sh\ntermux-wake-lock\ncd $HOME/youtube-watchdog\nnohup python dashboard_server.py >> server.log 2>&1 &\n' > ~/.termux/boot/start-watchdog.sh
      chmod +x ~/.termux/boot/start-watchdog.sh

  MATIKAN server:
      pkill -f dashboard_server.py
EOF
