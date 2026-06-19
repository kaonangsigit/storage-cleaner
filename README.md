# Storage Cleaner for macOS M1

🧹 Tool untuk menganalisis dan membersihkan penyimpanan Mac M1 Anda dengan aman.

## 📋 Fitur

✅ **Analisis Penyimpanan**
- Scan direktori besar (>100MB)
- Identifikasi cache, logs, temporary files
- Laporan detail dengan kategorisasi
- Visualisasi TOP 20 file terbesar

✅ **Pembersihan Aman**
- Xcode caches & derived data
- Homebrew cache
- npm/yarn cache
- Old logs
- Temporary files

✅ **Safety Features**
- Dry-run mode (preview sebelum delete)
- Confirmation before deletion
- Export report ke JSON

## 🚀 Installation

### Requirements
- Python 3.7+
- macOS 10.14+
- M1 compatible

### Setup

```bash
# Clone repository
git clone https://github.com/kaonangsigit/storage-cleaner.git
cd storage-cleaner

# Buat executable
chmod +x storage_analyzer.py
```

## 💻 Usage

### 1. Quick Scan (Recommended First)

```bash
python3 storage_analyzer.py
```

Hanya scan cache, logs, dan temporary files yang aman.

### 2. Full System Scan

```bash
python3 storage_analyzer.py --full-scan
```

Scan seluruh home directory (lebih lambat).

### 3. Custom Minimum Size

```bash
# Report files > 500MB
python3 storage_analyzer.py --min-size 500
```

### 4. Export Report ke JSON

```bash
python3 storage_analyzer.py --export report.json
```

### 5. Dry Run (Preview)

```bash
# Lihat apa yang akan dihapus (default)
python3 storage_analyzer.py
```

### 6. Actual Cleanup ⚠️

```bash
# BENAR-BENAR menghapus file yang aman
python3 storage_analyzer.py --cleanup
```

**Pastikan sudah review dry-run sebelum menjalankan cleanup!**

## 📊 Example Output

```
======================================================================
📊 macOS STORAGE ANALYSIS REPORT
======================================================================

Total recoverable space: 42.50 GB

TOP 20 LARGEST ITEMS:
----------------------------------------------------------------------
 1.       12.50 GB | ✅ SAFE | /Users/kaonangsigit/Library/Developer/Xcode/DerivedData
 2.        8.25 GB | ✅ SAFE | /Users/kaonangsigit/Library/Caches
 3.        6.30 GB | ✅ SAFE | /Users/kaonangsigit/.npm
...

======================================================================
GROUPED BY CATEGORY:
======================================================================

📁 Xcode (12.50 GB)
----------------------------------------------------------------------
  ✅        12.50 GB /Users/kaonangsigit/Library/Developer/Xcode/DerivedData

📁 Caches (8.25 GB)
----------------------------------------------------------------------
  ✅         8.25 GB /Users/kaonangsigit/Library/Caches
  ✅         2.15 GB /Users/kaonangsigit/.npm
...
```

## 🛡️ Safety Guidelines

### ✅ SAFE to Delete:
- Xcode DerivedData
- Caches (browser, app caches)
- Logs (old system logs)
- npm/yarn cache
- Temporary files in /tmp

### ⚠️ REVIEW before Deleting:
- Downloads folder
- Old backups
- Application support files

### 🚫 NEVER Delete:
- System files (/System, /Library system folders)
- Application binaries
- Important documents
- Git repositories

## 📝 Tips & Tricks

### Combine Options

```bash
# Full scan + export + dry run
python3 storage_analyzer.py --full-scan --export full_report.json
```

### Schedule Regular Cleanup

```bash
# Add to crontab untuk weekly cleanup
0 2 * * 0 /Users/kaonangsigit/storage-cleaner/storage_analyzer.py --cleanup
```

### Remove Download Files Older Than 30 Days

```bash
# Manual command
find ~/Downloads -mtime +30 -delete
```

## 🔍 File Categories

Script mendeteksi:

| Kategori | Lokasi | Safe? |
|----------|--------|-------|
| Xcode | `~/Library/Developer/Xcode/DerivedData` | ✅ |
| Xcode Archives | `~/Library/Developer/Xcode/Archives` | ✅ |
| Caches | `~/Library/Caches` | ✅ |
| npm | `~/.npm` | ✅ |
| Homebrew | `~/Library/Caches/Homebrew` | ✅ |
| Logs | `~/Library/Logs` | ✅ |
| Temp | `/tmp`, `/var/tmp` | ✅ |
| Large Dirs | Custom scan | ⚠️ |

## 📊 Performance

- **Quick Scan**: ~30 detik
- **Full Scan**: 5-10 menit
- **Cleanup**: Tergantung ukuran, biasanya 1-5 menit

## 🐛 Troubleshooting

### Permission Denied

```bash
chmod +x storage_analyzer.py
```

### Python Not Found

```bash
# Install Python 3
brew install python3

# atau check versi
python3 --version
```

### Script Hangs

- Tekan `Ctrl+C` untuk cancel
- Coba `--min-size 500` untuk scan lebih cepat

## 📄 License

MIT License - Bebas digunakan dan dimodifikasi

## 🤝 Contributing

PullRequest welcome! Untuk perubahan besar, silakan buka issue terlebih dahulu.

## 💬 Support

Jika ada masalah:
1. Buka GitHub Issue
2. Sertakan output dari script
3. Jelaskan error yang muncul

---

**Happy cleaning! 🧹**
