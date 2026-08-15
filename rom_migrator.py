#!/usr/bin/env python3
"""
Anbernic to Knulli ROM migrator - Anbernic → Knulli/Batocera
Interactive mode with simple prompts
"""

import argparse
import datetime as dt
import hashlib
import json
import os
import shutil
import sys
import time
import traceback
from pathlib import Path
from zoneinfo import ZoneInfo

from config import (
    ANBERNIC_TO_KNULLI,
    MERGE_SYSTEMS,
    ROM_EXTS_FINAL,
)
from permission_error_handler import PermissionErrorHandler
from progress_bar import SimpleProgressBar


class ROMMigrator:
    """Migrator with simple progress bar and error handling."""

    def __init__(
        self, source: str, dest: str, dry_run: bool = False, verbose: bool = False
    ):
        """__init__."""
        self.source = Path(source)
        self.dest = Path(dest)
        self.dry_run = dry_run
        self.verbose = verbose

        self.stats = {
            "total": 0,
            "copied": 0,
            "skipped": 0,
            "errors": 0,
            "size": 0,
            "permission_errors": 0,
            "other_errors": 0,
            "systems": {},
            "renamed_files": 0,
        }

        self.error_log: list[dict] = []
        self.permission_handler = PermissionErrorHandler()

        # Use config from config.py
        self.ANBERNIC_TO_KNULLI = ANBERNIC_TO_KNULLI
        self.MERGE_SYSTEMS = MERGE_SYSTEMS
        self.ROM_EXTS = ROM_EXTS_FINAL

        # Create reverse mapping for folder name lookup (case-insensitive)
        self.folder_mapping = {}
        for anbernic_folder, knulli_folder in self.ANBERNIC_TO_KNULLI.items():
            self.folder_mapping[anbernic_folder.lower()] = knulli_folder

        # Create mapping for systems that merge into one folder
        self.merge_mapping = {}
        for target_folder, source_folders in self.MERGE_SYSTEMS.items():
            for source_folder in source_folders:
                self.merge_mapping[source_folder.lower()] = target_folder

        # Counter for generating unique names
        self.rename_counter = 0

        self._validate()

    def _validate(self):
        """Validate paths and permissions."""
        print("\n🔍 Checking access...")

        # Check source
        if not self.source.exists():
            raise ValueError(f"🚫 Folder not found: {self.source}")

        # Check read access to source
        read_ok, read_msg = self.permission_handler.check_read_access(self.source)
        if not read_ok:
            print(
                f"   ⚠️  {read_msg}\n\n💡 "
                f"Recommendations:\n{self.permission_handler.get_permission_suggestion(read_msg)}"
            )
            if not self.dry_run:
                answer = input("\nContinue? (y/N): ")
                if answer.lower() != "y":
                    raise PermissionError("Insufficient permissions to read source")

        # Check write access to destination
        write_ok, write_msg = self.permission_handler.check_write_access(self.dest)
        if not write_ok:
            print(
                f"   ⚠️  {write_msg}\n\n💡 "
                f"Recommendations:\n{self.permission_handler.get_permission_suggestion(write_msg)}"
            )
            if not self.dry_run:
                answer = input("\nContinue? (y/N): ")
                if answer.lower() != "y":
                    raise PermissionError(
                        "Insufficient permissions to write to destination"
                    )

        # Check that source and destination are not the same
        if self.source == self.dest:
            raise ValueError("🚫 Source and destination are the same")

        # Check that source is not inside destination
        try:
            if str(self.dest) in str(self.source) and self.source != self.dest:
                print(
                    f"⚠️  WARNING: Source is inside destination folder!\n   "
                    f"Source: {self.source}\n   "
                    f"Destination: {self.dest}"
                )
                if not self.dry_run:
                    answer = input("Continue? (y/N): ")
                    if answer.lower() != "y":
                        raise ValueError("Operation cancelled")
        except Exception as e:
            print(f"Something went wrong: \n\n{e}")

        # Display information about systems that will be merged
        merge_info = "\n📋 System merge information:"
        for target, sources in self.MERGE_SYSTEMS.items():
            merge_info += f"\n   {', '.join(sources)} -> {target}"
        print(merge_info + "\n\n   ✅ Access check passed")

    def _get_knulli_folder(self, anbernic_folder: str) -> str:
        """Convert Anbernic folder name to Knulli folder name."""
        folder_lower = anbernic_folder.lower()

        # Check if it's a merging system
        if folder_lower in self.merge_mapping:
            return self.merge_mapping[folder_lower]

        # Direct match
        if folder_lower in self.folder_mapping:
            return self.folder_mapping[folder_lower]

        # Partial match
        for pattern, knulli_name in self.folder_mapping.items():
            if pattern in folder_lower or folder_lower in pattern:
                return knulli_name

        # If not found - use name as is (lowercase)
        return folder_lower

    def _get_original_system(self, folder_name: str) -> str:
        """Returns the original Anbernic system name for a folder."""
        folder_lower = folder_name.lower()

        # Check if folder is a system from ANBERNIC_TO_KNULLI
        for anbernic_system in self.ANBERNIC_TO_KNULLI.keys():
            if anbernic_system.lower() == folder_lower:
                return anbernic_system

        # Partial match
        for anbernic_system in self.ANBERNIC_TO_KNULLI.keys():
            if (
                anbernic_system.lower() in folder_lower
                or folder_lower in anbernic_system.lower()
            ):
                return anbernic_system

        return folder_name.upper()

    def _generate_unique_filename(
        self, original_path: Path, system: str, dest_folder: Path
    ) -> Path:
        """Generate unique filename on conflict."""
        stem = original_path.stem
        suffix = original_path.suffix

        # Check if name already has system suffix
        if f"_{system}" in stem:
            # If it does, add a number
            self.rename_counter += 1
            new_name = f"{stem}_{self.rename_counter}{suffix}"
        else:
            # Add system suffix
            new_name = f"{stem}_{system}{suffix}"

        new_path = dest_folder / new_name

        # If file with this name still exists, add a number
        counter = 1
        while new_path.exists():
            new_name = f"{stem}_{system}_{counter}{suffix}"
            new_path = dest_folder / new_name
            counter += 1

        return new_path

    def _detect_system_from_path(self, folder_path: Path) -> tuple[str, str]:
        """Detects system from folder path and returns (knulli_system, original_system)."""
        # Check all nesting levels
        for parent in folder_path.parents:
            if parent == self.source:
                continue

            # Check if folder is a system that maps to fbneo
            parent_name = parent.name
            parent_lower = parent_name.lower()

            if parent_lower in self.merge_mapping:
                return self.merge_mapping[parent_lower], parent_name.upper()

            knulli_name = self._get_knulli_folder(parent_name)
            if knulli_name != parent_name.lower():
                return knulli_name, self._get_original_system(parent_name)

        # If not found by path, try folder name
        folder_name = folder_path.name
        knulli_name = self._get_knulli_folder(folder_name)
        original_system = self._get_original_system(folder_name)

        return knulli_name, original_system

    def _find_roms(self, folder: Path) -> list[Path]:
        """Find all ROM files in a folder."""
        roms = []
        for ext in self.ROM_EXTS:
            try:
                roms.extend(folder.rglob(f"*{ext}"))
                roms.extend(folder.rglob(f"*{ext.upper()}"))
            except PermissionError:
                print(f"   ⚠️  No access to folder: {folder}")
                continue
            except Exception as e:
                print(f"   ⚠️  Error scanning {folder}: {e}")
                continue
        return sorted(set(roms))

    def _get_hash(self, filepath: Path) -> str:
        """Calculate SHA-256 hash of file."""
        sha256 = hashlib.sha256()
        try:
            with open(filepath, "rb") as f:
                for chunk in iter(lambda: f.read(8192), b""):
                    sha256.update(chunk)
            return sha256.hexdigest()
        except PermissionError:
            self._log_error(filepath, "Permission denied when reading")
            return ""
        except Exception as e:
            self._log_error(filepath, f"Read error: {e}")
            return ""

    def _log_error(self, filepath: Path, error_msg: str):
        """Log error."""
        self.error_log.append(
            {
                "file": str(filepath),
                "error": error_msg,
                "timestamp": dt.datetime.now(tz=ZoneInfo("UTC")).isoformat(),
            }
        )
        self.stats["errors"] += 1
        error_lower = error_msg.lower()
        if "permission" in error_lower or "access" in error_lower:
            self.stats["permission_errors"] += 1
        else:
            self.stats["other_errors"] += 1

    def _format_size(self, size: int) -> str:
        """Format size to human-readable format."""
        for unit in ["B", "KB", "MB", "GB"]:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"

    def _copy_file(
        self, src: Path, dst: Path, original_system: str = ""
    ) -> tuple[bool, str, int, Path]:
        """Copy file with permission error handling and name conflict resolution."""
        actual_dst = dst

        try:
            # Check access to source file
            read_ok, read_msg = self.permission_handler.check_read_access(src)
            if not read_ok:
                self._log_error(src, read_msg)
                return False, f"source access error: {read_msg}", 0, actual_dst

            # Check access to destination folder
            write_ok, write_msg = self.permission_handler.check_write_access(dst.parent)
            if not write_ok:
                self._log_error(dst, write_msg)
                return False, f"destination access error: {write_msg}", 0, actual_dst

            # Create destination folder
            try:
                dst.parent.mkdir(parents=True, exist_ok=True)
            except PermissionError as e:
                self._log_error(dst, f"Permission denied when creating folder: {e}")
                return (
                    False,
                    f"no permission to create folder: {dst.parent}",
                    0,
                    actual_dst,
                )
            except Exception as e:
                self._log_error(dst, f"Error creating folder: {e}")
                return False, f"folder creation error: {e}", 0, actual_dst

            # Check file existence and handle conflicts
            if dst.exists():
                # Check hashes
                try:
                    src_hash = self._get_hash(src)
                    dst_hash = self._get_hash(dst)
                    if src_hash == dst_hash and src_hash:
                        return True, "skipped (identical)", 0, actual_dst
                except Exception as e:
                    self._log_error(dst, f"Hash check error: {e}")

                # If file exists and this is fbneo system (merged)
                if original_system and dst.parent.name == "fbneo":
                    # Generate unique name
                    actual_dst = self._generate_unique_filename(
                        src, original_system, dst.parent
                    )
                    self.stats["renamed_files"] += 1
                    if self.verbose:
                        print(f"        🔄 Renamed: {dst.name} -> {actual_dst.name}")

            # COPY the file (source is not deleted!)
            if not self.dry_run:
                try:
                    shutil.copy2(src, actual_dst)
                except PermissionError as e:
                    self._log_error(src, f"Permission denied when copying: {e}")
                    return False, f"no permission to copy: {e}", 0, actual_dst
                except OSError as e:
                    if "Read-only file system" in str(e):
                        self._log_error(src, f"Read-only file system: {e}")
                        return False, "read-only disk", 0, actual_dst
                    raise

            return True, "copied", src.stat().st_size, actual_dst

        except PermissionError as e:
            error_msg = f"Permission denied: {e}"
            self._log_error(src, error_msg)

            if "Read-only" in str(e) or "read-only" in str(e):
                return False, "error: read-only disk", 0, actual_dst
            else:
                return False, f"error: insufficient permissions ({e})", 0, actual_dst

        except OSError as e:
            error_msg = f"OS Error: {e}"
            self._log_error(src, error_msg)

            if "No space left" in str(e):
                return False, "error: insufficient disk space", 0, actual_dst
            elif "Permission" in str(e) or "Access" in str(e):
                return False, f"access error: {e}", 0, actual_dst
            else:
                return False, f"system error: {e}", 0, actual_dst

        except Exception as e:
            error_msg = f"Unknown error: {e}"
            self._log_error(src, error_msg)
            return False, f"error: {e}", 0, actual_dst

    def scan_source(self) -> dict[str, list[tuple[Path, str]]]:
        """Scan source folder and group files by Knulli systems."""
        systems = {}

        print("\n🔍 Scanning source folder...")

        try:
            items = list(self.source.iterdir())
        except PermissionError:
            print(
                f"🚫 No access to folder: {self.source}\n\n💡 Recommendations:"
                f"\n{self.permission_handler.get_permission_suggestion('Permission denied')}"
            )
            return systems

        # First check root folders
        for item in items:
            if item.is_dir():
                try:
                    # Determine system for Knulli
                    knulli_system = self._get_knulli_folder(item.name)
                    original_system = self._get_original_system(item.name)

                    # Check if there are ROM files
                    roms = self._find_roms(item)
                    if roms:
                        if knulli_system not in systems:
                            systems[knulli_system] = []
                        systems[knulli_system].append((item, original_system))
                        print(
                            f"   ✅ {item.name} -> {knulli_system} ({len(roms)} files)"
                        )
                        if original_system and original_system != item.name.upper():
                            print(f"      (original system: {original_system})")
                    else:
                        print(f"   ⚠️  {item.name} -> {knulli_system} (no ROM files)")
                except PermissionError:
                    print(f"   ⚠️  No access to folder: {item.name}")
                    continue

        # If no folders with ROMs, search nested
        if not systems:
            print("   Searching nested folders for ROMs...")
            try:
                for item in self.source.rglob("*"):
                    if item.is_dir():
                        try:
                            roms = self._find_roms(item)
                            if roms:
                                knulli_system, original_system = (
                                    self._detect_system_from_path(item)
                                )
                                if knulli_system not in systems:
                                    systems[knulli_system] = []
                                if not any(
                                    folder == item
                                    for folder, _ in systems[knulli_system]
                                ):
                                    systems[knulli_system].append(
                                        (item, original_system)
                                    )
                                    print(
                                        f"   ✅ {item.relative_to(self.source)} -> {knulli_system} ({len(roms)} files)"
                                    )
                                    if original_system:
                                        print(
                                            f"      (original system: {original_system})"
                                        )
                        except PermissionError:
                            continue
            except PermissionError:
                print("   ⚠️  No access to some nested folders")

        return systems

    def run(self) -> bool:
        """Run migration."""
        print(
            f"{'=' * 60}\n"
            f"🎮 ROM Migrator (Anbernic → Knulli/Batocera)\n"
            f"{'=' * 60}\n"
            f"📂 Source: {self.source}\n"
            f"📂 Destination: {self.dest}\n"
            f"💾 Mode: {'DRY RUN' if self.dry_run else 'REAL'}\n"
            f"⚠️  Source files are NOT deleted"
            f"{'\n   (changes are not applied)' if self.dry_run else ''}\n"
        )

        # Scan
        systems = self.scan_source()

        if not systems:
            print("\n🚫 ROM files not found")

            # Check if there are any files in the folder
            try:
                files = list(self.source.rglob("*"))
                if files:
                    print(
                        f"   There are files in the folder, but no ROM extensions found\n   "
                        f"Supported extensions: {', '.join(sorted(self.ROM_EXTS))[:100]}..."
                    )
            except Exception as e:
                print(f"Something went wrong: \n\n{e}")

            return False

        # Count total files
        total_files = 0
        systems_header = "\n📊 Systems found for migration:"
        for system, folders in systems.items():
            system_total = 0
            for folder, original_system in folders:
                try:
                    roms = self._find_roms(folder)
                    system_total += len(roms)
                except PermissionError:
                    systems_header += f"\n   ⚠️  {system}: no access to some folders"
                    continue
            total_files += system_total
            systems_header += f"\n   {system}: {system_total} files"

        print(systems_header + f"\n\n📁 Total found: {total_files} ROM files")

        if total_files == 0:
            print("\n🚫 ROM files not found")
            return False

        # Check free space
        try:
            source_size = sum(
                f.stat().st_size for f in self.source.rglob("*") if f.is_file()
            )
            dest_free = shutil.disk_usage(self.dest).free

            if source_size > dest_free:
                print(
                    f"\n⚠️  Insufficient space! Need: {self._format_size(source_size)}, "
                    f"available: {self._format_size(dest_free)}"
                )
                if not self.dry_run:
                    answer = input("Continue? (y/N): ")
                    if answer.lower() != "y":
                        print("Cancelled")
                        return False
        except PermissionError:
            print("\n⚠️  Could not check free space (insufficient permissions)")
        except Exception as e:
            print(f"\n⚠️  Could not check free space: {e}")

        # Confirmation
        if not self.dry_run:
            print()
            answer = input("Continue copying? (y/N): ")
            if answer.lower() != "y":
                print("Cancelled")
                return False

        print("\n" + "=" * 60 + "\n🔄 Copying...\n" + "=" * 60)

        start_time = time.time()

        # MAIN PROGRESS BAR
        progress = SimpleProgressBar(total_files, "Overall progress")

        # Initialize system statistics
        for system in systems.keys():
            self.stats["systems"][system] = {
                "total": 0,
                "copied": 0,
                "skipped": 0,
                "errors": 0,
                "size": 0,
                "renamed": 0,
            }

        # Migrate systems
        for system, folder_list in systems.items():
            # Show current system
            print(f"\n📁 {system}:")

            for folder, original_system in folder_list:
                try:
                    roms = self._find_roms(folder)
                except PermissionError:
                    print(f"   ⚠️  No access to folder: {folder}")
                    continue

                if not roms:
                    continue

                dest_folder = self.dest / system
                try:
                    dest_folder.mkdir(parents=True, exist_ok=True)
                except PermissionError:
                    print(
                        f"   🚫 No permission to create folder: {dest_folder}\n\n💡 "
                        f"Recommendations:\n{self.permission_handler.get_permission_suggestion('Permission denied')}"
                    )
                    continue

                # Show source for fbneo systems
                if system == "fbneo" and original_system:
                    print(f"   📂 {original_system} -> {system}")

                for idx, rom in enumerate(roms, 1):
                    self.stats["total"] += 1
                    self.stats["systems"][system]["total"] += 1

                    try:
                        rel_path = rom.relative_to(folder)
                        dest_file = dest_folder / rel_path
                    except ValueError:
                        dest_file = dest_folder / rom.name

                    # Pass original system for conflict handling
                    success, msg, size, actual_dst = self._copy_file(
                        rom, dest_file, original_system
                    )

                    if success:
                        if msg == "skipped (identical)":
                            self.stats["skipped"] += 1
                            self.stats["systems"][system]["skipped"] += 1
                            status = "⏭️"
                        else:
                            self.stats["copied"] += 1
                            self.stats["size"] += size
                            self.stats["systems"][system]["copied"] += 1
                            self.stats["systems"][system]["size"] += size
                            status = "✅"

                            # Check if file was renamed
                            if actual_dst != dest_file:
                                self.stats["systems"][system]["renamed"] += 1
                    else:
                        self.stats["errors"] += 1
                        self.stats["systems"][system]["errors"] += 1
                        error_lower = msg.lower()
                        if "permission" in error_lower or "access" in error_lower:
                            self.stats["permission_errors"] += 1
                            status = "🔒"
                        else:
                            self.stats["other_errors"] += 1
                            status = "🚫"

                    # Update global progress
                    progress.update(1)

                    # If verbose - show each file
                    if self.verbose:
                        rename_info = (
                            f" -> {actual_dst.name}" if actual_dst != dest_file else ""
                        )
                        print(f"   {status} {rom.name}{rename_info}")
                        if "error" in msg:
                            print(f"        ⚠️  {msg}")

                if self.verbose:
                    print()

        elapsed = time.time() - start_time

        # Summary
        self._print_summary(elapsed)

        # Save error report
        self._save_error_report()

        return True

    def _print_summary(self, elapsed: float):
        """Print summary statistics."""
        summary = (
            f"\n{'=' * 60}\n📊 MIGRATION SUMMARY\n{'=' * 60}\n"
            f"⏱️  Time: {elapsed:.1f} sec\n📁 Total files: {self.stats['total']}\n"
            f"✅ Copied: {self.stats['copied']}\n⏭️  Skipped: {self.stats['skipped']}\n"
            f"🚫 Errors: {self.stats['errors']}"
        )

        if self.stats["permission_errors"] > 0:
            summary += f"\n🔒 Permission errors: {self.stats['permission_errors']}"

        if self.stats["renamed_files"] > 0:
            summary += f"\n🔄 Renamed files: {self.stats['renamed_files']}"

        if self.stats["total"] > 0:
            success_rate = (
                (self.stats["copied"] + self.stats["skipped"]) / self.stats["total"]
            ) * 100
            summary += f"\n📈 Success rate: {success_rate:.1f}%"

        if self.stats["size"] > 0:
            summary += f"\n💾 Copied: {self._format_size(self.stats['size'])}"

        # System statistics
        if self.stats["systems"]:
            summary += "\n\n" + "-" * 60 + "\n📋 By system:"
            for system, stats in sorted(self.stats["systems"].items()):
                if stats["total"] > 0:
                    size_str = self._format_size(stats["size"])
                    rename_info = (
                        f", renamed: {stats['renamed']}" if stats["renamed"] > 0 else ""
                    )
                    summary += (
                        f"\n  {system:15s}: {stats['copied']:4d}/{stats['total']:4d} "
                        f"(skipped: {stats['skipped']:3d}, errors: {stats['errors']:3d}{rename_info}) "
                        f"[{size_str}]"
                    )

        # If there were permission errors - show recommendations
        if self.stats["permission_errors"] > 0:
            permission_lines = [
                "\n\n",
                "=" * 60,
                "🔒 PERMISSION ERRORS",
                "=" * 60,
                "Permission issues were detected.",
                "\n💡 Recommendations:",
                "1. Run the program with administrator rights",
                "2. Check that the SD card is not write-protected",
                "3. Make sure files are not in use by other programs",
                "4. Check folder permissions (Properties -> Security)",
            ]
            summary += "\n".join(permission_lines)

            if sys.platform == "win32":
                summary += (
                    "\n\n   For Windows:\n   - Right-click on folder -> Properties\n"
                    + "   - Security tab -> Edit\n   - Add 'Everyone' with full access\n"
                    + "   - Or run Command Prompt as administrator"
                )
            else:
                summary += (
                    "\n\n   For Linux:\n   - Use: sudo python3 rom_migrator.py ...\n"
                    + "   - Or: chmod -R 777 /path/to/folder"
                )

        summary += "\n\n" + "=" * 60 + "\n💡 Source files preserved!"

        if self.dry_run:
            summary += "\n⚠️  This was a DRY RUN"

        if self.error_log:
            summary += (
                f"\n\n📄 Detailed error log saved to: "
                f"error_log_{dt.datetime.now(tz=ZoneInfo("UTC")):%Y%m%d_%H%M%S}.json"
            )

        print(summary)

    def _save_error_report(self):
        """Save error report"""
        if not self.error_log:
            return

        report_file = Path(f"error_log_{dt.datetime.now(tz=ZoneInfo("UTC")):%Y%m%d_%H%M%S}.json")
        try:
            with open(report_file, "w", encoding="utf-8") as f:
                json.dump(
                    {
                        "timestamp": dt.datetime.now(tz=ZoneInfo("UTC")).isoformat(),
                        "total_errors": len(self.error_log),
                        "errors": self.error_log,
                    },
                    f,
                    indent=2,
                    ensure_ascii=False,
                )
            print(f"📄 Error report: {report_file}")
        except Exception as e:
            print(f"Something went wrong while saving report: {e}")


def check_admin_rights():
    """Check administrator rights"""
    try:
        if sys.platform == "win32":
            import ctypes

            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        else:
            return os.geteuid() == 0
    except Exception as e:
        print(f"Something went wrong while checking permissions: {e}")
        return False


def get_user_input(prompt: str, default: str = "", is_path: bool = False) -> str:
    """
    Get user input with optional default value and path validation.

    Args:
        prompt (str): The prompt to show to the user
        default (str): Default value (optional)
        is_path (bool): If True, validates that the path exists

    Returns:
        str: User input string
    """
    while True:
        if default:
            user_input = input(f"{prompt} [{default}]: ").strip()
            if not user_input:
                user_input = default
        else:
            user_input = input(f"{prompt}: ").strip()

        if not user_input:
            print("   ⚠️  Input cannot be empty. Please try again.\n")
            continue

        if is_path:
            path = Path(user_input)
            if not path.exists():
                print(
                    f"   ⚠️  Path does not exist: {user_input}\n   Please enter a valid path.\n"
                )
                continue

        return user_input


def interactive_mode():
    """Run in interactive mode with user prompts."""
    lines = [
        "=" * 60,
        "🎮 ROM Migrator - Interactive Mode",
        "=" * 60,
        "",
        "This tool will copy ROM files from Anbernic to Knulli/Batocera.",
        "Source files will NOT be deleted.",
        "",
    ]
    print("\n".join(lines))

    # Get source path
    print(
        "📍 Step 1: Select source folder (Anbernic ROMS)\n   Example: C:/Anbernic/ROMS or /media/user/Anbernic/ROMS\n"
    )

    source = get_user_input("Enter source folder path", is_path=True)

    # Get destination path
    print(
        "\n📍 Step 2: Select destination folder (Knulli ROMS)\n   Example: E:/storage/roms or /media/user/Knulli/storage/roms\n"
    )

    dest = get_user_input("Enter destination folder path", is_path=False)

    # Check if destination folder exists, if not - ask to create
    dest_path = Path(dest)
    if not dest_path.exists():
        print(f"\n⚠️  Destination folder does not exist: {dest}")
        create = input("Create it? (y/N): ").lower()
        if create == "y":
            try:
                dest_path.mkdir(parents=True, exist_ok=True)
                print(f"✅ Folder created: {dest}")
            except Exception as e:
                print(f"❌ Failed to create folder: {e}")
                sys.exit(1)
        else:
            print("❌ Operation cancelled")
            sys.exit(1)

    # Get options
    print("\n⚙️  Step 3: Select options\n")

    dry_run = input("Dry run (preview only, no copying)? (y/N): ").lower() == "y"

    if not dry_run:
        verbose = input("Verbose output (show every file)? (y/N): ").lower() == "y"
    else:
        verbose = True  # Always show details in dry run

    # Show summary
    lines = [
        "",
        "=" * 60,
        "📋 MIGRATION SUMMARY",
        "=" * 60,
        f"📂 Source:      {source}",
        f"📂 Destination: {dest}",
        f"💾 Mode:        {'DRY RUN (no changes)' if dry_run else 'REAL (will copy files)'}",
        f"📝 Verbose:     {'YES' if verbose else 'NO'}",
        "=" * 60,
        "",
    ]
    print("\n".join(lines))

    confirm = input("Proceed with migration? (y/N): ").lower()
    if confirm != "y":
        print("❌ Operation cancelled")
        sys.exit(0)

    print("\n" + "=" * 60 + "\n🚀 Starting migration...\n" + "=" * 60 + "\n")

    # Create migrator and run
    try:
        migrator = ROMMigrator(source, dest, dry_run, verbose)
        success = migrator.run()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        if verbose:
            print("\n" + traceback.format_exc())
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Copy ROM files from Anbernic to Knulli/Batocera",
        epilog="Example: python rom_migrator.py -s D:/Anbernic/ROMS -d E:/storage/roms",
    )
    parser.add_argument("-s", "--source", help="ROM folder (Anbernic)")
    parser.add_argument("-d", "--dest", help="Destination folder (Knulli/Batocera)")
    parser.add_argument(
        "--dry-run", action="store_true", help="Dry run without copying"
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    parser.add_argument(
        "-i",
        "--interactive",
        action="store_true",
        help="Interactive mode (prompts for input)",
    )

    args = parser.parse_args()

    # If no arguments provided or interactive flag is set, run interactive mode
    if args.interactive or (not args.source and not args.dest):
        interactive_mode()
        return

    # Command line mode
    if not args.source or not args.dest:
        print(
            "❌ Error: Both --source and --dest are required in command line mode\n   Use -i or --interactive for interactive mode\n   Or provide both -s and -d parameters"
        )
        sys.exit(1)

    # Check administrator rights (just warning)
    if not check_admin_rights():
        print(
            "⚠️  Program is running without administrator rights\n   Some operations may fail\n   It is recommended to run with administrator privileges\n"
        )

    try:
        migrator = ROMMigrator(args.source, args.dest, args.dry_run, args.verbose)
        success = migrator.run()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user\n💡 Source files are intact")
        sys.exit(1)
    except PermissionError as e:
        print(
            f"\n🚫 Permission error: {e}\n\n💡 Recommendations:\n1. Run the program with administrator rights\n2. Check folder permissions\n3. Make sure the disk is not write-protected"
        )
        sys.exit(1)
    except Exception as e:
        print(f"\n🚫 Error: {e}")
        if args.verbose:
            print("\n" + traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    main()
