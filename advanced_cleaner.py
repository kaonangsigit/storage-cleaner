#!/usr/bin/env python3
"""
Advanced macOS Storage Cleaner
Aggressive cleanup untuk membebaskan 50-70GB+ dari Data System
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple
from dataclasses import dataclass, asdict
from collections import defaultdict
import shutil

@dataclass
class CleanupItem:
    """Item untuk dibersihkan"""
    path: str
    size: int
    category: str
    requires_sudo: bool
    description: str
    command: str = ""

class AdvancedCleaner:
    """Advanced cleaner untuk macOS"""
    
    def __init__(self):
        self.results: Dict[str, List[CleanupItem]] = defaultdict(list)
        self.total_size = 0
        self.requires_sudo = False
        
    def format_size(self, bytes_size: int) -> str:
        """Format ukuran dalam format yang readable"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_size < 1024:
                return f"{bytes_size:.2f} {unit}"
            bytes_size /= 1024
        return f"{bytes_size:.2f} PB"
    
    def expand_path(self, path: str) -> str:
        """Expand ~ dan variables dalam path"""
        return os.path.expanduser(os.path.expandvars(path))
    
    def get_dir_size(self, path: str) -> int:
        """Hitung ukuran directory"""
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
    
    def run_command(self, command: str, sudo: bool = False) -> Tuple[str, int]:
        """Run shell command"""
        try:
            if sudo:
                cmd = f"sudo {command}"
            else:
                cmd = command
            
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30
            )
            return result.stdout.strip(), result.returncode
        except Exception as e:
            return str(e), 1
    
    def scan_time_machine_snapshots(self):
        """Scan Time Machine local snapshots"""
        print("🔍 Scanning Time Machine snapshots...")
        
        try:
            # List local snapshots
            output, _ = self.run_command("tmutil listlocalsnapshotdates / 2>/dev/null")
            
            if output and output != "No snapshots found":
                lines = output.strip().split('\n')
                
                # Estimate size per snapshot (usually 5-10 GB each)
                num_snapshots = len([l for l in lines if l.strip()])
                estimated_size = num_snapshots * 8 * 1024 * 1024 * 1024  # 8GB per snapshot
                
                item = CleanupItem(
                    path="Time Machine Snapshots",
                    size=estimated_size,
                    category="System Optimization",
                    requires_sudo=True,
                    description=f"Delete {num_snapshots} local APFS snapshots",
                    command="tmutil deletelocalsnapshots /"
                )
                self.results["Time Machine"].append(item)
                self.total_size += estimated_size
                
                print(f"  Found {num_snapshots} snapshots (~{self.format_size(estimated_size)})")
        except Exception as e:
            print(f"  Error: {e}")
    
    def scan_virtual_memory(self):
        """Scan virtual memory/swap files"""
        print("🔍 Scanning virtual memory files...")
        
        try:
            # Check swap usage
            output, _ = self.run_command("sysctl vm.swapusage")
            
            if output:
                # Parse output: vm.swapusage = total=X.XXM used=X.XXM free=X.XXM
                parts = output.split("used=")
                if len(parts) > 1:
                    used_str = parts[1].split("M")[0]
                    try:
                        used_mb = float(used_str)
                        size_bytes = int(used_mb * 1024 * 1024)
                        
                        if size_bytes > 500 * 1024 * 1024:  # > 500 MB
                            item = CleanupItem(
                                path="/var/vm/",
                                size=size_bytes,
                                category="System Optimization",
                                requires_sudo=True,
                                description="Clear virtual memory/swap files",
                                command="sudo purge"
                            )
                            self.results["Virtual Memory"].append(item)
                            self.total_size += size_bytes
                            
                            print(f"  Found {self.format_size(size_bytes)} in virtual memory")
                    except:
                        pass
        except Exception as e:
            print(f"  Error: {e}")
    
    def scan_browser_caches(self):
        """Scan browser caches deeply"""
        print("🔍 Scanning browser caches...")
        
        browser_paths = {
            'Chrome': [
                '~/.cache/google-chrome',
                '~/Library/Google/Chrome/Default/Cache',
                '~/Library/Application Support/Google/Chrome/Default/Cache Data',
            ],
            'Firefox': [
                '~/.cache/firefox',
                '~/Library/Caches/Firefox',
            ],
            'Safari': [
                '~/Library/Safari/History.db-wal',
                '~/Library/Safari/TopSites.plist',
            ],
            'Edge': [
                '~/Library/Caches/Microsoft Edge',
                '~/Library/Application Support/Microsoft Edge/Default/Cache',
            ],
        }
        
        for browser, paths in browser_paths.items():
            for path_pattern in paths:
                path = self.expand_path(path_pattern)
                
                if os.path.exists(path):
                    try:
                        if os.path.isdir(path):
                            size = self.get_dir_size(path)
                        else:
                            size = os.path.getsize(path)
                        
                        if size > 100 * 1024 * 1024:  # > 100 MB
                            item = CleanupItem(
                                path=path,
                                size=size,
                                category="Browser Caches",
                                requires_sudo=False,
                                description=f"{browser} cache"
                            )
                            self.results["Browser Caches"].append(item)
                            self.total_size += size
                    except:
                        pass
    
    def scan_language_packs(self):
        """Scan unused language packs"""
        print("🔍 Scanning language packs...")
        
        # Get system language
        output, _ = self.run_command("defaults read -g AppleLanguages | head -1")
        system_lang = "en"  # Default to English
        
        try:
            if output:
                system_lang = output.strip().split('-')[0].lower()
        except:
            pass
        
        lang_paths = [
            '/System/Library/Speech/Synthesizers',
            '/Library/Fonts',
        ]
        
        for lang_path in lang_paths:
            if os.path.exists(lang_path):
                try:
                    size = self.get_dir_size(lang_path)
                    if size > 100 * 1024 * 1024:  # > 100 MB
                        item = CleanupItem(
                            path=lang_path,
                            size=size,
                            category="System Optimization",
                            requires_sudo=True,
                            description=f"Language packs and fonts"
                        )
                        self.results["Language Packs"].append(item)
                        self.total_size += size
                except:
                    pass
    
    def scan_old_app_support(self):
        """Scan old/unused application support files"""
        print("🔍 Scanning old app support files...")
        
        app_support_path = self.expand_path("~/Library/Application Support")
        
        if os.path.exists(app_support_path):
            try:
                for item_name in os.listdir(app_support_path):
                    item_path = os.path.join(app_support_path, item_name)
                    
                    if os.path.isdir(item_path):
                        # Check if corresponding app exists
                        app_path = self.expand_path(f"~/Applications/{item_name}.app")
                        system_app_path = f"/Applications/{item_name}.app"
                        
                        if not os.path.exists(app_path) and not os.path.exists(system_app_path):
                            size = self.get_dir_size(item_path)
                            
                            if size > 100 * 1024 * 1024:  # > 100 MB
                                item = CleanupItem(
                                    path=item_path,
                                    size=size,
                                    category="Orphaned App Data",
                                    requires_sudo=False,
                                    description=f"Orphaned app support: {item_name}"
                                )
                                self.results["Orphaned App Data"].append(item)
                                self.total_size += size
            except:
                pass
    
    def scan_xcode_deep_clean(self):
        """Deep clean Xcode files"""
        print("🔍 Scanning Xcode files...")
        
        xcode_paths = {
            'DerivedData': '~/Library/Developer/Xcode/DerivedData',
            'Archives': '~/Library/Developer/Xcode/Archives',
            'Device Support': '~/Library/Developer/Xcode/iOS DeviceSupport',
            'Simulators': '~/Library/Developer/CoreSimulator/Caches',
        }
        
        for name, path_pattern in xcode_paths.items():
            path = self.expand_path(path_pattern)
            
            if os.path.exists(path):
                try:
                    size = self.get_dir_size(path)
                    
                    if size > 100 * 1024 * 1024:  # > 100 MB
                        item = CleanupItem(
                            path=path,
                            size=size,
                            category="Xcode",
                            requires_sudo=False,
                            description=f"Xcode {name}"
                        )
                        self.results["Xcode"].append(item)
                        self.total_size += size
                except:
                    pass
    
    def scan_log_files(self):
        """Scan system log files"""
        print("🔍 Scanning log files...")
        
        log_paths = [
            '~/Library/Logs',
            '/var/log',
            '/private/var/log',
        ]
        
        for path_pattern in log_paths:
            path = self.expand_path(path_pattern)
            
            if os.path.exists(path):
                try:
                    size = self.get_dir_size(path)
                    
                    if size > 100 * 1024 * 1024:  # > 100 MB
                        item = CleanupItem(
                            path=path,
                            size=size,
                            category="System Logs",
                            requires_sudo="/var" in path,
                            description="Old log files"
                        )
                        self.results["System Logs"].append(item)
                        self.total_size += size
                except:
                    pass
    
    def scan_trash(self):
        """Scan Trash/Bin"""
        print("🔍 Scanning trash...")
        
        trash_path = self.expand_path("~/.Trash")
        
        if os.path.exists(trash_path):
            try:
                size = self.get_dir_size(trash_path)
                
                if size > 0:
                    item = CleanupItem(
                        path=trash_path,
                        size=size,
                        category="Trash",
                        requires_sudo=False,
                        description="Empty trash/bin"
                    )
                    self.results["Trash"].append(item)
                    self.total_size += size
            except:
                pass
    
    def generate_report(self) -> str:
        """Generate laporan"""
        report = []
        report.append("=" * 80)
        report.append("🚀 ADVANCED macOS STORAGE CLEANER - AGGRESSIVE MODE")
        report.append("=" * 80)
        report.append("")
        
        report.append(f"Total recoverable space: {self.format_size(self.total_size)}")
        report.append("")
        
        report.append("⚠️  WARNING - AGGRESSIVE CLEANUP:")
        report.append("-" * 80)
        report.append("Some items require sudo and may affect system functionality!")
        report.append("Make sure you have backups before running this.")
        report.append("")
        
        # Sort by size
        all_items = []
        for category, items in self.results.items():
            all_items.extend(items)
        
        all_items.sort(key=lambda x: x.size, reverse=True)
        
        report.append("TOP CLEANUP TARGETS:")
        report.append("-" * 80)
        
        for idx, item in enumerate(all_items[:20], 1):
            sudo_indicator = "🔐" if item.requires_sudo else "✅"
            report.append(f"{idx:2d}. {self.format_size(item.size):>12} | {sudo_indicator} | {item.description}")
        
        report.append("")
        report.append("=" * 80)
        report.append("GROUPED BY CATEGORY:")
        report.append("=" * 80)
        
        for category, items in sorted(self.results.items()):
            if items:
                category_size = sum(item.size for item in items)
                report.append(f"\n📁 {category} ({self.format_size(category_size)})")
                report.append("-" * 80)
                
                items.sort(key=lambda x: x.size, reverse=True)
                for item in items[:5]:
                    sudo = "🔐" if item.requires_sudo else "✅"
                    report.append(f"  {sudo} {self.format_size(item.size):>12} {item.description}")
                
                if len(items) > 5:
                    report.append(f"  ... and {len(items) - 5} more items")
        
        report.append("")
        report.append("=" * 80)
        report.append("CLEANUP CATEGORIES LEGEND:")
        report.append("=" * 80)
        report.append("")
        report.append("✅ SAFE (no sudo needed)")
        report.append("   - Browser caches")
        report.append("   - Xcode caches & archives")
        report.append("   - Orphaned app data")
        report.append("   - Trash files")
        report.append("")
        report.append("🔐 REQUIRES SUDO (elevated privileges)")
        report.append("   - Time Machine snapshots")
        report.append("   - Virtual memory files")
        report.append("   - System logs")
        report.append("   - Language packs")
        report.append("")
        report.append("⚠️  AFTER CLEANUP:")
        report.append("   - Your Mac may rebuild caches automatically")
        report.append("   - First startup after cleanup may be slower")
        report.append("   - This is normal and temporary")
        
        return "\n".join(report)
    
    def cleanup(self, dry_run: bool = True, category_filter: str = ""):
        """Execute cleanup"""
        if dry_run:
            print("\n🧹 DRY RUN - Preview of cleanup:")
            print("=" * 80)
        else:
            print("\n🧹 AGGRESSIVE CLEANUP - DELETING FILES:")
            print("=" * 80)
        
        cleaned_size = 0
        cleaned_count = 0
        to_delete_items = []
        
        # Collect items
        for category, items in self.results.items():
            if category_filter and category_filter.lower() not in category.lower():
                continue
            
            for item in items:
                to_delete_items.append(item)
                
                if dry_run:
                    sudo_indicator = "🔐" if item.requires_sudo else "✅"
                    print(f"[DRY RUN] {sudo_indicator} Remove: {item.path} ({self.format_size(item.size)})")
        
        # Execute cleanup
        if not dry_run:
            for item in to_delete_items:
                try:
                    if item.requires_sudo:
                        # Special handling for sudo commands
                        if "tmutil" in item.command:
                            self.run_command(item.command, sudo=True)
                            print(f"✓ Executed: {item.command}")
                        elif "purge" in item.command:
                            self.run_command(item.command, sudo=True)
                            print(f"✓ Executed: Cleared virtual memory")
                        else:
                            # For regular paths with sudo
                            if os.path.isdir(item.path):
                                self.run_command(f"rm -rf {item.path}", sudo=True)
                            else:
                                self.run_command(f"rm {item.path}", sudo=True)
                            print(f"✓ Deleted: {item.path}")
                    else:
                        # Regular deletion without sudo
                        if os.path.isdir(item.path):
                            shutil.rmtree(item.path)
                        else:
                            os.remove(item.path)
                        print(f"✓ Deleted: {item.path}")
                    
                    cleaned_count += 1
                    cleaned_size += item.size
                
                except Exception as e:
                    print(f"✗ Error: {item.path} - {e}")
        
        print("=" * 80)
        if dry_run:
            total_to_delete = sum(item.size for item in to_delete_items)
            print(f"Items to clean: {len(to_delete_items)}")
            print(f"Space to recover: {self.format_size(total_to_delete)}")
            print("\n💡 Tip: Run dengan --cleanup untuk benar-benar menghapus files")
        else:
            print(f"Items cleaned: {cleaned_count}")
            print(f"Space recovered: {self.format_size(cleaned_size)}")
            print("\n✅ Advanced cleanup completed!")
            print("💾 Your Mac may need to rebuild some caches - this is normal")

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Advanced macOS Storage Cleaner - Aggressive mode"
    )
    parser.add_argument(
        '--cleanup',
        action='store_true',
        help='Actually delete files (use with caution!)'
    )
    parser.add_argument(
        '--category',
        type=str,
        help='Only cleanup specific category'
    )
    
    args = parser.parse_args()
    
    print("\n🚀 Starting Advanced Storage Cleaner...\n")
    
    cleaner = AdvancedCleaner()
    
    # Scan all categories
    cleaner.scan_time_machine_snapshots()
    cleaner.scan_virtual_memory()
    cleaner.scan_browser_caches()
    cleaner.scan_language_packs()
    cleaner.scan_old_app_support()
    cleaner.scan_xcode_deep_clean()
    cleaner.scan_log_files()
    cleaner.scan_trash()
    
    # Print report
    print("\n" + cleaner.generate_report())
    
    # Cleanup if requested
    if args.cleanup:
        response = input("\n⚠️  ⚠️  ⚠️  Are you ABSOLUTELY sure? (yes/no): ")
        if response.lower() == 'yes':
            cleaner.cleanup(dry_run=False, category_filter=args.category)
        else:
            print("Cancelled.")
    else:
        cleaner.cleanup(dry_run=True, category_filter=args.category)

if __name__ == "__main__":
    main()
