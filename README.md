# 🔮 Ammora Protocol Season 2 — All-in-One Automation Bot

![Ammora Bot](https://img.shields.io/badge/Ammora_Protocol-Season_2-blue?style=for-the-badge)
![Chain](https://img.shields.io/badge/GIWA_Sepolia-Testnet_91342-orange?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.9+-green?style=for-the-badge)
![License](https://img.shields.io/badge/License-MIT-purple?style=for-the-badge)

Skrip otomatisasi otonom lengkap untuk panen poin harian (**Ammora Points / AP**) di platform [Ammora Protocol Season 2](https://ammora.org) pada jaringan **GIWA Sepolia Testnet** (Chain ID: `91342`).

---

## ⚡ Fitur Utama

| Misi / Fitur | Hadiah AP | Frekuensi | Mekanisme |
| :--- | :---: | :---: | :--- |
| **Daily Check-in** | `+100 AP` | Harian | REST API Request |
| **GIWA ETH Vault Deposit** | `+50 AP` | Harian | On-Chain Transaction (`0.001 ETH`) |
| **5x Curve Pool DEX Swaps** | `+100 AP` | Harian (`+20 AP`/swap) | On-Chain Swaps (`ETH` ⇄ `$tAMM`) |
| **Stake $tAMM** | `+100 AP` | Harian | On-Chain Staking Contract |
| **One-Time Social Quests** | `+350 AP` | Sekali (7 Misi) | Follow, Like, Repost, Comment, dll. |
| **Weekly X Post Submission** | `+300 AP` | Mingguan | Kirim URL Postingan X |
| **Smart Anti-Sybil Engine** | 🛡️ | Selalu Aktif | Jitter Gas Fee EIP-1559, Nominal Non-Round, Delay Acak |
| **24/7 Background Daemon** | 🔄 | Otomatis | Berjalan otomatis setiap 24 jam dengan waktu acak |

---

## 📋 Persyaratan Sistem

- Python 3.9+
- Saldo testnet GIWA Sepolia ETH (dapat diambil gratis dari [GIWA Faucet](https://giwa.io/faucet) atau bridge).

---

## 🚀 Instalasi Cepat (1 Menit)

### 1. Clone atau Unduh Repository
```bash
git clone https://github.com/0xAraka/Ammora-Autodaily.git
cd Ammora-Autodaily
```

### 2. Pasang Dependencies
```bash
pip install -r requirements.txt
```

### 3. Konfigurasi File `.env` (2 Pilihan Mode)
Salin template konfigurasi:
```bash
cp .env.example .env
```
Buka file `.env` dan pilih salah satu mode yang Anda inginkan:

#### 🔹 Pilihan A: Full Auto Mode (Dengan Private Key — Rekomendasi ⭐)
Mendukung 100% otomatisasi on-chain (Vault + 5x DEX Swaps + Staking + Check-in):
```ini
PRIVATE_KEY=7e4861ba...anda
```

#### 🔹 Pilihan B: Cookie-Only Mode (Aman 100% Tanpa Private Key)
Bagi pengguna yang tidak ingin memasukkan Private Key karena alasan keamanan, cukup gunakan Cookie browser (`ammora_s2_auth`). Mode ini dapat menjalankan **Daily Check-in (+100 AP)**, **7 Misi Sosial (+350 AP)**, dan **Weekly Post (+300 AP)**:
```ini
AMMORA_COOKIE=ammora_s2_auth=v1.7cb6b5...
WALLET_ADDRESS=0x123456789...
```
*(Cara mengambil cookie: Buka DevTools peramban F12 ➔ Tab Application ➔ Cookies ➔ https://ammora.org ➔ Salin nilai `ammora_s2_auth`).*

#### 🌐 Menggunakan Stock Proxy (`proxy.txt`):
Jika Anda memiliki stok proxy, masukkan daftar proxy Anda ke dalam file `proxy.txt` (satu baris satu proxy). Bot otomatis mendeteksi dan mendukung berbagai format:
- `http://username:password@ip:port`
- `socks5://username:password@ip:port`
- `ip:port:username:password`
- `ip:port`

*(Jika `proxy.txt` kosong atau tidak ada, bot akan langsung menggunakan koneksi internet langsung / direct).*

---

## 💻 Panduan Perintah (CLI)

### 1. Cek Status Akun & Saldo On-Chain
Menampilkan total AP, ranking leaderboard, dan saldo ETH / $tAMM di testnet:
```bash
python ammora_bot.py status
```

### 2. Jalankan 1 Siklus Panen Harian Penuh (Rekomendasi ⭐)
Mengeksekusi seluruh 4 misi harian (Check-in + Vault Deposit + 5x Swaps + Staking) secara berurutan dengan jeda natural anti-sybil:
```bash
python ammora_bot.py cycle
```

### 3. Klaim Seluruh Misi Sosial (One-Time +350 AP)
Klaim instan untuk 7 misi sosial bawaan Ammora:
```bash
python ammora_bot.py socials
```

### 4. Kirim Postingan X Mingguan (+300 AP)
```bash
python ammora_bot.py weekly https://x.com/username/status/1234567890
```

### 5. Jalankan Daemon 24/7 Tanpa Henti
Menjalankan bot di latar belakang secara berkelanjutan. Bot akan otomatis panen setiap 24 jam sekali ditambah jeda acak 15–45 menit:
```bash
python ammora_bot.py daemon
```

---

## 🔒 Keamanan & Anti-Sybil (Organic Behavior)

Bot ini dirancang khusus dengan standar bot Web3 modern:
1. **Dynamic EIP-1559 Gas Jitter:** Tidak menggunakan gas fee yang kaku; priority fee diacak dinamis agar terlihat seperti transaksi manusia melalui dompet MetaMask / Brave Wallet.
2. **Organic Sizing:** Nominal swap dan staking menggunakan fraksi desimal natural (contoh: `0.001004 ETH`, `1.04 $tAMM`), bukan angka bulat kaku.
3. **Randomized Timing:** Jeda waktu antar transaksi diacak antara 3–8 detik untuk menghindari deteksi pola otomatisasi.
4. **Zero Cloud Leaks:** Private key hanya disimpan secara lokal di mesin Anda dan tidak pernah dikirim ke pihak ketiga.

---

## 📄 Lisensi
Didistribusikan di bawah lisensi MIT. Bebas digunakan, dimodifikasi, dan dibagikan secara terbuka.
