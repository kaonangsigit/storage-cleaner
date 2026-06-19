#!/usr/bin/env python3
"""
macOS Backup Tool
Untuk backup files sebelum cleanup ke external drive
"""

import os
import shutil
import json
from pathlib import Path
from typing import List, Dict, Tuple
from datetime import datetime
import subprocess

class BackupTool:
    """Tool untuk backup files ke external drive"""
    
    def __init__(self, mount_point: str = None):
        self.mount_point = mount_point
        self.backup_manifest = {
            'timestamp': datetime.now().isoformat(),
            'mount_point': mount_point,
            'files': [],
            'stats': {
                'total_files': 0,
                'total_size': 0,
                'backup_path': '',
            }
        }
        
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
    
    def list_external_drives(self) -> List[str]:
        """List available external drives"""
        volumes_path = "/Volumes"
        drives = []
        
        try:
            for item in os.listdir(volumes_path):
                item_path = os.path.join(volumes_path, item)
                # Skip Macintosh HD (system drive)
                if os.path.isdir(item_path) and item not in ['Macintosh HD', 'System', 'Data', 'VM', 'Preboot', 'Update']:
                    drives.append(item_path)
        except:
            pass
        
        return drives
    
    def get_drive_space(self, path: str) -> Tuple[int, int, int]:
        """Get drive space info (total, used, free)"""
        try:
            stat = shutil.disk_usage(path)
            return stat.total, stat.used, stat.free
        except:
            return 0, 0, 0
    
    def get_dir_size(self, path: str) -> int:
        """Get directory size"""
        total = 0
        try:
            for dirpath, dirnames, filenames in os.walk(path):
                for filename in filenames:
                    filepath = os.path.join(dirpath, filename)
                    try:
                        total += os.path.getsize(filepath)
                    except (OSError, FileNotFoundError):
                        pass
        except (OSError, PermissionError):
            pass
        
        return total
    
    def select_backup_location(self) -> str:
        """Select backup location"""
        print("\n🔍 Scanning for external drives...")
        print("=" * 80)
        
        drives = self.list_external_drives()
        
        if not drives:
            print("\n❌ No external drives found!")
            print("\nPlease connect an external drive and try again.")
            return None
        
        print(f"\nFound {len(drives)} external drive(s):\n")
        
        for idx, drive in enumerate(drives, 1):
            total, used, free = self.get_drive_space(drive)
            drive_name = os.path.basename(drive)
            
            print(f"{idx}. {drive_name}")
            print(f"   Path: {drive}")
            print(f"   Free space: {self.format_size(free)}")
            print(f"   Total space: {self.format_size(total)}")
            print()
        
        if len(drives) == 1:
            choice = 1
        else:
            while True:
                try:
                    choice = int(input("Select drive number: "))
                    if 1 <= choice <= len(drives):
                        break
                    print("Invalid choice!")
                except ValueError:
                    print("Invalid input!")
        
        return drives[choice - 1]
    
    def create_backup_structure(self, backup_path: str) -> str:
        """Create backup directory structure"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = os.path.join(backup_path, f"macOS_Backup_{timestamp}")
        
        try:
            os.makedirs(backup_dir, exist_ok=True)
            print(f"\n✓ Created backup directory: {backup_dir}")
            return backup_dir
        except Exception as e:
            print(f"✗ Error creating backup directory: {e}")
            return None
    
    def plan_backup(self) -> Dict[str, List[str]]:
        """Plan what to backup"""
        print("\n📋 Planning backup...")
        print("=" * 80)
        
        backup_plan = {
            'Application Support': [],
            'Caches': [],
            'Library Data': [],
        }
        
        # Items to backup
        paths_to_backup = {
            'Application Support': [
                '~/Library/Application Support',
            ],
            'Caches': [
                '~/.cache',
                '~/Library/Caches',
            ],
            'Library Data': [
                '~/Library/Logs',
            ],
        }
        
        for category, paths in paths_to_backup.items():
            for path_pattern in paths:
                path = self.expand_path(path_pattern)
                
                if os.path.exists(path):
                    size = self.get_dir_size(path)
                    backup_plan[category].append({
                        'path': path,
                        'size': size,
                        'name': os.path.basename(path)
                    })
                    print(f"  ✓ {os.path.basename(path):30} {self.format_size(size):>12}")
        
        return backup_plan
    
    def calculate_backup_size(self, backup_plan: Dict) -> int:
        """Calculate total backup size"""
        total = 0
        for category, items in backup_plan.items():
            for item in items:
                total += item['size']
        
        return total
    
    def verify_space(self, backup_path: str, required_size: int) -> bool:
        """Verify enough space on backup drive"""
        total, used, free = self.get_drive_space(backup_path)
        
        # Add 10% buffer
        required_with_buffer = required_size * 1.1
        
        print(f"\n📊 Space check:")
        print(f"  Required: {self.format_size(int(required_with_buffer))}")
        print(f"  Available: {self.format_size(free)}")
        
        if free > required_with_buffer:
            print(f"  ✓ Enough space!")
            return True
        else:
            print(f"  ✗ Not enough space! Need {self.format_size(int(required_with_buffer - free))} more")
            return False
    
    def backup_files(self, backup_dir: str, backup_plan: Dict) -> bool:
        """Execute backup"""
        print(f"\n💾 Starting backup to {backup_dir}...")
        print("=" * 80)
        
        total_files = 0
        total_size = 0
        backed_up_files = []
        
        for category, items in backup_plan.items():
            if not items:
                continue
            
            category_dir = os.path.join(backup_dir, category)
            os.makedirs(category_dir, exist_ok=True)
            
            print(f"\n📁 Backing up {category}...")
            
            for item in items:
                source = item['path']
                dest = os.path.join(category_dir, item['name'])
                
                try:
                    print(f"  Copying {item['name']}... ", end='', flush=True)
                    
                    if os.path.isdir(source):
                        shutil.copytree(source, dest, dirs_exist_ok=True)
                    else:
                        shutil.copy2(source, dest)
                    
                    print(f"✓ ({self.format_size(item['size'])})")
                    
                    total_files += 1
                    total_size += item['size']
                    backed_up_files.append({
                        'category': category,
                        'name': item['name'],
                        'source': source,
                        'dest': dest,
                        'size': item['size'],
                        'timestamp': datetime.now().isoformat()
                    })
                
                except Exception as e:
                    print(f"✗ Error: {e}")
        
        self.backup_manifest['files'] = backed_up_files
        self.backup_manifest['stats']['total_files'] = total_files
        self.backup_manifest['stats']['total_size'] = total_size
        self.backup_manifest['stats']['backup_path'] = backup_dir
        
        return total_files > 0
    
    def verify_backup(self, backup_dir: str) -> bool:
        """Verify backup integrity"""
        print(f"\n🔍 Verifying backup...")
        print("=" * 80)
        
        manifest_path = os.path.join(backup_dir, 'MANIFEST.json')
        
        # Save manifest
        try:
            with open(manifest_path, 'w') as f:
                json.dump(self.backup_manifest, f, indent=2)
            print(f"✓ Manifest saved: {manifest_path}")
        except Exception as e:
            print(f"✗ Error saving manifest: {e}")
            return False
        
        # Verify files
        verified = 0
        for file_info in self.backup_manifest['files']:
            if os.path.exists(file_info['dest']):
                verified += 1
        
        print(f"✓ Verified {verified}/{len(self.backup_manifest['files'])} files")
        
        return verified == len(self.backup_manifest['files'])
    
    def generate_backup_report(self) -> str:
        """Generate backup report"""
        report = []
        report.append("=" * 80)
        report.append("📋 BACKUP REPORT")
        report.append("=" * 80)
        report.append("")
        
        report.append(f"Timestamp: {self.backup_manifest['timestamp']}")
        report.append(f"Backup Location: {self.backup_manifest['stats']['backup_path']}")
        report.append("")
        
        report.append(f"Total Files Backed Up: {self.backup_manifest['stats']['total_files']}")
        report.append(f"Total Size: {self.format_size(self.backup_manifest['stats']['total_size'])}")
        report.append("")
        
        report.append("FILES BACKED UP:")
        report.append("-" * 80)
        
        for file_info in self.backup_manifest['files']:
            report.append(f"  📁 {file_info['category']}")
            report.append(f"     Name: {file_info['name']}")
            report.append(f"     Size: {self.format_size(file_info['size'])}")
            report.append(f"     Destination: {file_info['dest']}")
            report.append("")
        
        report.append("=" * 80)
        report.append("✅ BACKUP COMPLETED")
        report.append("=" * 80)
        report.append("")
        report.append("You can safely cleanup your Mac now.")
        report.append("")
        report.append("To restore files later:")
        report.append("  1. Connect the external drive")
        report.append("  2. Copy files back from this backup")
        report.append("  3. Or reference MANIFEST.json for file locations")
        report.append("")
        
        return "\n".join(report)
    
    def run_backup(self) -> bool:
        """Run full backup process"""
        print("\n" + "=" * 80)
        print("🚀 macOS BACKUP TOOL")
        print("=" * 80)
        
        # Select drive
        if not self.mount_point:
            self.mount_point = self.select_backup_location()
            if not self.mount_point:
                return False
        
        # Verify drive exists
        if not os.path.exists(self.mount_point):
            print(f"✗ Mount point not found: {self.mount_point}")
            return False
        
        # Plan backup
        backup_plan = self.plan_backup()
        
        # Calculate size
        backup_size = self.calculate_backup_size(backup_plan)
        print(f"\nTotal backup size: {self.format_size(backup_size)}")
        
        # Verify space
        if not self.verify_space(self.mount_point, backup_size):
            print("\n✗ Not enough space on external drive!")
            return False
        
        # Create backup structure
        backup_dir = self.create_backup_structure(self.mount_point)
        if not backup_dir:
            return False
        
        # Confirm
        response = input("\n⚠️  Proceed with backup? (yes/no): ")
        if response.lower() != 'yes':
            print("Cancelled.")
            return False
        
        # Execute backup
        if not self.backup_files(backup_dir, backup_plan):
            print("✗ Backup failed!")
            return False
        
        # Verify
        if not self.verify_backup(backup_dir):
            print("⚠️  Backup verification failed!")
        
        # Print report
        print("\n" + self.generate_backup_report())
        
        return True

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="macOS Backup Tool - Backup files to external drive"
    )
    parser.add_argument(
        '--mount-point',
        type=str,
        help='Path to external drive mount point'
    )
    
    args = parser.parse_args()
    
    backup_tool = BackupTool(mount_point=args.mount_point)
    success = backup_tool.run_backup()
    
    if success:
        print("\n✅ Backup completed successfully!")
        print("\nNext steps:")
        print("  1. Run: python3 storage_analyzer.py --cleanup")
        print("  2. Run: python3 advanced_cleaner.py --cleanup")
    else:
        print("\n✗ Backup failed!")

if __name__ == "__main__":
    main()
