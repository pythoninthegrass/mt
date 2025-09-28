"""PyWebView native file system API bridge."""

import os
import webview
from pathlib import Path
from typing import List, Optional, Dict, Any
from eliot import log_message


class FileSystemAPI:
    """PyWebView native file system API bridge for JavaScript integration."""

    def __init__(self):
        """Initialize the file system API."""
        self._window = None

    def set_window(self, window: webview.Window):
        """Set the PyWebView window reference."""
        self._window = window

    def open_file_dialog(
        self, file_types: Optional[List[str]] = None, multiple: bool = False, title: str = "Select Files"
    ) -> List[str]:
        """
        Open native file selection dialog.

        Args:
            file_types: List of file extensions (e.g., ['mp3', 'flac', 'wav'])
            multiple: Allow multiple file selection
            title: Dialog title

        Returns:
            List of selected file paths
        """
        try:
            if not self._window:
                log_message(message_type="filesystem_error", error="PyWebView window not set")
                return []

            # Convert file types to PyWebView format
            file_filter = ()
            if file_types:
                # PyWebView expects tuple of file extensions
                file_filter = tuple(f"*.{ext}" for ext in file_types)

            # Open file dialog
            result = self._window.create_file_dialog(dialog_type=0, directory="", allow_multiple=multiple, file_types=file_filter)

            if result:
                paths = [str(Path(p).resolve()) for p in result]
                log_message(
                    message_type="file_dialog_success", file_count=len(paths), message=f"File dialog selected {len(paths)} files"
                )
                return paths
            else:
                log_message(message_type="file_dialog_cancelled", message="File dialog cancelled")
                return []

        except Exception as e:
            log_message(message_type="file_dialog_error", error=str(e), error_type=type(e).__name__)
            return []

    def open_directory_dialog(self, title: str = "Select Directory") -> Optional[str]:
        """
        Open native directory selection dialog.

        Args:
            title: Dialog title

        Returns:
            Selected directory path or None if cancelled
        """
        try:
            if not self._window:
                log_message(message_type="filesystem_error", error="PyWebView window not set")
                return None

            # Open directory dialog
            result = self._window.create_file_dialog(dialog_type=2, directory="")

            if result and len(result) > 0:
                path = str(Path(result[0]).resolve())
                log_message(message_type="directory_dialog_success", path=path, message=f"Directory dialog selected: {path}")
                return path
            else:
                log_message(message_type="directory_dialog_cancelled", message="Directory dialog cancelled")
                return None

        except Exception as e:
            log_message(message_type="directory_dialog_error", error=str(e), error_type=type(e).__name__)
            return None

    def save_file_dialog(
        self, default_filename: str = "", file_types: Optional[List[str]] = None, title: str = "Save File"
    ) -> Optional[str]:
        """
        Open native file save dialog.

        Args:
            default_filename: Default filename to suggest
            file_types: List of file extensions
            title: Dialog title

        Returns:
            Selected file path or None if cancelled
        """
        try:
            if not self._window:
                log_message(message_type="filesystem_error", error="PyWebView window not set")
                return None

            # Convert file types to PyWebView format
            file_filter = ()
            if file_types:
                file_filter = tuple(f"*.{ext}" for ext in file_types)

            # Open save dialog
            result = self._window.create_file_dialog(
                dialog_type=1, directory="", save_filename=default_filename, file_types=file_filter
            )

            if result and len(result) > 0:
                path = str(Path(result[0]).resolve())
                log_message(message_type="save_dialog_success", path=path, message=f"Save dialog selected: {path}")
                return path
            else:
                log_message(message_type="save_dialog_cancelled", message="Save dialog cancelled")
                return None

        except Exception as e:
            log_message(message_type="save_dialog_error", error=str(e), error_type=type(e).__name__)
            return None

    def validate_paths(self, paths: List[str]) -> Dict[str, Any]:
        """
        Validate file/directory paths for accessibility, existence, and security.

        Args:
            paths: List of paths to validate

        Returns:
            Dictionary with validation results
        """
        results = {"valid": [], "invalid": [], "directories": [], "files": [], "warnings": []}

        for path_str in paths:
            try:
                path = Path(path_str).resolve()  # Resolve symlinks and relative paths

                # Security checks
                security_issues = self._check_path_security(path)
                if security_issues:
                    results["invalid"].append({"path": path_str, "error": f"Security violation: {', '.join(security_issues)}"})
                    continue

                if not path.exists():
                    results["invalid"].append({"path": path_str, "error": "Path does not exist"})
                    continue

                # Check if accessible
                try:
                    stat_info = path.stat()

                    # Additional security checks on file metadata
                    if not self._is_safe_file_permissions(stat_info):
                        results["invalid"].append({"path": path_str, "error": "Unsafe file permissions"})
                        continue

                    if path.is_dir():
                        # Try to list directory contents
                        try:
                            list(path.iterdir())
                        except (OSError, PermissionError):
                            results["invalid"].append({"path": path_str, "error": "Cannot read directory contents"})
                            continue

                        results["valid"].append(path_str)
                        results["directories"].append(path_str)
                    else:
                        # For files, check if they're readable
                        if not os.access(path, os.R_OK):
                            results["invalid"].append({"path": path_str, "error": "File is not readable"})
                            continue

                        results["valid"].append(path_str)
                        results["files"].append(path_str)

                except (OSError, PermissionError) as e:
                    results["invalid"].append({"path": path_str, "error": f"Permission denied: {e}"})

            except Exception as e:
                results["invalid"].append({"path": path_str, "error": f"Invalid path: {e}"})

        log_message(
            message_type="path_validation_complete",
            valid_count=len(results['valid']),
            invalid_count=len(results['invalid']),
            warning_count=len(results['warnings']),
        )
        return results

    def _check_path_security(self, path: Path) -> List[str]:
        """
        Check for security issues with a file path.

        Args:
            path: Path to check

        Returns:
            List of security issues found
        """
        issues = []

        try:
            # Resolve the path to check for directory traversal
            resolved_path = path.resolve()
            original_path = path.absolute()

            # Check for directory traversal attacks
            if str(resolved_path) != str(original_path):
                issues.append("path traversal detected")

            # Check for suspicious path components
            parts = resolved_path.parts
            suspicious_patterns = ['..', '.', '~', '$']

            for part in parts:
                if any(pattern in part for pattern in suspicious_patterns):
                    if part not in ['.', '..']:  # Allow legitimate . and ..
                        issues.append(f"suspicious path component: {part}")

            # Check for system directories that should not be accessed
            system_paths = [
                '/System',
                '/usr',
                '/bin',
                '/sbin',
                '/private',
                '/Library/Keychains',
                '/System/Library/Keychains',
                '/private/var/db',
                '/var/root',
            ]

            path_str = str(resolved_path)
            for sys_path in system_paths:
                if path_str.startswith(sys_path):
                    issues.append(f"access to system directory: {sys_path}")

            # Check for hidden files/directories (starting with .)
            if resolved_path.name.startswith('.') and resolved_path.name != '.':
                issues.append("hidden file access")

        except Exception as e:
            issues.append(f"path resolution error: {e}")

        return issues

    def _is_safe_file_permissions(self, stat_info) -> bool:
        """
        Check if file permissions are safe for reading.

        Args:
            stat_info: File stat information

        Returns:
            True if permissions are safe
        """
        try:
            import stat

            # Check if file is world-writable (insecure)
            if stat_info.st_mode & stat.S_IWOTH:
                return False

            # Check if file is owned by root/admin (be more careful)
            if stat_info.st_uid == 0:
                return False

            # For directories, check if they're world-writable
            if stat.S_ISDIR(stat_info.st_mode) and (stat_info.st_mode & stat.S_IWOTH):
                return False

            return True

        except Exception:
            # If we can't check permissions, err on the side of caution
            return False

    def get_path_info(self, path: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a file or directory path.

        Args:
            path: Path to analyze

        Returns:
            Dictionary with path information or None if invalid
        """
        try:
            p = Path(path).resolve()

            # Security check
            security_issues = self._check_path_security(p)
            if security_issues:
                log_message(message_type="path_info_security_violation", path=path, issues=security_issues)
                return None

            if not p.exists():
                return None

            stat = p.stat()

            # Check if we have permission to access this path
            if not os.access(p, os.R_OK):
                log_message(message_type="path_info_access_denied", path=path)
                return None

            # Only expose safe information
            info = {
                "name": p.name,
                "is_file": p.is_file(),
                "is_dir": p.is_dir(),
                "size": stat.st_size,
                "modified": stat.st_mtime,
                "readable": os.access(p, os.R_OK),
                "writable": os.access(p, os.W_OK),
                "executable": os.access(p, os.X_OK),
            }

            # Don't expose full path for security
            # Don't expose detailed permissions

            # Additional file info
            if p.is_file():
                info["extension"] = p.suffix.lower()
                info["stem"] = p.stem

            # Additional directory info
            elif p.is_dir():
                try:
                    contents = list(p.iterdir())
                    info["item_count"] = len(contents)
                    info["subdirs"] = len([c for c in contents if c.is_dir()])
                    info["files"] = len([c for c in contents if c.is_file()])
                except (OSError, PermissionError):
                    info["item_count"] = 0
                    info["subdirs"] = 0
                    info["files"] = 0

            return info

        except Exception as e:
            log_message(message_type="path_info_error", path=path, error=str(e), error_type=type(e).__name__)
            return None

    def list_directory(self, path: str, recursive: bool = False, max_depth: int = 3) -> Dict[str, Any]:
        """
        List contents of a directory with optional recursion and security checks.

        Args:
            path: Directory path to list
            recursive: Whether to list subdirectories recursively
            max_depth: Maximum recursion depth

        Returns:
            Dictionary with directory listing results
        """
        try:
            p = Path(path).resolve()

            # Security check
            security_issues = self._check_path_security(p)
            if security_issues:
                log_message(message_type="directory_list_security_violation", path=path, issues=security_issues)
                return {"success": False, "error": f"Security violation: {', '.join(security_issues)}", "contents": []}

            if not p.exists() or not p.is_dir():
                return {"success": False, "error": "Path is not a valid directory", "contents": []}

            # Check directory access
            if not os.access(p, os.R_OK):
                return {"success": False, "error": "Directory is not readable", "contents": []}

            contents = []

            def _list_dir(current_path: Path, current_depth: int = 0):
                if current_depth > max_depth:
                    return

                try:
                    # Security check for each subdirectory
                    if current_depth > 0:
                        sub_security_issues = self._check_path_security(current_path)
                        if sub_security_issues:
                            log_message(
                                message_type="directory_list_subdirectory_security_violation",
                                path=str(current_path),
                                issues=sub_security_issues,
                            )
                            return

                    items = list(current_path.iterdir())
                    for item in sorted(items):
                        # Security check for each item
                        item_security_issues = self._check_path_security(item)
                        if item_security_issues:
                            # Skip insecure items but don't fail the whole operation
                            continue

                        try:
                            stat_info = item.stat()
                            if not self._is_safe_file_permissions(stat_info):
                                # Skip files with unsafe permissions
                                continue

                            item_info = {
                                "name": item.name,
                                "is_file": item.is_file(),
                                "is_dir": item.is_dir(),
                                "size": stat_info.st_size if item.is_file() else 0,
                                "modified": stat_info.st_mtime,
                                "depth": current_depth,
                                "readable": os.access(item, os.R_OK),
                            }
                            contents.append(item_info)

                            if recursive and item.is_dir() and current_depth < max_depth:
                                _list_dir(item, current_depth + 1)

                        except (OSError, PermissionError):
                            # Skip items we can't access
                            continue

                except (OSError, PermissionError) as e:
                    log_message(message_type="directory_list_warning", path=str(current_path), error=str(e))

            _list_dir(p)

            return {"success": True, "contents": contents, "total_items": len(contents)}

        except Exception as e:
            log_message(message_type="directory_list_error", path=path, error=str(e), error_type=type(e).__name__)
            return {"success": False, "error": str(e), "contents": []}


# Global instance for use across the application
filesystem_api = FileSystemAPI()
