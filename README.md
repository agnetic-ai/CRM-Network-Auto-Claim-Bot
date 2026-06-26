# CRM Network Auto-Claim Bot

Auto-claim bot untuk [@CRMNetworkBot](https://t.me/CRMNetworkBot) Telegram Mini App. Reverse engineered dari TanStack Start server functions.

## Fitur

- **Auto-claim** — claim mining reward otomatis
- **Auto restart mining** — mulai mining lagi setelah claim
- **Energy boost** — boost energy otomatis sebelum claim
- **Stake rewards** — claim reward dari stake yang sudah ada
- **Multi-account** — support banyak akun sekaligus
- **Zero dependency** — cuma butuh Python 3 + curl

## Requirements

- Python 3.6+
- curl

No pip install needed — script uses only Python stdlib.

## Cara Kerja

Bot ini memanggil server functions TanStack Start langsung via HTTP POST dengan payload seroval format. Tidak perlu browser atau Selenium — cukup curl.

Endpoint: `POST https://crmnetwork.xyz/_serverFn/<sha256hash>`

Function hashes sudah tersedia di `hashes.json`. Jika hash berubah (server update), tinggal update file tersebut.

## Setup

### 1. Clone

```bash
git clone https://github.com/agnetic-ai/CRM-Network-Auto-Claim-Bot.git
cd CRM-Network-Auto-Claim-Bot
```

### 2. Siapkan akun

Copy template dan isi dengan initData asli:

```bash
cp accounts.json accounts.local.json
```

Cara dapat initData:

1. Buka [@CRMNetworkBot](https://t.me/CRMNetworkBot) di Telegram
2. Klik buka Mini App-nya
3. Buka DevTools (F12) → Console
4. Ketik: `copy(Telegram.WebApp.initData)`
5. Paste ke `accounts.local.json`

Format:

```json
[
  {
    "name": "akun1",
    "init_data": "user=%7B%22id%22%3A12345%2C...signature_here"
  },
  {
    "name": "akun2",
    "init_data": "user=%7B%22id%22%3A67890%2C...signature_here"
  }
]
```

### 3. Jalankan

```bash
python3 crm_autoclaim.py
```

## Usage

```bash
# Semua akun
python3 crm_autoclaim.py

# Akun tertentu
python3 crm_autoclaim.py --only ombengz

# File akun custom
python3 crm_autoclaim.py --accounts /path/ke/file.json

# Test profile akun pertama
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

Rekomendasi: tiap 100 menit (~1 jam 40 menit). Lebih sering dari itu bikin energy boncos, lebih jarang pending kecil.

```bash
crontab -e
```

```
59 0,2,4,6,8,10,12,14,16,18,20,22 * * * cd /path/to/CRM-Network-Auto-Claim-Bot && python3 crm_autoclaim.py >> crm.log 2>&1
```

Atau pakai loop:

```bash
while true; do python3 crm_autoclaim.py >> crm.log 2>&1; sleep 6000; done
```

## File Structure

```
.
├── crm_autoclaim.py         # Main script
├── accounts.json            # Template akun (placeholder)
├── accounts.local.json      # Akun asli — initData (gitignored)
├── hashes.json              # Function hashes (public, sudah berisi hash asli)
├── hashes.local.json        # Override hashes (opsional, gitignored)
└── .gitignore
```

## Hash Override

`hashes.json` sudah berisi hash yang benar. Jika server update hash-nya:

1. Ambil hash baru dari bundle JS (`/assets/api.functions-*.js`)
2. Update `hashes.json` atau buat `hashes.local.json` untuk override lokal

Script akan pakai `hashes.local.json` jika ada, kalau tidak fallback ke `hashes.json`.

## Troubleshooting

| Error | Penyebab | Solusi |
|-------|----------|--------|
| `TG_AUTH_REQUIRED` | initData expired | Ambil initData baru dari Telegram Web App |
| `No energy` | Energy habis | Normal — skip, claim di cycle berikutnya |
| `Missing: hashes.json` | File hash tidak ada | Pastikan `hashes.json` ada di direktori yang sama |
| `Bad response` | Server down / hash expired | Cek hash masih valid, cek server status |

## Catatan

- **initData expiry** tergantung server CRMNetworkBot — bisa tahan >24 jam hingga berminggu-minggu. Kalau `TG_AUTH_REQUIRED`, refresh initData.
- **error=true** dalam response seroval = sukses (bukan error). Ini konvensi framework TanStack Start.
- **Energy boost** dijalankan sebelum claim — claim tanpa energy = skip.
- Script zero dependency — cuma Python 3 standar + curl.
