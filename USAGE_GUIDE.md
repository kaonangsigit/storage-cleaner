# Storage Cleaner - Panduan Lengkap Penggunaan

## 🎯 Quick Start (5 Menit)

### Step 1: Clone Repository

```bash
git clone https://github.com/kaonangsigit/storage-cleaner.git
cd storage-cleaner
```

### Step 2: Run First Scan

```bash
python3 storage_analyzer.py
```

### Step 3: Review Report

Lihat laporan yang ditampilkan. Perhatikan:
- **Total recoverable space** - berapa yang bisa dihemat
- **TOP 20 LARGEST ITEMS** - file/folder terbesar
- **Dry run preview** - apa yang akan dihapus

### Step 4: Cleanup (Optional)

Jika puas dengan dry-run preview:

```bash
python3 storage_analyzer.py --cleanup
```

Konfirmasi dengan mengetik `yes`.

---

## 📋 Command Reference

### Basic Commands

```bash
# Scan caches, logs, temp files (RECOMMENDED)
python3 storage_analyzer.py

# Scan seluruh home directory
python3 storage_analyzer.py --full-scan

# Preview apa yang akan dihapus
python3 storage_analyzer.py --cleanup (no actual deletion)

# BENAR-BENAR menghapus
python3 storage_analyzer.py --cleanup --confirm
```

### Advanced Commands

```bash
# Report hanya file > 500MB
python3 storage_analyzer.py --min-size 500

# Export ke JSON
python3 storage_analyzer.py --export my_report.json

# Kombinasi
python3 storage_analyzer.py --full-scan --export report.json --min-size 200
```

---

## 🧹 Cleanup Scenarios

### Scenario 1: Xcode Developers

Xcode DerivedData bisa sangat besar (10GB+)

```bash
# Review
python3 storage_analyzer.py

# Cleanup (DerivedData akan rebuild otomatis)
python3 storage_analyzer.py --cleanup
```

**Aman karena**: Xcode akan rebuild DerivedData saat diperlukan.

### Scenario 2: Node/npm Developers

npm cache bisa 5-10GB

```bash
python3 storage_analyzer.py
```

**Aman karena**: npm akan rebuild cache otomatis.

### Scenario 3: General Users

```bash
# Scan
python3 storage_analyzer.py

# Lihat dry-run output
# Cleanup
python3 storage_analyzer.py --cleanup
```

**JANGAN delete**:
- Downloads folder important files
- ~/Documents
- ~/Pictures

---

## 📊 Understanding the Report

### Report Structure

```
📊 macOS STORAGE ANALYSIS REPORT
├─ Total recoverable space: XX GB
├─ TOP 20 LARGEST ITEMS (sorted by size)
├─ GROUPED BY CATEGORY
│  ├─ Xcode (XX GB)
│  ├─ Caches (XX GB)
│  ├─ Package Managers (XX GB)
│  └─ ...
└─ RECOMMENDATIONS
```

### Symbol Reference

| Symbol | Meaning |
|--------|----------|
| ✅ SAFE | Aman dihapus, rebuild otomatis |
| ⚠️ RISKY | Review sebelum dihapus |
| 📁 | Directory/Folder |
| 🔍 | Scanning |
| ✓ | Selesai/Success |
| ✗ | Error |

### Example Report

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
 4.        5.15 GB | ⚠️  RISKY | /Users/kaonangsigit/Downloads
 5.        3.80 GB | ✅ SAFE | /Users/kaonangsigit/Library/Caches/Homebrew
 6.        2.40 GB | ✅ SAFE | /var/log
 7.        1.30 GB | ⚠️  RISKY | /Users/kaonangsigit/Large Project Folder
...

======================================================================
GROUPED BY CATEGORY:
======================================================================

📁 Xcode (12.50 GB)
----------------------------------------------------------------------
  ✅       12.50 GB /Users/kaonangsigit/Library/Developer/Xcode/DerivedData

📁 Caches (17.30 GB)
----------------------------------------------------------------------
  ✅        8.25 GB /Users/kaonangsigit/Library/Caches
  ✅        6.30 GB /Users/kaonangsigit/.npm
  ✅        2.75 GB /Users/kaonangsigit/Library/Caches/Homebrew

📁 Package Managers (6.30 GB)
----------------------------------------------------------------------
  ✅        6.30 GB /Users/kaonangsigit/.npm
  ... and 2 more items

📁 Logs (2.40 GB)
----------------------------------------------------------------------
  ✅        2.40 GB /var/log

📁 Large Directories (5.15 GB)
----------------------------------------------------------------------
  ⚠️        5.15 GB /Users/kaonangsigit/Downloads
  ⚠️        1.30 GB /Users/kaonangsigit/Large Project Folder

======================================================================
RECOMMENDATIONS:
======================================================================

✅ Safe to delete: 41.20 GB
   - Empty caches
   - Delete old logs
   - Clean package manager cache

⚠️  Review before deleting:
   - Downloads folder
   - Old backups
   - Application support files

🛡️  DO NOT delete:
   - System files
   - Application binaries
   - Important documents
```

---

## 🚨 Important Safety Notes

### Before Running Cleanup

1. ✅ Always run dry-run first:
   ```bash
   python3 storage_analyzer.py
   ```

2. ✅ Review what will be deleted carefully

3. ✅ Make backup if you're unsure

4. ✅ Only delete items marked with ✅ SAFE

### What Gets Deleted

✅ **SAFE** (akan rebuild otomatis):
- Xcode DerivedData
- Caches (browser, app)
- npm/yarn cache
- Old logs
- Temp files

⚠️ **RISKY** (perlu manual review):
- Downloads folder
- Application Support
- Old backups

🚫 **NEVER**:
- System files
- Applications
- Documents
- Important projects

---

## 🔧 Troubleshooting

### Problem: "Permission denied"

**Solution:**
```bash
chmod +x storage_analyzer.py
python3 storage_analyzer.py
```

### Problem: "Python not found"

**Solution:**
```bash
# Check if Python 3 installed
python3 --version

# Install if needed
brew install python3
```

### Problem: Script too slow

**Solution:**
```bash
# Use quick scan (default)
python3 storage_analyzer.py

# Not full scan
# python3 storage_analyzer.py --full-scan

# Or increase minimum size
python3 storage_analyzer.py --min-size 500
```

### Problem: Script hangs

**Solution:**
```bash
# Press Ctrl+C to stop
# Try with higher minimum size
python3 storage_analyzer.py --min-size 1000
```

### Problem: Permission Error on Delete

**Solution:**
```bash
# Use sudo
sudo python3 storage_analyzer.py --cleanup

# Or check file permissions
ls -la /path/to/file
```

---

## 📈 Expected Results

Typical cleanup results:

| User Type | Recoverable Space | Time |
|-----------|-------------------|------|
| Developer (Xcode) | 20-50 GB | 5-10 min |
| Node Developer | 10-30 GB | 3-5 min |
| General User | 5-20 GB | 2-3 min |
| Light User | 1-5 GB | 1-2 min |

---

## 🎓 Tips & Best Practices

### Tip 1: Regular Maintenance

```bash
# Run monthly
month=$(date +%m)
if [ $((month % 3)) -eq 0 ]; then
  ~/storage-cleaner/storage_analyzer.py --cleanup
fi
```

### Tip 2: Export Reports

```bash
# Keep history
python3 storage_analyzer.py --export "report_$(date +%Y%m%d).json"
```

### Tip 3: Selective Cleanup

```bash
# Only Xcode
rm -rf ~/Library/Developer/Xcode/DerivedData

# Only npm
rm -rf ~/.npm

# Only Homebrew cache
brew cleanup -s
```

### Tip 4: Monitor Disk Space

```bash
# Check disk usage
df -h

# Check directory size
du -sh ~/Library
```

---

## 📞 Support

Hadapi masalah? 

1. Check troubleshooting section
2. Open GitHub Issue dengan:
   - Output dari script
   - Error message
   - macOS version
   - Python version

```bash
# Get system info
swiftc --version
python3 --version
system_profiler SPSoftwareDataType
```

---

**Happy cleaning! 🧹**
