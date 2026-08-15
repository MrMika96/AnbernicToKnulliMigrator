import os
import sys
from pathlib import Path


class PermissionErrorHandler:
    """Permission error handler."""

    @staticmethod
    def check_read_access(path: Path) -> tuple[bool, str]:
        """Check read access."""
        try:
            if not path.exists():
                return False, f"Path does not exist: {path}"

            if not os.access(str(path), os.R_OK):
                return False, f"No read permission: {path}"

            return True, "OK"
        except Exception as e:
            return False, f"Access check error: {e}"

    @staticmethod
    def check_write_access(path: Path) -> tuple[bool, str]:
        """Check write access."""
        try:
            # Check parent folder
            parent = path.parent if path.suffix else path

            if not parent.exists():
                # Try to create folder
                try:
                    parent.mkdir(parents=True, exist_ok=True)
                    return True, "Folder created"
                except PermissionError:
                    return False, f"No permission to create folder: {parent}"
                except Exception as e:
                    return False, f"Error creating folder: {e}"

            # Check write access
            if not os.access(str(parent), os.W_OK):
                return False, f"No write permission to folder: {parent}"

            # Try to create a test file
            test_file = parent / ".write_test"
            try:
                test_file.touch()
                test_file.unlink()
                return True, "OK"
            except PermissionError:
                return False, f"No write permission to folder (test failed): {parent}"
            except Exception as e:
                return False, f"Write test error: {e}"

        except Exception as e:
            return False, f"Access check error: {e}"

    @staticmethod
    def get_permission_suggestion(error_msg: str) -> str:
        """Returns suggestions for fixing permission errors."""
        suggestions = []

        if "Permission denied" in error_msg or "Access denied" in error_msg:
            suggestions.append("🔧 Run the program with administrator rights")
            suggestions.append(
                "🔧 Check folder permissions (right-click -> Properties -> Security)"
            )
            suggestions.append("🔧 Make sure files are not in use by other programs")

            if sys.platform == "win32":
                suggestions.append(
                    "🔧 For Windows: disable write protection on SD card"
                )
                suggestions.append(
                    "🔧 For Windows: check if the disk is write-protected"
                )
            else:
                suggestions.append(
                    "🔧 For Linux: use sudo or chmod to change permissions"
                )

        if "Read-only" in error_msg or "read-only" in error_msg:
            suggestions.append("🔧 Folder or disk is write-protected")
            suggestions.append(
                "🔧 For SD card: check the physical write protection switch"
            )

        if "No such file" in error_msg:
            suggestions.append("🔧 Check the path is correct")
            suggestions.append("🔧 Make sure the disk is connected")

        if not suggestions:
            suggestions.append("🔧 Check file and folder permissions")

        return "\n".join(suggestions)
