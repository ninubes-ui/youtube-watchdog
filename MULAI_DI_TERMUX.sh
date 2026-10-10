#!/data/data/com.termux/files/usr/bin/bash
# ==========================================================================
#  MULAI_DI_TERMUX.sh  --  SEKALI JALAN  (v3)
#  YouTube Growth Room milik BOS NINU
#
#  v3 TIDAK memakai paket hermes (itu penyebab gagal berulang).
#  Sekarang pakai agent_termux.py: dashboard + chat + kendali jarak jauh.
#  Unduhannya KECIL (ratusan KB), bukan 171 MB.
#
#  CARA PAKAI (di Termux):
#     pkg install -y curl
#     curl -fsSL https://raw.githubusercontent.com/ninubes-ui/youtube-watchdog/main/MULAI_DI_TERMUX.sh -o mulai.sh && bash mulai.sh
#     bash pasang_kunci.sh <KUNCI_AI> <TOKEN_GITHUB>      <- kunci dari BOS NINU
# ==========================================================================
set -u
umask 022

REPO_RAW="https://raw.githubusercontent.com/ninubes-ui/youtube-watchdog/main"
PROJDIR="$HOME/youtube-watchdog"
LOGDIR="$HOME/.watchdog"
mkdir -p "$LOGDIR" "$PROJDIR"
LOG="$LOGDIR/mulai.log"; : > "$LOG"

WARN=0; FAIL=0
say()  { printf '\n\033[1m== %s ==\033[0m\n' "$1" 2>/dev/null | tee -a "$LOG"; }
ok()   { printf '   [OK] %s\n' "$1" | tee -a "$LOG"; }
warn() { printf '   [!!] %s\n' "$1" | tee -a "$LOG"; WARN=$((WARN+1)); }
bad()  { printf '   [XX] %s\n' "$1" | tee -a "$LOG"; FAIL=$((FAIL+1)); }

echo "==============================================" | tee -a "$LOG"
echo "  YOUTUBE GROWTH ROOM  --  PASANG DI HP (v3)"    | tee -a "$LOG"
echo "  tanpa paket hermes; unduhan kecil"            | tee -a "$LOG"
echo "==============================================" | tee -a "$LOG"
echo "log: $LOG"
date | tee -a "$LOG"

# ---------------------------------------------------------------- 1/7
say "1/7 Cek ini benar Termux?"
if [ -n "${PREFIX:-}" ] && [ -d "${PREFIX:-/nonexistent}" ]; then
  ok "Termux terdeteksi"
else
  bad "Bukan Termux. Skrip ini KHUSUS Termux di Android."
  exit 1
fi
echo "   arsitektur: $(uname -m 2>/dev/null)"

# ---------------------------------------------------------------- 2/7
say "2/7 Alat dasar: python curl (cepat, tidak ada unduhan besar)"
if pkg update -y >/dev/null 2>&1; then ok "indeks paket diperbarui"; else warn "pkg update dilewati (tidak fatal)"; fi
for p in python curl; do
  if command -v "$p" >/dev/null 2>&1; then ok "$p sudah ada"
  elif pkg install -y "$p" >/dev/null 2>&1; then ok "$p terpasang"
  else warn "$p gagal dipasang"
  fi
done
if ! command -v python >/dev/null 2>&1; then bad "python TIDAK ada -> dashboard tidak bisa jalan"; fi

# ---------------------------------------------------------------- 3/7
say "3/7 Ambil berkas proyek dari GitHub"
cd "$PROJDIR" || exit 1
GOT=0
if command -v git >/dev/null 2>&1; then
  if [ -d .git ]; then
    if git pull --ff-only >/dev/null 2>&1; then ok "proyek di-update (git pull)"; GOT=1
    else ok "proyek sudah ada (versi lokal)"; GOT=1; fi
  elif git clone --depth 1 "https://github.com/ninubes-ui/youtube-watchdog.git" . >/dev/null 2>&1; then
    ok "proyek di-clone (git)"; GOT=1
  fi
fi
if [ "$GOT" -eq 0 ]; then
  warn "git tidak ada/gagal -> unduh berkas satu per satu"
  for f in agent_termux.py index.html run_termux.sh pasang_kunci.sh penjaga.sh; do
    if curl -fsSL "$REPO_RAW/$f" -o "$f" 2>/dev/null && [ -s "$f" ]; then
      echo "   [OK] $f"
    else
      warn "gagal unduh $f"
    fi
  done
fi
if [ -s "$PROJDIR/agent_termux.py" ]; then ok "agent_termux.py siap ($(wc -c < "$PROJDIR/agent_termux.py") byte)"
else bad "agent_termux.py TIDAK ada -> server tidak bisa jalan"; fi
if [ -s "$PROJDIR/index.html" ]; then ok "index.html siap"
else bad "index.html TIDAK ada -> halaman dashboard kosong"; fi

# ---------------------------------------------------------------- 4/7
say "4/7 Kunci (untuk tab Chat + kendali jarak jauh)"
if [ -s "$LOGDIR/rahasia" ]; then
  grep -q '^AI_KEY=.\+' "$LOGDIR/rahasia" && ok "kunci AI TERBACA" || bad "kunci AI kosong -> tab Chat mati"
  grep -q '^GH_TOKEN=.\+' "$LOGDIR/rahasia" && ok "token GitHub TERBACA (kendali jarak jauh hidup)" || warn "token GitHub kosong (kendali jarak jauh mati)"
else
  warn "kunci belum dipasang. Jalankan sekali:"
  echo "        bash ~/youtube-watchdog/pasang_kunci.sh <KUNCI_AI> <TOKEN_GITHUB>"
  echo "        (kuncinya dikirim BOS NINU lewat chat, JANGAN dibagikan)"
fi

# ---------------------------------------------------------------- 5/7
say "5/7 Biarkan Termux hidup di latar"
if command -v termux-wake-lock >/dev/null 2>&1; then
  termux-wake-lock 2>/dev/null && ok "wake-lock aktif" || warn "wake-lock gagal (pkg install termux-api + buka app Termux:API)"
else
  warn "termux-wake-lock tidak ada (pkg install termux-api + buka app Termux:API)"
fi

# ---------------------------------------------------------------- 6/7
say "6/7 Nyalakan server + penjaga otomatis"
if ! command -v python >/dev/null 2>&1; then
  bad "python tidak ada -> server tidak dinyalakan"
else
  pkill -f agent_termux.py 2>/dev/null || true
  sleep 1
  nohup python agent_termux.py >> "$LOGDIR/agent.log" 2>&1 &
  sleep 4
  CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 8 http://localhost:8765/index.html 2>/dev/null)
  if [ "$CODE" = "200" ]; then
    ok "SERVER HIDUP -> http://localhost:8765/index.html"
    termux-open-url "http://localhost:8765/index.html" >/dev/null 2>&1 && ok "browser dibuka otomatis" || echo "   buka manual: http://localhost:8765/index.html"
  else
    bad "server belum menjawab (HTTP ${CODE:-000}). Baris log terakhir:"
    tail -n 12 "$LOGDIR/agent.log" 2>/dev/null | sed 's/^/       /'
  fi
  pkill -f penjaga.sh 2>/dev/null || true
  nohup bash penjaga.sh >/dev/null 2>&1 &
  ok "penjaga aktif (menyalakan ulang otomatis, cek tiap 45 detik)"
fi

# ---------------------------------------------------------------- 7/7
say "7/7 Auto-jalan saat HP reboot + pintasan"
mkdir -p "$HOME/.termux/boot" 2>/dev/null
cat > "$HOME/.termux/boot/start-growthroom.sh" <<'EOBOOT'
#!/data/data/com.termux/files/usr/bin/sh
termux-wake-lock
cd $HOME/youtube-watchdog
nohup python agent_termux.py >> $HOME/.watchdog/agent.log 2>&1 &
nohup bash penjaga.sh >/dev/null 2>&1 &
EOBOOT
chmod +x "$HOME/.termux/boot/start-growthroom.sh" 2>/dev/null && ok "siap (butuh app Termux:Boot dibuka sekali)" || warn "boot script gagal dibuat"
mkdir -p "$HOME/.shortcuts" 2>/dev/null
printf 'cd $HOME/youtube-watchdog && bash run_termux.sh\n' > "$HOME/.shortcuts/Nyalakan Growth Room.sh" 2>/dev/null
chmod +x "$HOME/.shortcuts/Nyalakan Growth Room.sh" 2>/dev/null || true

say "RINGKASAN"
echo "   peringatan: $WARN   |   masalah: $FAIL" | tee -a "$LOG"
if [ "$FAIL" -eq 0 ]; then
  echo "   STATUS: BERHASIL - Growth Room sudah hidup di HP ini." | tee -a "$LOG"
  [ "$WARN" -gt 0 ] && echo "   (ada $WARN peringatan kecil, lihat baris [!!] di atas)" | tee -a "$LOG"
else
  echo "   STATUS: SEBAGIAN GAGAL - kirim isi log ini ke BOS NINU:" | tee -a "$LOG"
  echo "     $LOG" | tee -a "$LOG"
fi
cat <<'EOF' | tee -a "$LOG"

   BUKA LAGI NANTI (setelah HP di-restart):
       cd ~/youtube-watchdog && bash run_termux.sh

   MATIKAN:
       pkill -f agent_termux.py ; pkill -f penjaga.sh

   LIHAT CATATAN:
       cat ~/.watchdog/agent.log
EOF
echo "=============================================="
printf 'selesai pada %s\n' "$(date '+%H:%M:%S')"
