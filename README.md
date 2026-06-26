# CRM Network Auto-Claim Bot

Auto-claim bot untuk [@CRMNetworkBot](https://t.me/CRMNetworkBot) Telegram Mini App. Reverse engineered dari TanStack Start server functions.

## Fitur

- ✅ **Auto-claim** — claim mining reward otomatis
- ✅ **Auto restart mining** — mulai mining lagi setelah claim
- ✅ **Energy boost** — boost energy otomatis
- ✅ **Stake rewards** — claim stake rewards
- ✅ **Multi-account** — support banyak akun sekaligus
- ✅ **Curl-based** — no browser, no Selenium, lightweight

## Cara Kerja

Bot ini memanggil server functions TanStack Start langsung via HTTP POST dengan payload seroval. Tidak perlu browser, cukup curl.

## Setup

### 1. Clone
```bash
git clone https://github.com/agnetic-ai/CRM-Network-Auto-Claim-Bot.git
cd CRM-Network-Auto-Claim-Bot
```

### 2. Siapkan function hashes

Buat file `hashes.local.json` dari template:
```bash
cp hashes.json hashes.local.json
```

Isi dengan hash function yang benar (didapat dari reverse engineering bundle JS).

### 3. Siapkan akun

Buat file `accounts.local.json` dari template:
```bash
cp accounts.json accounts.local.json
```

Isi `init_data` dengan data dari Telegram Web App:
1. Buka [@CRMNetworkBot](https://t.me/CRMNetworkBot) di Telegram
2. Buka Mini App-nya
3. Buka DevTools (F12) → Console
4. Ketik: `copy(Telegram.WebApp.initData)`
5. Paste ke `accounts.local.json`

Format file:
```json
[
  {
    "name": "akun1",
    "init_data": "user=%7B%22id%22%3A..."
  },
  {
    "name": "akun2",
    "init_data": "user=%7B%22id%22%3A..."
  }
]
```

### 4. Jalankan

```bash
python3 crm_autoclaim.py
```

## Usage

```bash
# Semua akun
python3 crm_autoclaim.py

# Akun tertentu doang
python3 crm_autoclaim.py --only ombengz

# Pake file akun custom
python3 crm_autoclaim.py --accounts /path/ke/file.json

# Test (profile akun pertama)
python3 crm_autoclaim.py -t
```

## Output

```
[17:02:04] CRM Auto-Claim (2 akun)

  [OK] ombengz
         0.4545 CRM | 0.2500/hr | E:33/100 | P:25
  [OK] akun2
         0.1234 CRM | 0.1500/hr | E:50/100 | P:15

  2 OK / 0 FAIL / 2 total
```

## Cron Job (VPS)

Jalankan tiap 30 menit:
```bash
crontab -e
```

```
*/30 * * * * cd /path/to/CRM-Network-Auto-Claim-Bot && python3 crm_autoclaim.py >> crm.log
```

## File Structure

```
.
├── crm_autoclaim.py         # Main script
├── accounts.json            # Template akun (placeholder, safe for git)
├── accounts.local.json      # Akun asli (gitignored)
├── hashes.json              # Template hash function (placeholder, safe for git)
├── hashes.local.json        # Hash asli (gitignored)
└── .gitignore               # Ignore sensitive files
```

## Catatan

- **initData expiry** tergantung server — bisa tahan berhari-hari hingga berminggu-minggu. Kalau error `TG_AUTH_REQUIRED`, tinggal refresh initData dari Telegram Web App.
- **error=true** dalam response seroval berarti sukses (bukan error) — ini konvensi framework TanStack Start.
- Script hanya support curl — dependency zero.