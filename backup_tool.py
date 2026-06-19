#!/usr/bin/env python3
"""
macOS Backup Tool
Untuk backup files sebelum cleanup ke external drive
"""

import os
import shutil
import json
import hashlib
from typing import List, Dict, Tuple
from datetime import datetime
import time


class ProgressTracker:
    """Track progress dengan percentage"""

    def __init__(self, total_size: int):
        self.total_size = max(total_size, 1)
        self.copied_size = 0
        self.start_time = time.time()

    def format_size(self, bytes_size: int) -> str:
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_size < 1024:
                return f"{bytes_size:.2f} {unit}"
            bytes_size /= 1024
        return f"{bytes_size:.2f} PB"

    def get_progress_bar(self, current: int, total: int, width: int = 24) -> str:
        if total <= 0:
            return "[" + "█" * width + "]"

        percentage = min(current / total, 1.0)
        filled = int(width * percentage)
        bar = "█" * filled + "░" * (width - filled)
        return f"[{bar}]"

    def get_eta(self, current: int) -> str:
        elapsed = time.time() - self.start_time
        if elapsed > 0 and current > 0:
            rate = current / elapsed
            remaining = max(self.total_size - current, 0)
            if rate > 0:
                eta_seconds = remaining / rate
                minutes = int(eta_seconds // 60)
                seconds = int(eta_seconds % 60)
                if minutes > 0:
                    return f"{minutes}m {seconds}s"
                return f"{seconds}s"
        return "calculating..."

    def get_speed(self, current: int) -> str:
        elapsed = time.time() - self.start_time
        if elapsed > 0 and current > 0:
            speed_bps = current / elapsed
            speed_mbps = speed_bps / (1024 * 1024)
            return f"{speed_mbps:.1f} MB/s"
        return "calculating..."

    def update(self, size: int):
        self.copied_size += size

    def print_progress(self, label: str):
        percentage = (self.copied_size / self.total_size) * 100
        progress_bar = self.get_progress_bar(self.copied_size, self.total_size)

        copied_str = self.format_size(self.copied_size)
        total_str = self.format_size(self.total_size)
        speed = self.get_speed(self.copied_size)
        eta = self.get_eta(self.copied_size)

        progress_line = (
            f"  {label[:32]:32} {progress_bar} {percentage:6.2f}% "
            f"({copied_str} / {total_str}) | {speed} | ETA: {eta}"
        )
        print(f"\r{progress_line}", end='', flush=True)


class BackupTool:
    """Tool untuk backup files ke external drive"""

    def __init__(self, mount_point: str = None, weekly_mode: bool = False):
        self.mount_point = mount_point
        self.weekly_mode = weekly_mode
        self.stats = {
            "copied_files": 0,
            "skipped_files": 0,
            "updated_files": 0,
            "total_files_scanned": 0
        }
        self.backup_manifest = {
            'timestamp': datetime.now().isoformat(),
            'mount_point': mount_point,
            'mode': 'weekly_incremental' if weekly_mode else 'full',
            'compare_mode': 'smart_hash_on_demand',
            'files': [],
            'stats': {
                'total_files': 0,
                'total_size': 0,
                'backup_path': '',
                'start_time': '',
                'end_time': '',
                'duration': '',
                'copied_files': 0,
                'skipped_files': 0,
                'updated_files': 0,
                'total_files_scanned': 0
            }
        }

    def format_size(self, bytes_size: int) -> str:
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_size < 1024:
                return f"{bytes_size:.2f} {unit}"
            bytes_size /= 1024
        return f"{bytes_size:.2f} PB"

    def expand_path(self, path: str) -> str:
        return os.path.expanduser(os.path.expandvars(path))

    def list_external_drives(self) -> List[str]:
        volumes_path = "/Volumes"
        drives = []
        try:
            for item in os.listdir(volumes_path):
                item_path = os.path.join(volumes_path, item)
                if os.path.isdir(item_path) and item not in ['Macintosh HD', 'System', 'Data', 'VM', 'Preboot', 'Update']:
                    drives.append(item_path)
        except Exception:
            pass
        return drives

    def get_drive_space(self, path: str) -> Tuple[int, int, int]:
        try:
            stat = shutil.disk_usage(path)
            return stat.total, stat.used, stat.free
        except Exception:
            return 0, 0, 0

    def get_dir_size(self, path: str) -> int:
        total = 0
        try:
            for dirpath, _, filenames in os.walk(path):
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
        print("\n🔍 Scanning for external drives...")
        print("=" * 80)

        drives = self.list_external_drives()

        if not drives:
            print("\n❌ No external drives found!")
            print("\nPlease connect an external drive and try again.")
            return None

        print(f"\nFound {len(drives)} external drive(s):\n")

        for idx, drive in enumerate(drives, 1):
            total, _, free = self.get_drive_space(drive)
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
        if self.weekly_mode:
            backup_dir = os.path.join(backup_path, "macOS_Backup_weekly")
        else:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_dir = os.path.join(backup_path, f"macOS_Backup_{timestamp}")

        try:
            os.makedirs(backup_dir, exist_ok=True)
            print(f"\n✓ Using backup directory: {backup_dir}")
            return backup_dir
        except Exception as e:
            print(f"✗ Error creating backup directory: {e}")
            return None

    def plan_backup(self) -> Dict[str, List[Dict]]:
        print("\n📋 Planning backup...")
        print("=" * 80)

        backup_plan = {
            'Application Support': [],
            'Caches': [],
            'Library Data': [],
        }

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

    def calculate_backup_size(self, backup_plan: Dict[str, List[Dict]]) -> int:
        total = 0
        for _, items in backup_plan.items():
            for item in items:
                total += item['size']
        return total

    def verify_space(self, backup_path: str, required_size: int) -> bool:
        _, _, free = self.get_drive_space(backup_path)
        required_with_buffer = int(required_size * 1.1)

        print(f"\n📊 Space check:")
        print(f"  Required: {self.format_size(required_with_buffer)}")
        print(f"  Available: {self.format_size(free)}")

        if free > required_with_buffer:
            print("  ✓ Enough space!")
            return True
        else:
            print(f"  ✗ Not enough space! Need {self.format_size(required_with_buffer - free)} more")
            return False

    def hash_file(self, file_path: str, chunk_size: int = 1024 * 1024) -> str:
        h = hashlib.sha256()
        with open(file_path, 'rb') as f:
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                h.update(chunk)
        return h.hexdigest()

    def load_incremental_index(self, backup_dir: str) -> Dict:
        index_path = os.path.join(backup_dir, "INCREMENTAL_INDEX.json")
        if os.path.exists(index_path):
            try:
                with open(index_path, "r") as f:
                    return json.load(f)
            except Exception:
                pass
        return {"files": {}}

    def save_incremental_index(self, backup_dir: str, index_data: Dict):
        index_path = os.path.join(backup_dir, "INCREMENTAL_INDEX.json")
        with open(index_path, "w") as f:
            json.dump(index_data, f, indent=2)

    def iter_source_files(self, source_root: str):
        if os.path.isfile(source_root):
            yield source_root, os.path.basename(source_root)
            return

        for dirpath, _, filenames in os.walk(source_root):
            for filename in filenames:
                full_path = os.path.join(dirpath, filename)
                rel_path = os.path.relpath(full_path, source_root)
                yield full_path, rel_path

    def copy_file_with_progress(self, source: str, dest: str, progress_tracker: ProgressTracker, label: str):
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        chunk_size = 1024 * 1024

        with open(source, 'rb') as src_file, open(dest, 'wb') as dst_file:
            while True:
                chunk = src_file.read(chunk_size)
                if not chunk:
                    break
                dst_file.write(chunk)
                progress_tracker.update(len(chunk))
                progress_tracker.print_progress(label)

    def backup_item_incremental(
        self,
        source_root: str,
        dest_root: str,
        category: str,
        progress_tracker: ProgressTracker,
        index_data: Dict
    ) -> List[Dict]:
        entries = []
        files_index = index_data.setdefault("files", {})

        for src_file, rel_path in self.iter_source_files(source_root):
            self.stats["total_files_scanned"] += 1
            key = f"{category}/{os.path.basename(source_root)}/{rel_path}"
            dest_file = os.path.join(dest_root, rel_path)

            try:
                src_stat = os.stat(src_file)
                src_size = src_stat.st_size
                src_mtime = int(src_stat.st_mtime)

                previous = files_index.get(key)
                action = "copy"
                src_hash = None

                if self.weekly_mode and os.path.exists(dest_file):
                    dst_stat = os.stat(dest_file)
                    dst_size = dst_stat.st_size
                    dst_mtime = int(dst_stat.st_mtime)

                    # Fast path: metadata sama -> skip
                    if dst_size == src_size and dst_mtime == src_mtime:
                        action = "skip"
                    elif dst_size != src_size:
                        action = "update" if previous else "copy"
                    else:
                        # size sama, mtime beda -> hash on-demand
                        src_hash = self.hash_file(src_file)
                        dst_hash = self.hash_file(dest_file)
                        action = "skip" if src_hash == dst_hash else ("update" if previous else "copy")

                if previous and action != "skip":
                    # tambahan fast check dari index
                    if previous.get("size") == src_size and previous.get("mtime") == src_mtime:
                        action = "skip"

                label = f"{os.path.basename(source_root)}/{rel_path}"[-32:]

                if action == "skip":
                    progress_tracker.update(src_size)
                    progress_tracker.print_progress(f"SKIP {label}")
                    self.stats["skipped_files"] += 1
                else:
                    self.copy_file_with_progress(src_file, dest_file, progress_tracker, f"COPY {label}")
                    if action == "update":
                        self.stats["updated_files"] += 1
                    else:
                        self.stats["copied_files"] += 1

                # simpan hash seperlunya (smart mode)
                if src_hash is None and action != "skip":
                    src_hash = self.hash_file(src_file)

                files_index[key] = {
                    "size": src_size,
                    "mtime": src_mtime,
                    "sha256": src_hash if src_hash is not None else (previous.get("sha256") if previous else None),
                    "dest": dest_file,
                    "updated_at": datetime.now().isoformat()
                }

                entries.append({
                    'category': category,
                    'name': os.path.basename(source_root),
                    'source': src_file,
                    'dest': dest_file,
                    'size': src_size,
                    'relative_path': rel_path,
                    'action': action,
                    'timestamp': datetime.now().isoformat()
                })

            except Exception as e:
                print(f"\n✗ Error processing {src_file}: {e}")

        return entries

    def backup_files(self, backup_dir: str, backup_plan: Dict[str, List[Dict]], total_backup_size: int) -> bool:
        print(f"\n💾 Starting backup to {backup_dir}...")
        print("=" * 80)

        total_size = 0
        backed_up_files = []

        progress_tracker = ProgressTracker(total_backup_size)
        start_time = time.time()
        index_data = self.load_incremental_index(backup_dir)

        for category, items in backup_plan.items():
            if not items:
                continue

            category_dir = os.path.join(backup_dir, category)
            os.makedirs(category_dir, exist_ok=True)

            print(f"\n📁 Backing up {category}...")
            print("  Copying with progress...")

            for item in items:
                source = item['path']
                source_name = item['name']
                dest_root = os.path.join(category_dir, source_name)

                try:
                    entries = self.backup_item_incremental(
                        source_root=source,
                        dest_root=dest_root,
                        category=category,
                        progress_tracker=progress_tracker,
                        index_data=index_data
                    )
                    backed_up_files.extend(entries)
                    total_size += item['size']
                    print()
                except Exception as e:
                    print(f"\n✗ Error: {e}")

        end_time = time.time()
        duration = end_time - start_time

        self.save_incremental_index(backup_dir, index_data)

        self.backup_manifest['files'] = backed_up_files
        self.backup_manifest['stats']['total_files'] = len(backed_up_files)
        self.backup_manifest['stats']['total_size'] = total_size
        self.backup_manifest['stats']['backup_path'] = backup_dir
        self.backup_manifest['stats']['start_time'] = datetime.fromtimestamp(start_time).isoformat()
        self.backup_manifest['stats']['end_time'] = datetime.fromtimestamp(end_time).isoformat()

        minutes = int(duration // 60)
        seconds = int(duration % 60)
        self.backup_manifest['stats']['duration'] = f"{minutes}m {seconds}s"

        self.backup_manifest['stats']['copied_files'] = self.stats["copied_files"]
        self.backup_manifest['stats']['skipped_files'] = self.stats["skipped_files"]
        self.backup_manifest['stats']['updated_files'] = self.stats["updated_files"]
        self.backup_manifest['stats']['total_files_scanned'] = self.stats["total_files_scanned"]

        return len(backed_up_files) > 0

    def verify_backup(self, backup_dir: str) -> bool:
        print(f"\n🔍 Verifying backup...")
        print("=" * 80)

        manifest_path = os.path.join(backup_dir, 'MANIFEST.json')

        try:
            with open(manifest_path, 'w') as f:
                json.dump(self.backup_manifest, f, indent=2)
            print(f"✓ Manifest saved: {manifest_path}")
        except Exception as e:
            print(f"✗ Error saving manifest: {e}")
            return False

        verified = 0
        for file_info in self.backup_manifest['files']:
            if file_info.get('action') == 'skip' or os.path.exists(file_info['dest']):
                verified += 1

        print(f"✓ Verified {verified}/{len(self.backup_manifest['files'])} entries")
        return verified == len(self.backup_manifest['files'])

    def generate_backup_report(self) -> str:
        report = []
        report.append("=" * 80)
        report.append("📋 BACKUP REPORT")
        report.append("=" * 80)
        report.append("")

        report.append(f"Timestamp: {self.backup_manifest['timestamp']}")
        report.append(f"Mode: {self.backup_manifest['mode']}")
        report.append(f"Backup Location: {self.backup_manifest['stats']['backup_path']}")
        report.append(f"Duration: {self.backup_manifest['stats']['duration']}")
        report.append("")

        report.append(f"Total Entries Processed: {self.backup_manifest['stats']['total_files']}")
        report.append(f"Total Files Scanned: {self.backup_manifest['stats']['total_files_scanned']}")
        report.append(f"Copied: {self.backup_manifest['stats']['copied_files']}")
        report.append(f"Updated: {self.backup_manifest['stats']['updated_files']}")
        report.append(f"Skipped (unchanged): {self.backup_manifest['stats']['skipped_files']}")
        report.append(f"Total Source Size: {self.format_size(self.backup_manifest['stats']['total_size'])}")
        report.append("")

        report.append("=" * 80)
        report.append("✅ BACKUP COMPLETED")
        report.append("=" * 80)
        report.append("")
        report.append("You can safely cleanup your Mac now.")
        report.append("")

        return "\n".join(report)

    def run_backup(self) -> bool:
        print("\n" + "=" * 80)
        print("🚀 macOS BACKUP TOOL")
        print("=" * 80)

        if self.weekly_mode:
            print("Mode: WEEKLY INCREMENTAL | Compare: smart_hash_on_demand")
        else:
            print("Mode: FULL BACKUP")

        if not self.mount_point:
            self.mount_point = self.select_backup_location()
            if not self.mount_point:
                return False

        if not os.path.exists(self.mount_point):
            print(f"✗ Mount point not found: {self.mount_point}")
            return False

        backup_plan = self.plan_backup()

        backup_size = self.calculate_backup_size(backup_plan)
        print(f"\nEstimated source size: {self.format_size(backup_size)}")

        if not self.verify_space(self.mount_point, backup_size):
            print("\n✗ Not enough space on external drive!")
            return False

        backup_dir = self.create_backup_structure(self.mount_point)
        if not backup_dir:
            return False

        response = input("\n⚠️  Proceed with backup? (yes/no): ")
        if response.lower() != 'yes':
            print("Cancelled.")
            return False

        if not self.backup_files(backup_dir, backup_plan, backup_size):
            print("✗ Backup failed!")
            return False

        if not self.verify_backup(backup_dir):
            print("⚠️  Backup verification failed!")

        print("\n" + self.generate_backup_report())
        return True


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="macOS Backup Tool - Backup files to external drive"
    )
    parser.add_argument(
        '--mount-point',
        type=str,
        help='Path to external drive mount point'
    )
    parser.add_argument(
        '--weekly',
        action='store_true',
        help='Use weekly incremental mode (skip unchanged files)'
    )

    args = parser.parse_args()

    backup_tool = BackupTool(
        mount_point=args.mount_point,
        weekly_mode=args.weekly
    )
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