#!/data/data/com.termux/files/usr/bin/bash
# ==============================================================
#  PASANG_KUNCI.sh -- sekali jalan
#     bash pasang_kunci.sh <KUNCI_AI> <TOKEN_GITHUB>
#  Atau taruh rahasia.txt di Download lalu:  bash pasang_kunci.sh
# ==============================================================
CONF="$HOME/.watchdog"
mkdir -p "$CONF"
TARGET="$CONF/rahasia"

echo "=============================================="
echo "  PASANG KUNCI -- YouTube Growth Room"
echo "=============================================="

AI="${1:-}"
GH="${2:-}"

if [ -z "$AI" ]; then
  if [ -f /sdcard/Download/rahasia.txt ]; then
    while IFS= read -r baris; do
      case "$baris" in
        AI_KEY=*)  AI="${baris#AI_KEY=}" ;;
        GH_TOKEN=*) GH="${baris#GH_TOKEN=}" ;;
      esac
    done < /sdcard/Download/rahasia.txt
    echo "   sumber: /sdcard/Download/rahasia.txt"
  elif [ -f "$HOME/storage/downloads/rahasia.txt" ]; then
    while IFS= read -r baris; do
      case "$baris" in
        AI_KEY=*)  AI="${baris#AI_KEY=}" ;;
        GH_TOKEN=*) GH="${baris#GH_TOKEN=}" ;;
      esac
    done < "$HOME/storage/downloads/rahasia.txt"
    echo "   sumber: ~/storage/downloads/rahasia.txt"
  fi
fi

AI="$(printf '%s' "$AI" | tr -d '[:space:]')"
GH="$(printf '%s' "$GH" | tr -d '[:space:]')"

if [ -z "$AI" ]; then
  echo "   [XX] kunci AI kosong. Cara pakai:"
  echo "       bash pasang_kunci.sh KUNCI_AI TOKEN_GITHUB"
  exit 1
fi

{
  echo "AI_KEY=$AI"
  echo "AI_BASE=https://modelrouter.id/v1"
  echo "AI_MODEL=mr-vip"
  echo "GH_TOKEN=$GH"
} > "$TARGET"
chmod 600 "$TARGET" 2>/dev/null

echo "----------------------------------------------"
echo "   [OK] kunci AI tersimpan  (${#AI} karakter)"
if [ -n "$GH" ]; then
  echo "   [OK] token GitHub tersimpan (${#GH} karakter)"
  echo "        -> kendali jarak jauh HIDUP"
else
  echo "   [!!] token GitHub kosong -> kendali jarak jauh mati"
fi
echo "   berkas: $TARGET"
echo "----------------------------------------------"
echo "   Tidak perlu dinyalakan ulang; agent membaca kunci tiap kali dipakai."
echo "   Uji: curl -s http://localhost:8765/api/status"
