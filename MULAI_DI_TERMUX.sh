#!/data/data/com.termux/files/usr/bin/bash
# ==========================================================================
#  MULAI_DI_TERMUX.sh   --   SATU FILE, SEKALI JALAN, LANGSUNG HIDUP
#  YouTube Growth Room (BOS NINU)  +  Hermes Agent
#  Dibuat 10-10-2026. Tahan-gagal: satu langkah gagal tidak menghentikan
#  sisanya. Setiap masalah dicatat di baris RINGKASAN paling bawah.
#
#  CARA PAKAI (di Termux, copy-paste 3 baris ini):
#     pkg install -y curl
#     curl -fsSL https://raw.githubusercontent.com/ninubes-ui/youtube-watchdog/main/MULAI_DI_TERMUX.sh -o mulai.sh
#     bash mulai.sh
# ==========================================================================
set -u
umask 022

REPO_RAW="https://raw.githubusercontent.com/ninubes-ui/youtube-watchdog/main"
REPO_SAFE="https://github.com/ninubes-ui/youtube-watchdog.git"
KEYFP="C572B5FDD1A29CCFA9A912B6840B0848E139156D"
PROJDIR="$HOME/youtube-watchdog"
LOGDIR="$HOME/.watchdog"
mkdir -p "$LOGDIR"
LOG="$LOGDIR/mulai.log"; : > "$LOG"

WARN=0; FAIL=0; ARCH_OK=1
say()  { printf '\n\033[1m== %s ==\033[0m\n' "$1" | tee -a "$LOG"; }
ok()   { printf '   [OK] %s\n' "$1" | tee -a "$LOG"; }
warn() { printf '   [!!] %s\n' "$1" | tee -a "$LOG"; WARN=$((WARN+1)); }
bad()  { printf '   [XX] %s\n' "$1" | tee -a "$LOG"; FAIL=$((FAIL+1)); }

echo "==============================================" | tee -a "$LOG"
echo "  YOUTUBE GROWTH ROOM  --  PASANG DI HP"        | tee -a "$LOG"
echo "  (butuh internet; paket Hermes ~171 MB)"        | tee -a "$LOG"
echo "==============================================" | tee -a "$LOG"
echo "log: $LOG"
date | tee -a "$LOG"

# ---------------------------------------------------------------- 1/8
say "1/8 Cek ini benar Termux?"
if [ -n "${PREFIX:-}" ] && [ -d "${PREFIX:-/nonexistent}" ]; then
  ok "Termux terdeteksi (PREFIX=$PREFIX)"
else
  bad "Bukan Termux (PREFIX kosong). Skrip ini KHUSUS Termux di Android."
  echo "   -> berhenti. Kalau di laptop, pakai buka_dashboard.bat."
  exit 1
fi
ARCH=$(uname -m 2>/dev/null || echo "tidak-diketahui")
echo "   arsitektur: $ARCH"
case "$ARCH" in
  aarch64|arm64) ok "arsitektur didukung (paket tersedia)" ;;
  *) ARCH_OK=0; warn "arsitektur '$ARCH' tanpa paket Hermes; dashboard tetap bisa jalan" ;;
esac

# ---------------------------------------------------------------- 2/8
say "2/8 Alat dasar: python git curl gnupg termux-api"
if pkg update -y >/dev/null 2>&1; then ok "indeks paket diperbarui"; else warn "pkg update dilewati/gagal (tidak fatal)"; fi
for p in python git curl gnupg termux-api; do
  if command -v "$p" >/dev/null 2>&1; then ok "$p sudah ada"
  elif pkg install -y "$p" >/dev/null 2>&1; then ok "$p terpasang"
  else warn "$p gagal dipasang"; fi
done
if ! command -v python >/dev/null 2>&1; then bad "python TIDAK ada -> dashboard tidak bisa jalan!"; fi

# ---------------------------------------------------------------- 3/8
say "3/8 Ambil folder proyek"
if [ -f "$PROJDIR/dashboard_server.py" ]; then
  cd "$PROJDIR" || bad "tidak bisa masuk $PROJDIR"
  if command -v git >/dev/null 2>&1 && [ -d .git ] && git pull --ff-only >/dev/null 2>&1; then
    ok "proyek di-update ke versi terbaru"
  else
    ok "proyek sudah ada (pakai versi lokal)"
  fi
else
  mkdir -p "$PROJDIR"
  GOT=0
  if command -v git >/dev/null 2>&1; then
    for BR in main master; do
      if git clone --depth 1 -b "$BR" "$REPO_SAFE" "$PROJDIR" >/dev/null 2>&1; then
        ok "proyek di-clone (git, cabang $BR)"; GOT=1; break
      fi
      rm -rf "$PROJDIR"; mkdir -p "$PROJDIR"
    done
  fi
  if [ "$GOT" -eq 0 ]; then
    warn "git clone gagal -> unduh berkas satu per satu (mode langsung)"
    cd "$PROJDIR" || exit 1
    for f in dashboard_server.py index.html run_termux.sh CARA_PAKAI_TERMUX.txt; do
      if curl -fsSL "$REPO_RAW/$f" -o "$f" 2>/dev/null && [ -s "$f" ]; then
        echo "   [OK] $f"
      else
        warn "gagal unduh $f"
      fi
    done
  fi
  cd "$PROJDIR" 2>/dev/null || true
fi
if [ -f "$PROJDIR/dashboard_server.py" ]; then
  ok "dashboard_server.py siap"
else
  bad "dashboard_server.py TIDAK ada -> dashboard tidak bisa jalan"
fi

# ---------------------------------------------------------------- 4/8
say "4/8 Hermes Agent (untuk tab CHAT)"
if command -v hermes >/dev/null 2>&1; then
  ok "hermes sudah terpasang"
elif [ "$ARCH_OK" -eq 0 ]; then
  bad "hermes dilewati: arsitektur $ARCH tidak didukung paket resmi"
else
  KEYRING="$PREFIX/etc/apt/keyrings/hermes-agent.asc"
  SRCLIST="$PREFIX/etc/apt/sources.list.d/hermes-agent.list"
  mkdir -p "$PREFIX/etc/apt/keyrings"
  if curl -fsSL --retry 3 -o "$KEYRING" "https://hermes-assets.nousresearch.com/releases/termux/canary/key.asc"; then
    echo "   sidik jari kunci yang diharapkan: $KEYFP"
    FPGOT=$(gpg --show-keys --with-fingerprint "$KEYRING" 2>/dev/null | tr -d ' ' | grep -o -i -E "$KEYFP" | head -n 1)
    if [ -n "$FPGOT" ]; then
      ok "kunci repo resmi terverifikasi (sidik jari COCOK)"
    else
      warn "sidik jari kunci tidak terbaca (gpg bermasalah) - lanjut hati-hati"
    fi
    printf 'deb [signed-by=%s] https://hermes-assets.nousresearch.com/releases/termux/canary hermes-canary main\n' "$KEYRING" > "$SRCLIST"
    ok "sumber paket resmi (channel canary) ditambahkan"
    pkg update -y >/dev/null 2>&1 || true
    echo "   mengunduh paket ~171 MB, mohon sabar (bisa 5-15 menit)..."
    if pkg install -y hermes-agent; then
      ok "hermes-agent TERPASANG (tab Chat hidup)"
    else
      bad "hermes-agent gagal dipasang -> tab Chat mati. Tab Kantor & Rekomendasi tetap jalan."
    fi
  else
    bad "gagal unduh kunci repo -> tab Chat mati. Tab Kantor & Rekomendasi tetap jalan."
  fi
fi

# ---------------------------------------------------------------- 5/8
say "5/8 Izinkan Termux tetap hidup di latar"
if command -v termux-wake-lock >/dev/null 2>&1; then
  if termux-wake-lock 2>/dev/null; then
    ok "wake-lock aktif"
  else
    warn "termux-wake-lock gagal (pasang+ buka app 'Termux:API' dari F-Droid)"
  fi
else
  warn "termux-wake-lock tidak ada (pasang+ buka app 'Termux:API' dari F-Droid)"
fi
echo "   Setelan Android: matikan 'Optimasi baterai' untuk Termux"
echo "   Setelan Android: izinkan notifikasi Termux"

# ---------------------------------------------------------------- 6/8
say "6/8 Nyalakan server dashboard"
mkdir -p "$PROJDIR"
RUNNER="$PROJDIR/run_termux.sh"
if [ ! -f "$RUNNER" ]; then
  cat > "$RUNNER" <<'EORUN'
#!/data/data/com.termux/files/usr/bin/bash
cd "$(dirname "$0")" || exit 1
termux-wake-lock 2>/dev/null
pkill -f dashboard_server.py 2>/dev/null
sleep 1
nohup python dashboard_server.py > server.log 2>&1 &
sleep 3
curl -s -o /dev/null -w "HTTP: %{http_code}\n" http://localhost:8765/index.html
tail -n 12 server.log
EORUN
  chmod +x "$RUNNER" 2>/dev/null || true
fi
if command -v python >/dev/null 2>&1; then
  cd "$PROJDIR" || exit 1
  pkill -f dashboard_server.py 2>/dev/null || true
  sleep 1
  nohup python dashboard_server.py > server.log 2>&1 &
  sleep 4
  CODE=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:8765/index.html" 2>/dev/null)
  if [ "$CODE" = "200" ]; then
    ok "SERVER HIDUP  ->  http://localhost:8765/index.html"
    if termux-open-url "http://localhost:8765/index.html" >/dev/null 2>&1; then
      ok "browser dibuka otomatis"
    else
      echo "   buka manual di browser HP: http://localhost:8765/index.html"
    fi
  else
    bad "server belum menjawab (kode HTTP '${CODE:-000}'). 12 baris log terakhir:"
    tail -n 12 "$PROJDIR/server.log" 2>/dev/null | sed 's/^/       /'
    echo "   uji manual:  cd ~/youtube-watchdog && python dashboard_server.py"
  fi
else
  bad "python tidak ada -> server tidak dinyalakan"
fi

# ---------------------------------------------------------------- 7/8
say "7/8 Auto-jalan saat HP reboot (opsional)"
if command -v termux-boot >/dev/null 2>&1 || pkg install -y termux-boot >/dev/null 2>&1; then
  mkdir -p "$HOME/.termux/boot"
  cat > "$HOME/.termux/boot/start-watchdog.sh" <<'EOBOOT'
#!/data/data/com.termux/files/usr/bin/sh
termux-wake-lock
cd $HOME/youtube-watchdog
nohup python dashboard_server.py >> server.log 2>&1 &
EOBOOT
  chmod +x "$HOME/.termux/boot/start-watchdog.sh"
  ok "disiapkan (butuh app 'Termux:Boot' dibuka sekali)"
else
  warn "termux-boot tidak tersedia (dilewati - tidak penting)"
fi
mkdir -p "$HOME/.shortcuts" 2>/dev/null
if [ -d "$HOME/.shortcuts" ]; then
  cat > "$HOME/.shortcuts/Nyalakan Dashboard.sh" <<'EOSHORTCUT'
cd $HOME/youtube-watchdog && bash run_termux.sh
EOSHORTCUT
  chmod +x "$HOME/.shortcuts/Nyalakan Dashboard.sh" 2>/dev/null || true
fi

# ---------------------------------------------------------------- 8/8
say "8/8 RINGKASAN"
echo "   peringatan: $WARN   |   masalah: $FAIL" | tee -a "$LOG"
if [ "$FAIL" -eq 0 ]; then
  echo "   STATUS: BERHASIL - dashboard sudah hidup di HP ini." | tee -a "$LOG"
  if [ "$WARN" -gt 0 ]; then
    echo "   (ada $WARN peringatan kecil, lihat baris [!!] di atas)" | tee -a "$LOG"
  fi
else
  echo "   STATUS: SEBAGIAN GAGAL - kirim isi log ini ke BOS NINU:" | tee -a "$LOG"
  echo "     $LOG" | tee -a "$LOG"
fi
cat <<'EOF' | tee -a "$LOG"

   BUKA LAGI NANTI (setelah HP di-restart):
       cd ~/youtube-watchdog && bash run_termux.sh

   MATIKAN SERVER:
       pkill -f dashboard_server.py

   PASANG KUNCI CHAT (sekali saja, kalau hermes terpasang):
       hermes setup
EOF
echo "=============================================="
printf 'selesai pada %s\n' "$(date '+%H:%M:%S')"
