#!/usr/bin/env python3
"""
macOS Storage Diagnostic Tool
Untuk menemukan file besar yang tersembunyi di system
"""

import os
import subprocess
from pathlib import Path
from typing import List, Tuple
import json

class StorageDiagnostic:
    """Diagnostic tool untuk menemukan penyebab Data System membengkak"""
    
    def __init__(self):
        self.findings = {}
        
    def format_size(self, bytes_size: int) -> str:
        """Format ukuran"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_size < 1024:
                return f"{bytes_size:.2f} {unit}"
            bytes_size /= 1024
        return f"{bytes_size:.2f} PB"
    
    def expand_path(self, path: str) -> str:
        """Expand ~ dan variables"""
        return os.path.expanduser(os.path.expandvars(path))
    
    def run_command(self, command: str) -> str:
        """Run shell command"""
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=60
            )
            return result.stdout.strip()
        except Exception as e:
            return str(e)
    
    def get_dir_size(self, path: str) -> int:
        """Get directory size"""
        total = 0
        try:
            for dirpath, dirnames, filenames in os.walk(path):
                dirnames[:] = [d for d in dirnames if not d.startswith('.')]
                
                for filename in filenames:
                    filepath = os.path.join(dirpath, filename)
                    try:
                        total += os.path.getsize(filepath)
                    except (OSError, FileNotFoundError):
                        pass
        except (OSError, PermissionError):
            pass
        
        return total
    
    def scan_system_library(self):
        """Scan /Library yang mungkin besar"""
        print("🔍 Scanning /Library directory...")
        print("=" * 80)
        
        lib_path = "/Library"
        big_dirs = {}
        
        try:
            for item in os.listdir(lib_path):
                item_path = os.path.join(lib_path, item)
                
                if os.path.isdir(item_path):
                    try:
                        size = self.get_dir_size(item_path)
                        if size > 100 * 1024 * 1024:  # > 100 MB
                            big_dirs[item_path] = size
                    except:
                        pass
        except:
            pass
        
        # Sort by size
        sorted_dirs = sorted(big_dirs.items(), key=lambda x: x[1], reverse=True)
        
        print("\nLarge directories in /Library:")
        for path, size in sorted_dirs[:20]:
            print(f"  {self.format_size(size):>12} {path}")
        
        self.findings["/Library"] = sorted_dirs
        
        return sum(size for _, size in sorted_dirs)
    
    def scan_usr_local(self):
        """Scan /usr/local"""
        print("\n🔍 Scanning /usr/local directory...")
        print("=" * 80)
        
        local_path = "/usr/local"
        big_dirs = {}
        
        try:
            for item in os.listdir(local_path):
                item_path = os.path.join(local_path, item)
                
                if os.path.isdir(item_path):
                    try:
                        size = self.get_dir_size(item_path)
                        if size > 50 * 1024 * 1024:  # > 50 MB
                            big_dirs[item_path] = size
                    except:
                        pass
        except:
            pass
        
        sorted_dirs = sorted(big_dirs.items(), key=lambda x: x[1], reverse=True)
        
        print("\nLarge directories in /usr/local:")
        for path, size in sorted_dirs[:20]:
            print(f"  {self.format_size(size):>12} {path}")
        
        self.findings["/usr/local"] = sorted_dirs
        
        return sum(size for _, size in sorted_dirs)
    
    def scan_applications(self):
        """Scan /Applications for large apps"""
        print("\n🔍 Scanning /Applications directory...")
        print("=" * 80)
        
        app_path = "/Applications"
        big_apps = {}
        
        try:
            for item in os.listdir(app_path):
                item_path = os.path.join(app_path, item)
                
                if os.path.isdir(item_path) and item.endswith('.app'):
                    try:
                        size = self.get_dir_size(item_path)
                        if size > 100 * 1024 * 1024:  # > 100 MB
                            big_apps[item_path] = size
                    except:
                        pass
        except:
            pass
        
        sorted_apps = sorted(big_apps.items(), key=lambda x: x[1], reverse=True)
        
        print("\nLarge applications in /Applications:")
        for path, size in sorted_apps[:20]:
            app_name = os.path.basename(path)
            print(f"  {self.format_size(size):>12} {app_name}")
        
        self.findings["/Applications"] = sorted_apps
        
        return sum(size for _, size in sorted_apps)
    
    def scan_docker_volumes(self):
        """Scan Docker volumes jika ada"""
        print("\n🔍 Scanning Docker volumes...")
        print("=" * 80)
        
        docker_path = self.expand_path("~/.docker/volumes")
        
        if os.path.exists(docker_path):
            size = self.get_dir_size(docker_path)
            if size > 0:
                print(f"\n⚠️  Docker volumes: {self.format_size(size)}")
                return size
        
        print("\n  (No Docker volumes found)")
        return 0
    
    def scan_homebrew(self):
        """Scan Homebrew installation"""
        print("\n🔍 Scanning Homebrew...")
        print("=" * 80)
        
        brew_paths = [
            "/usr/local/Cellar",
            "/opt/homebrew/Cellar",
        ]
        
        total_size = 0
        
        for brew_path in brew_paths:
            if os.path.exists(brew_path):
                size = self.get_dir_size(brew_path)
                if size > 0:
                    print(f"\n  {self.format_size(size):>12} {brew_path}")
                    total_size += size
        
        if total_size == 0:
            print("\n  (No Homebrew installation found)")
        
        return total_size
    
    def get_apfs_snapshot_info(self):
        """Get detailed APFS snapshot info"""
        print("\n🔍 Analyzing APFS snapshots...")
        print("=" * 80)
        
        # Get snapshot info
        output = self.run_command("diskutil apfs listSnapshots /")
        
        if output and "No snapshots" not in output:
            print("\nAPFS Snapshots found:")
            print(output[:500])  # Print first 500 chars
            return True
        else:
            print("\n  (Checking snapshot sizes...)")
            
            # Try to get used space info
            output = self.run_command("df -h / | tail -1")
            print(f"\n  Root volume info: {output}")
        
        return False
    
    def check_purgeable_space(self):
        """Check purgeable space"""
        print("\n🔍 Checking purgeable space...")
        print("=" * 80)
        
        # Get purgeable space using system_profiler
        output = self.run_command(
            "system_profiler SPStorageDataType 2>/dev/null | grep -i 'purgeable'"
        )
        
        if output:
            print(f"\n  Purgeable space info:\n  {output}")
        else:
            # Alternative method
            output = self.run_command(
                "du -sh / 2>/dev/null | head -1"
            )
            if output:
                print(f"\n  Root directory size: {output}")
    
    def scan_cache_directories(self):
        """Deep scan cache directories"""
        print("\n🔍 Deep scanning cache directories...")
        print("=" * 80)
        
        cache_paths = [
            "/Library/Caches",
            "/var/cache",
            "/private/var/cache",
            "/private/tmp",
            "/private/var/tmp",
        ]
        
        total_size = 0
        
        for cache_path in cache_paths:
            if os.path.exists(cache_path):
                try:
                    size = self.get_dir_size(cache_path)
                    if size > 0:
                        print(f"  {self.format_size(size):>12} {cache_path}")
                        total_size += size
                except:
                    pass
        
        return total_size
    
    def get_disk_usage_summary(self):
        """Get overall disk usage"""
        print("\n🔍 Getting disk usage summary...")
        print("=" * 80)
        
        output = self.run_command("df -h")
        print("\nDisk usage overview:")
        print(output)
        
        # Get detailed breakdown
        output = self.run_command(
            "du -sh /* 2>/dev/null | sort -rh | head -15"
        )
        print("\nTop-level directories by size:")
        print(output)
    
    def generate_full_report(self) -> str:
        """Generate comprehensive report"""
        report = []
        report.append("=" * 80)
        report.append("🔎 macOS STORAGE DIAGNOSTIC REPORT")
        report.append("=" * 80)
        report.append("")
        
        report.append("📊 FINDINGS SUMMARY:")
        report.append("-" * 80)
        
        lib_total = sum(size for _, size in self.findings.get("/Library", []))
        local_total = sum(size for _, size in self.findings.get("/usr/local", []))
        apps_total = sum(size for _, size in self.findings.get("/Applications", []))
        
        report.append(f"\n/Library large items: {self.format_size(lib_total)}")
        report.append(f"/usr/local large items: {self.format_size(local_total)}")
        report.append(f"/Applications large items: {self.format_size(apps_total)}")
        
        report.append(f"\nTotal found in scans: {self.format_size(lib_total + local_total + apps_total)}")
        
        report.append("\n" + "=" * 80)
        report.append("💡 COMMON CAUSES OF LARGE DATA SYSTEM SIZE:")
        report.append("=" * 80)
        report.append("")
        report.append("1. ⚙️  System Frameworks & Libraries")
        report.append("   - Located in /System and /Library")
        report.append("   - Usually 20-40 GB on modern macOS")
        report.append("   - Cannot be safely deleted")
        report.append("")
        report.append("2. 📦 Installed Applications & Frameworks")
        report.append("   - Development frameworks (Java, Node, Python, etc.)")
        report.append("   - Large applications in /Applications")
        report.append("   - Can be 20-50 GB depending on what you install")
        report.append("")
        report.append("3. 🔐 Protected System Files")
        report.append("   - System integrity protection files")
        report.append("   - Kernel caches")
        report.append("   - Security frameworks")
        report.append("")
        report.append("4. 🗂️  Directory metadata & indexing")
        report.append("   - Spotlight indices")
        report.append("   - File system metadata")
        report.append("")
        
        report.append("=" * 80)
        report.append("✅ RECOMMENDED ACTIONS:")
        report.append("=" * 80)
        report.append("")
        report.append("1. Run basic cleaner first:")
        report.append("   python3 storage_analyzer.py --cleanup")
        report.append("")
        report.append("2. Run advanced cleaner:")
        report.append("   python3 advanced_cleaner.py --cleanup")
        report.append("")
        report.append("3. Uninstall unused large applications:")
        report.append("   - Check /Applications for apps you don't use")
        report.append("")
        report.append("4. Check development tools:")
        report.append("   - Xcode: 10-20 GB")
        report.append("   - Android Studio: 10-20 GB")
        report.append("   - Docker: 10-30 GB")
        report.append("   - Kubernetes: 5-10 GB")
        report.append("")
        report.append("5. Use CleanMyMac X for additional cleanup")
        report.append("")
        
        return "\n".join(report)

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Storage Diagnostic Tool"
    )
    parser.add_argument(
        '--export',
        type=str,
        help='Export findings to JSON'
    )
    
    args = parser.parse_args()
    
    print("\n🚀 Starting Storage Diagnostic...\n")
    
    diagnostic = StorageDiagnostic()
    
    # Run all scans
    diagnostic.scan_system_library()
    diagnostic.scan_usr_local()
    diagnostic.scan_applications()
    diagnostic.scan_docker_volumes()
    diagnostic.scan_homebrew()
    diagnostic.get_apfs_snapshot_info()
    diagnostic.check_purgeable_space()
    diagnostic.scan_cache_directories()
    diagnostic.get_disk_usage_summary()
    
    # Print report
    print("\n" + diagnostic.generate_full_report())
    
    # Export if requested
    if args.export:
        with open(args.export, 'w') as f:
            json.dump(diagnostic.findings, f, indent=2, default=str)
        print(f"\n💾 Findings exported to: {args.export}")

if __name__ == "__main__":
    main()
