#!/usr/bin/env python3
"""
macOS Storage Analyzer & Cleaner
Membantu mengidentifikasi dan membersihkan file besar di Mac M1
"""

import os
import sys
import json
from pathlib import Path
from typing import Dict, List, Tuple
import subprocess
from dataclasses import dataclass, asdict
from collections import defaultdict
import shutil

@dataclass
class FileInfo:
    """Informasi file untuk analisis"""
    path: str
    size: int
    category: str
    is_safe_to_delete: bool
    description: str

class StorageAnalyzer:
    """Analyzer untuk penyimpanan macOS"""
    
    # Kategori file yang aman dihapus
    SAFE_TO_DELETE_PATTERNS = {
        'Caches': [
            '~/.cache',
            '~/Library/Caches',
            '~/.npm',
            '~/.yarn/cache',
        ],
        'Logs': [
            '~/Library/Logs',
            '/var/log',
        ],
        'Temporary': [
            '/tmp',
            '/var/tmp',
            '~/Downloads',  # optional
        ],
        'Old Backups': [
            '~/Library/Mobile Documents/com~apple~CloudDocs',
        ],
        'Xcode': [
            '~/Library/Developer/Xcode/DerivedData',
            '~/Library/Developer/Xcode/Archives',
        ],
        'Package Managers': [
            '~/Library/Caches/Homebrew',
            '~/Library/Caches/pip',
        ],
        'Applications': [
            '~/Library/Application Support',
        ],
    }
    
    def __init__(self, min_size_mb: int = 100):
        """
        Initialize analyzer
        
        Args:
            min_size_mb: Minimum file size to report (in MB)
        """
        self.min_size_bytes = min_size_mb * 1024 * 1024
        self.results: Dict[str, List[FileInfo]] = defaultdict(list)
        self.total_size = 0
        
    def expand_path(self, path: str) -> str:
        """Expand ~ dan variables dalam path"""
        return os.path.expanduser(os.path.expandvars(path))
    
    def get_dir_size(self, path: str) -> int:
        """
        Hitung ukuran directory secara rekursif
        Lebih cepat daripada du command
        """
        total = 0
        try:
            for dirpath, dirnames, filenames in os.walk(path):
                # Skip hidden directories untuk kecepatan
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
    
    def get_file_size(self, path: str) -> int:
        """Get file size dengan error handling"""
        try:
            return os.path.getsize(path)
        except (OSError, FileNotFoundError):
            return 0
    
    def format_size(self, bytes_size: int) -> str:
        """Format ukuran dalam format yang readable"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_size < 1024:
                return f"{bytes_size:.2f} {unit}"
            bytes_size /= 1024
        return f"{bytes_size:.2f} PB"
    
    def scan_safe_directories(self):
        """Scan direktori yang aman untuk dihapus"""
        print("🔍 Scanning safe directories for cleanup...")
        
        for category, paths in self.SAFE_TO_DELETE_PATTERNS.items():
            for path_pattern in paths:
                path = self.expand_path(path_pattern)
                
                if not os.path.exists(path):
                    continue
                
                if os.path.isfile(path):
                    size = self.get_file_size(path)
                else:
                    size = self.get_dir_size(path)
                
                if size >= self.min_size_bytes:
                    info = FileInfo(
                        path=path,
                        size=size,
                        category=category,
                        is_safe_to_delete=True,
                        description=f"Safe to delete: {category}"
                    )
                    self.results[category].append(info)
                    self.total_size += size
        
        print(f"✓ Scan complete!")
    
    def scan_large_directories(self, start_path: str = "~", depth: int = 3):
        """Scan direktori besar di home"""
        print(f"🔍 Scanning large directories from {start_path}...")
        
        start = self.expand_path(start_path)
        self._recursive_scan(start, depth, 0)
        
        print(f"✓ Scan complete!")
    
    def _recursive_scan(self, path: str, max_depth: int, current_depth: int):
        """Recursive directory scanning"""
        if current_depth > max_depth:
            return
        
        try:
            entries = os.listdir(path)
        except (PermissionError, OSError):
            return
        
        for entry in entries:
            # Skip hidden files dan system directories
            if entry.startswith('.'):
                continue
            
            full_path = os.path.join(path, entry)
            
            try:
                if os.path.isdir(full_path):
                    # Skip specific directories
                    if entry in ['Applications', 'System', 'Library']:
                        continue
                    
                    size = self.get_dir_size(full_path)
                    if size >= self.min_size_bytes:
                        info = FileInfo(
                            path=full_path,
                            size=size,
                            category="Large Directories",
                            is_safe_to_delete=False,
                            description=f"Directory: {entry}"
                        )
                        self.results["Large Directories"].append(info)
                        self.total_size += size
                    
                    # Continue scanning if not too deep
                    if current_depth < max_depth:
                        self._recursive_scan(full_path, max_depth, current_depth + 1)
            
            except (OSError, PermissionError):
                pass
    
    def generate_report(self) -> str:
        """Generate laporan tertulis"""
        report = []
        report.append("=" * 70)
        report.append("📊 macOS STORAGE ANALYSIS REPORT")
        report.append("=" * 70)
        report.append("")
        
        report.append(f"Total recoverable space: {self.format_size(self.total_size)}")
        report.append("")
        
        # Sort by size
        all_items = []
        for category, items in self.results.items():
            all_items.extend(items)
        
        all_items.sort(key=lambda x: x.size, reverse=True)
        
        report.append("TOP 20 LARGEST ITEMS:")
        report.append("-" * 70)
        
        for idx, item in enumerate(all_items[:20], 1):
            safe_indicator = "✅ SAFE" if item.is_safe_to_delete else "⚠️  RISKY"
            report.append(f"{idx:2d}. {self.format_size(item.size):>12} | {safe_indicator} | {item.path}")
        
        report.append("")
        report.append("=" * 70)
        report.append("GROUPED BY CATEGORY:")
        report.append("=" * 70)
        
        for category, items in sorted(self.results.items()):
            if items:
                category_size = sum(item.size for item in items)
                report.append(f"\n📁 {category} ({self.format_size(category_size)})")
                report.append("-" * 70)
                
                items.sort(key=lambda x: x.size, reverse=True)
                for item in items[:5]:  # Top 5 per category
                    safe = "✅" if item.is_safe_to_delete else "⚠️"
                    report.append(f"  {safe} {self.format_size(item.size):>12} {item.path}")
                
                if len(items) > 5:
                    report.append(f"  ... and {len(items) - 5} more items")
        
        report.append("")
        report.append("=" * 70)
        report.append("RECOMMENDATIONS:")
        report.append("=" * 70)
        report.append("")
        
        safe_total = sum(item.size for category, items in self.results.items() 
                        for item in items if item.is_safe_to_delete)
        
        report.append(f"✅ Safe to delete: {self.format_size(safe_total)}")
        report.append("   - Empty caches")
        report.append("   - Delete old logs")
        report.append("   - Clean package manager cache")
        report.append("")
        
        report.append("⚠️  Review before deleting:")
        report.append("   - Downloads folder")
        report.append("   - Old backups")
        report.append("   - Application support files")
        report.append("")
        
        report.append("🛡️  DO NOT delete:")
        report.append("   - System files")
        report.append("   - Application binaries")
        report.append("   - Important documents")
        
        return "\n".join(report)
    
    def export_to_json(self, filename: str = "storage_report.json"):
        """Export hasil ke JSON"""
        data = {
            'total_size': self.total_size,
            'total_size_formatted': self.format_size(self.total_size),
            'categories': {}
        }
        
        for category, items in self.results.items():
            data['categories'][category] = {
                'total_size': sum(item.size for item in items),
                'items': [asdict(item) for item in items]
            }
        
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"\n💾 Report exported to: {filename}")
    
    def cleanup_safe_files(self, dry_run: bool = True):
        """
        Cleanup file yang aman
        
        Args:
            dry_run: Jika True, hanya tampilkan apa yang akan dihapus
        """
        if dry_run:
            print("\n🧹 DRY RUN - Menampilkan file yang akan dihapus:")
            print("=" * 70)
        else:
            print("\n🧹 CLEANING - Menghapus file...")
            print("=" * 70)
        
        cleaned_size = 0
        cleaned_count = 0
        to_delete_items = []
        
        # Collect all items to delete first
        for category, items in self.results.items():
            if not items:
                continue
            
            for item in items:
                if not item.is_safe_to_delete:
                    continue
                
                to_delete_items.append(item)
                
                if dry_run:
                    print(f"[DRY RUN] Remove: {item.path} ({self.format_size(item.size)})")
        
        # Process deletion if not dry run
        if not dry_run:
            for item in to_delete_items:
                try:
                    if os.path.isdir(item.path):
                        shutil.rmtree(item.path)
                    else:
                        os.remove(item.path)
                    print(f"✓ Deleted: {item.path}")
                    cleaned_count += 1
                    cleaned_size += item.size
                except Exception as e:
                    print(f"✗ Error deleting {item.path}: {e}")
        
        # Print summary
        print("=" * 70)
        if dry_run:
            total_to_delete = sum(item.size for item in to_delete_items)
            print(f"Items to clean: {len(to_delete_items)}")
            print(f"Space to recover: {self.format_size(total_to_delete)}")
            print("\n💡 Tip: Run dengan --cleanup untuk benar-benar menghapus files")
        else:
            print(f"Items cleaned: {cleaned_count}")
            print(f"Space recovered: {self.format_size(cleaned_size)}")
            print("\n✅ Cleanup completed!")

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="macOS Storage Analyzer & Cleaner untuk M1 Mac"
    )
    parser.add_argument(
        '--min-size',
        type=int,
        default=100,
        help='Minimum size to report in MB (default: 100)'
    )
    parser.add_argument(
        '--full-scan',
        action='store_true',
        help='Scan full home directory (slower)'
    )
    parser.add_argument(
        '--cleanup',
        action='store_true',
        help='Actually delete safe files (use with caution!)'
    )
    parser.add_argument(
        '--export',
        type=str,
        help='Export report to JSON file'
    )
    
    args = parser.parse_args()
    
    # Create analyzer
    analyzer = StorageAnalyzer(min_size_mb=args.min_size)
    
    # Scan safe directories
    analyzer.scan_safe_directories()
    
    # Scan large directories if requested
    if args.full_scan:
        analyzer.scan_large_directories(depth=4)
    else:
        analyzer.scan_large_directories(depth=2)
    
    # Print report
    print("\n" + analyzer.generate_report())
    
    # Export if requested
    if args.export:
        analyzer.export_to_json(args.export)
    
    # Cleanup if requested
    if args.cleanup:
        response = input("\n⚠️  Are you sure? This will delete safe files. (yes/no): ")
        if response.lower() == 'yes':
            analyzer.cleanup_safe_files(dry_run=False)
        else:
            print("Cancelled.")
    else:
        analyzer.cleanup_safe_files(dry_run=True)

if __name__ == "__main__":
    main()
