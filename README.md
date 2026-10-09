## Cara CEPAT (otomatis) - pindah file ke GitHub
Kalau kamu bingung upload manual, jalankan cara ini:

1. Buka folder: `Desktop\youtube_github`
2. Dobel-klik file `PINDAH_KE_GITHUB.bat`
3. Browser akan terbuka, login GitHub (sekali saja)
4. Bot akan: buat repo `youtube-watchdog` (Public), upload semua file,
   isi 4 GitHub Secrets (sudah terisi YT_CHANNEL_ID = UCTo4AAkP9bPT9ux40oWmqvg),
   aktifkan GitHub Pages, dan langsung jalankan uji pertama

Bila tidak ingin browser, tempel token GitHub ke `GITHUB_TOKEN.txt`
(format: `ghp_xxx` / `github_pat_xxx`) lalu jalankan `PINDAH_KE_GITHUB.bat`.

---

# YouTube Growth Watchdog — GROWTH ROOM (LIVE)

Bot otomatis yang memantau tren YouTube Shorts + animasi Roblox dan
metrik channel YouTube-mu setiap 12 jam — **tanpa perlu laptop menyala**.
Kalau ada sinyal penting (metrik turun / tren baru) → laporan dikirim ke
Discord. Kalau tidak ada → senyap. Dashboard selalu diperbarui.

Dashboard bergaya **GROWTH ROOM**: ada NPC (agen) yang mengucapkan pesan
di atas kepalanya dan statusnya berubah: ISTIRAHAT / BEKERJA / SIBUK / BINGUNG.

## Cara kerjanya (LIVE)
- `run_watchdog.py` menulis 2 file: `index.html` (tampilan) dan `feed.json` (data hidup).
- `index.html` membaca `feed.json` tiap 8 detik → robot update **tanpa reload**.
- Di GitHub Pages keduanya disajikan lewat http, jadi LIVE otomatis.

---

## LANGKAH DEMI LANGKAH

### 1. Akun GitHub
Buka https://github.com/signup , daftar pakai email. Gratis.

### 2. Buat repository
- Klik **+** (kanan atas) → **New repository**
- Nama: `youtube-watchdog`
- Pilih **Public**  ← WAJIB (jadwal cron gratis tanpa batas; di repo privat
  akun gratis, cron otomatis dimatikan)
- Jangan centang "Add README"
- Klik **Create repository**

### 3. Upload file
Klik **Add file → Upload files**, seret (drag) file ini dari folder
`Desktop\youtube_github`:
  - `run_watchdog.py`
  - `config_state.json`
  - `.gitignore`
  - `README.md`
Klik **Commit changes**.

File workflow dibuat terpisah:
  - **Add file → Create new file**
  - Di kotak nama ketik persis:  `.github/workflows/watchdog.yml`
  - Tempel isi file `watchdog.yml` (ada di folder yang disiapkan)
  - **Commit changes**

### 4. Isi Secrets (kunci rahasia)
Buka file `KUNCI_UNTUK_GITHUB.txt` (di folder yang disiapkan) — nilainya
sudah siap. Di GitHub: **Settings → Secrets and variables → Actions →
New repository secret**. Buat 4:

| Name | Value |
|------|-------|
| `YT_API_KEY` | (dari KUNCI_UNTUK_GITHUB.txt) |
| `YT_CHANNEL_ID` | kosongkan dulu, isi `UC...` nanti |
| `DISCORD_BOT_TOKEN` | (dari KUNCI_UNTUK_GITHUB.txt) |
| `DISCORD_CHANNEL_ID` | `1218606873259937835` |

> Terenkripsi. Setelah disimpan tak bisa dibaca lagi (hanya ditimpa).

### 5. Aktifkan GitHub Pages (dashboard online & LIVE)
- **Settings → Pages**
- Source: **Deploy from a branch**
- Branch: **main** , folder: **/ (root)** → **Save**
- Tunggu 1-2 menit. Buka:
  `https://NAMA-KAMU.github.io/youtube-watchdog/`

### 6. Uji coba
- Tab **Actions** → **YouTube Growth Watchdog** → **Run workflow**
- ~1 menit. Cek: Actions hijau, Discord #general (kalau ada sinyal),
  dan halaman Pages ter-update.

Selesai. Bot jalan tiap 12 jam walau laptopmu mati.

---

## Mendapatkan YT_CHANNEL_ID (UC...)
YouTube Studio → Setelan → Kanal → Info kanal lanjutan → salin **ID Kanal**.
Isi ke Secret `YT_CHANNEL_ID` → bot langsung bisa memantau metrik channelmu.

## Mengubah jadwal
Edit `.github/workflows/watchdog.yml` baris `cron:`.
- tiap 6 jam : `'0 */6 * * *'`
- tiap hari 09:00 UTC : `'0 9 * * *'`

## Amankan token
Karena repo **publik**, rahasia HANYA lewat Secrets (langkah 4), jangan
pernah ditulis di file. Sangat disarankan **reset token bot** di Discord
Developer Portal sekali, lalu pakai token baru.
