# 🤖 Multi-Bot Telegram VIP System

Sistem ini mengelola **beberapa bot Telegram** untuk:

* Aktivasi VIP oleh admin (manual)
* Deteksi donasi (Trakteer/dll)
* Reminder otomatis sebelum masa VIP habis
* Auto-cleanup user VIP expired
* Notifikasi admin real-time (via bot)
* Modular handler untuk tiap fungsi dan bot

---

## ✅ Struktur Bot

| Bot           | Fungsi Utama                          |
| ------------- | ------------------------------------- |
| `drac1n_bot`  | Bot utama: aktivasi VIP, tools user   |
| `utbkvip_bot` | Bot UTBK: soal, jawaban, analisis VIP |
| `dcst_bot`    | Bot kelola posting, repost, dashboard |

Semua bot menggunakan **webhook yang sama** dan diproses paralel.

---

## 🧠 Fitur Sistem

### 🎯 VIP Management

* `/vip_add` (admin only)
* Inline step FSM: input user → pilih paket → konfirmasi
* Cek duplikat aktivasi VIP pada hari yang sama
* Kirim notifikasi ke user & admin
* Simpan log ke database

### ⏰ Reminder Loop

* Cek semua user VIP tiap X detik
* Jika sisa hari < 1, kirim reminder ke user & admin
* Reset reminder jika diperpanjang

### 🔁 Auto Cleanup

* Scheduler APScheduler tiap 6 jam
* Nonaktifkan otomatis user VIP yang sudah expired

### 📬 Notifikasi Log Donasi & VIP

* Polling ke `vip_logs` dan `donation_log`
* Kirim notifikasi ke semua admin jika ada donasi atau aktivasi VIP
* Balas email otomatis ke donatur (jika terdaftar)

---

## 🛠️ Modul Inti

| Modul                      | Fungsi                                         |
| -------------------------- | ---------------------------------------------- |
| `startup_sequence.py`      | Menginisialisasi semua task & handler          |
| `vip_add.py`               | FSM tahap awal input user ID                   |
| `vip_package_selection.py` | Pilih paket VIP                                |
| `vip_add_confirmation.py`  | Konfirmasi dan aktivasi VIP                    |
| `process_vip_activation()` | Eksekusi aktivasi VIP, notifikasi, logging     |
| `admin_cache.py`           | Reload daftar admin otomatis, register command |
| `task_monitor.py`          | Memantau task async dan restart jika gagal     |

---

## 🧩 Struktur Modular

Berikut adalah penjelasan masing-masing modul utama dalam sistem:

### 🛠️ Modul Inti

| Modul                      | Fungsi                                                                 |
|----------------------------|------------------------------------------------------------------------|
| `startup_sequence.py`      | Menjalankan startup semua task dan background loop seperti:<br>– `reminder_loop()`<br>– `run_notifier_loop()`<br>– `admin_cache.start_background_task()`<br>– `scheduler VIP auto-cleanup` |
| `task_monitor.py`          | Memantau task async dan otomatis restart jika task mati/error         |
| `admin_cache.py`           | Memuat ulang daftar admin dari DB secara periodik + sinkronisasi command |
| `VipStateManager`          | FSM state handler untuk proses VIP (`add`, `delete`, `reset`, dll.)   |

---

### ➕ VIP Add Flow

| Modul                        | Fungsi                                                                 |
|------------------------------|------------------------------------------------------------------------|
| `vip_add.py`                 | FSM tahap awal: admin memasukkan user_id                               |
| `vip_package_selection.py`   | Admin memilih paket VIP dari daftar pilihan                            |
| `vip_add_confirmation.py`    | Konfirmasi dan trigger aktivasi VIP                                   |
| `process_vip_activation.py`  | Eksekusi backend aktivasi: update DB, log, dan notifikasi              |
| `activate_vip()`             | Fungsi utama penulisan DB untuk insert/update data VIP                 |

---

### ♻️ VIP Reset Flow

| Modul                          | Fungsi                                                            |
|--------------------------------|-------------------------------------------------------------------|
| `vip_reset.py`                 | FSM untuk reset VIP 1 user (cek status VIP dulu)                 |
| `vip_reset_confirmation.py`    | Konfirmasi reset VIP dan eksekusi ke DB                          |
| `vip_reset_all.py`             | Mass reset (hapus semua user VIP yang expired) + konfirmasi      |

---

### ❌ VIP Delete Flow

| Modul                          | Fungsi                                                            |
|--------------------------------|-------------------------------------------------------------------|
| `vip_delete.py`                | FSM untuk input user_id yang ingin dihapus VIP-nya               |
| `vip_delete_confirmation.py`   | Konfirmasi dan eksekusi penghapusan VIP                          |

---

### 📊 Statistik VIP

| Modul                      | Fungsi                                                                 |
|----------------------------|------------------------------------------------------------------------|
| `vip_stats.py`             | Menampilkan statistik pengguna VIP (total, aktif, expired)            |
| `vip_users.vip_status.py`  | Fungsi helper untuk cek status VIP pengguna dari DB                   |

---

### 📦 Manajemen VIP

| Modul                      | Fungsi                                                                 |
|----------------------------|------------------------------------------------------------------------|
| `vip_utils.py`             | Fungsi utilitas umum:<br>– `mark_vip_notified()`<br>– `reset_vip_notified()`<br>– `deactivate_expired_vips()` |
| `vip_remove.py`            | Menghapus status VIP dari DB                                          |
| `vip_logs` (table)         | Menyimpan histori aktivasi VIP (log harian + is_notified)             |

---

## 🔄 Daftar Task Loop Otomatis

| Task                      | Fungsi                                                                 |
|---------------------------|------------------------------------------------------------------------|
| `reminder_loop()`         | Mengirim pengingat jika VIP akan habis dalam 1x24 jam                  |
| `run_notifier_loop()`     | Mengecek `vip_logs` dan `donation_log` untuk kirim notifikasi          |
| `start_vip_auto_cleanup()`| Reset otomatis VIP yang sudah expired (via APScheduler setiap 6 jam)   |
| `admin_cache.start_background_task()` | Reload admin + register command bot                         |
| `task_monitor.monitor_loop()` | Memantau seluruh task & restart jika task error                    |

---

## 💬 Perintah Admin

- `/dashboard` – Masuk ke menu utama admin
- `/list_users` – Menampilkan seluruh user (VIP & Free)
- Semua fitur lain berbasis tombol inline melalui dashboard

---

## 🧠 FSM (State Manager)

Sistem menggunakan `VipStateManager` dan `AdminStateManager` untuk mengelola alur FSM secara persistent (tersimpan ke DB). Semua step disimpan dengan kunci unik per-bot (`drac1n`, `utbk`, dll).

---

## 🧪 Testing Tips

- Gunakan akun admin Telegram yang sudah didaftarkan ke DB.
- Lakukan `/dashboard` lalu pilih "Kelola VIP" → "Tambah / Hapus / Reset".
- Gunakan webhook `ngrok` atau Railway untuk testing live.

---

## 🚀 Deployment

- Semua bot dijalankan via `main.py`, dengan `startup_sequence(app, bot_name)` dan `register_all_handlers()` untuk tiap bot.
- Gunakan `.env` atau `config.py` untuk token dan URL webhook per bot.

---

## 🔐 Keamanan

* Cek admin di semua handler (`admin_cache.is_admin_async()`)
* FSM gunakan `VipStateManager` per admin → hindari tumpang tindih
* Anti double-click → gunakan `is_processing` flag

---

## 📦 Database

### Tabel-tabel:

* `users`: daftar user dengan status VIP
* `vip_logs`: log aktivasi VIP manual
* `donation_log`: log donasi masuk
* `admins`: user ID admin bot

---

## 📡 Webhook

Semua bot menggunakan endpoint yang sama:

```
/webhook/trakteer
```

Diatur secara dinamis saat startup via `setWebhook` API.

---

## 🧩 Cara Menambahkan Bot Baru

1. Tambahkan ke `BOT_CONFIG` di `bots_config.py`
2. Buat `create_xxx_app()` di `core/app.py`
3. Daftarkan handler di `register_handlers/`
4. Pastikan `register_handlers(bot, admin_cache)` dipanggil

---

## 🩺 Monitoring

### Task Monitor:

* Aktif setiap 30 detik
* Cek status `reminder_loop`, `notifier_loop`, `admin_cache_reload`
* Restart task jika error / `done()`

### Memory Monitor:

* Log penggunaan memori setiap 60 detik

---

## ✅ Status: Production Ready

* Semua bot stabil (webhook, handler, polling, command)
* Task async termonitor & auto-restart
* Logging dan notifikasi admin lengkap
* Bisa dikembangkan menjadi sistem donasi berlangganan

---

## ✨ TODO (Opsional Berikutnya)

* [ ] `/list_vip` untuk melihat semua user aktif
* [ ] `/vip_status` untuk cek masa aktif user
* [ ] Dashboard web (FastAPI + Jinja)
* [ ] Statistik penggunaan (total aktivasi, expired, dll)
* [ ] Fitur broadcast VIP
