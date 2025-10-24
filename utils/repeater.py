#!/usr/bin/env python

"""
repeater

Watches the project directory for changes and automatically reloads the
Tkinter application when any Python files are modified, respecting .gitignore.

Usage:
    python repeater [main_file]

Arguments:
    main_file: Path to the main Tkinter application file (default: main.py)

Watched paths:
    - The entire project directory recursively
    - Respects .gitignore patterns (inverse match)
    - Always watches the main file regardless of gitignore
"""

import argparse
import fnmatch
import logging
import os
import signal
import subprocess
import sys
import time
from collections import defaultdict
from decouple import config
from pathlib import Path
from threading import Lock, Timer
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer


def parse_gitignore(gitignore_path):
    """Parse .gitignore file and return list of patterns."""
    patterns = []
    if gitignore_path.exists():
        with open(gitignore_path, encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                if line.startswith('/'):
                    line = line[1:]
                patterns.append(line)
    return patterns


def should_ignore_path(file_path, gitignore_patterns, repo_root):
    """Check if a file path should be ignored based on gitignore patterns."""
    if not gitignore_patterns:
        return False

    try:
        rel_path = file_path.relative_to(repo_root)
    except ValueError:
        return False

    rel_path_str = str(rel_path)

    for pattern in gitignore_patterns:
        if pattern.endswith('/'):
            if rel_path_str.startswith(pattern[:-1] + '/'):
                return True
        elif pattern.startswith('!'):
            if fnmatch.fnmatch(rel_path_str, pattern[1:]):
                return False
        elif (
            fnmatch.fnmatch(rel_path_str, pattern)
            or pattern in rel_path_str
            or any(part.startswith(pattern.rstrip('/')) for part in rel_path.parts)
        ):
            return True

    return False


class ReloadEventHandler(FileSystemEventHandler):
    """Event handler that triggers app reload on file changes."""

    def __init__(self, main_file, repo_root, gitignore_patterns, debounce_seconds=0.5):
        self.main_file = main_file
        self.repo_root = repo_root
        self.gitignore_patterns = gitignore_patterns
        self.process = None
        self.debounce_seconds = debounce_seconds
        self.pending_reload = None
        self.reload_lock = Lock()
        self.changed_files = set()
        self.logger = logging.getLogger('repeater')
        self.start_app()

    def setup_macos_environment(self):
        """Setup TCL/TK environment variables for macOS."""
        env = os.environ.copy()

        if sys.platform == 'darwin':
            # Get TCL/TK paths from environment or use Homebrew defaults
            tcl_library = config('TCL_LIBRARY', default='/opt/homebrew/opt/tcl-tk/lib/tcl8.6')
            tk_library = config('TK_LIBRARY', default='/opt/homebrew/opt/tcl-tk/lib/tk8.6')
            tcl_tk_bin = config('TCL_TK_BIN', default='/opt/homebrew/opt/tcl-tk/bin')

            # Set TCL/TK environment variables
            env['TCL_LIBRARY'] = tcl_library
            env['TK_LIBRARY'] = tk_library

            # Prepend TCL/TK bin to PATH
            env['PATH'] = f"{tcl_tk_bin}:{env.get('PATH', '')}"

        # Enable API server by default for development (can be overridden with env var)
        api_server_enabled = config('MT_API_SERVER_ENABLED', default='true', cast=str)
        api_server_port = config('MT_API_SERVER_PORT', default='5555', cast=str)
        env['MT_API_SERVER_ENABLED'] = api_server_enabled
        env['MT_API_SERVER_PORT'] = api_server_port

        return env

    def start_app(self):
        """Start the Tkinter application."""
        print(f"Starting {self.main_file}...")
        env = self.setup_macos_environment()
        self.process = subprocess.Popen([sys.executable, str(self.main_file)], env=env)

    def should_reload(self, file_path):
        """Check if the changed file should trigger a reload."""
        if not file_path.endswith('.py'):
            return False

        path = Path(file_path)

        if path == self.main_file:
            return True

        should_watch = not should_ignore_path(path, self.gitignore_patterns, self.repo_root)
        if should_watch:
            try:
                rel_path = path.relative_to(self.repo_root)
                self.logger.debug(f"Will reload for: {rel_path}")
            except ValueError:
                pass
        return should_watch

    def schedule_reload(self, file_path):
        """Schedule a debounced reload for the changed file."""
        with self.reload_lock:
            self.changed_files.add(file_path)

            # Cancel existing reload timer
            if self.pending_reload:
                self.pending_reload.cancel()

            # Schedule new reload
            self.pending_reload = Timer(self.debounce_seconds, self._execute_reload)
            self.pending_reload.start()

    def _execute_reload(self):
        """Execute the actual reload after debounce period."""
        with self.reload_lock:
            if self.changed_files:
                files = list(self.changed_files)
                self.changed_files.clear()
                self.pending_reload = None

                # Log all changed files
                for file_path in files:
                    try:
                        rel_path = Path(file_path).relative_to(self.repo_root)
                        print(f"File changed: {rel_path}")
                    except (ValueError, Exception):
                        print(f"File changed: {file_path}")

                self.restart_app()

    def on_modified(self, event):
        """Called when a file is modified."""
        if not event.is_directory and self.should_reload(event.src_path):
            self.schedule_reload(event.src_path)

    def on_created(self, event):
        """Called when a file is created."""
        if not event.is_directory and self.should_reload(event.src_path):
            self.schedule_reload(event.src_path)

    def on_moved(self, event):
        """Called when a file is moved (common with atomic saves)."""
        # Check destination path for atomic save pattern (editors often save to .tmp then move)
        if not event.is_directory and self.should_reload(event.dest_path):
            self.schedule_reload(event.dest_path)

    def restart_app(self):
        """Restart the Tkinter application."""
        if self.process:
            print("Stopping current process...")
            self.process.send_signal(signal.SIGINT)
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                print("Process didn't terminate gracefully, killing...")
                self.process.kill()
                self.process.wait()
            self.process = None

        time.sleep(0.5)
        self.start_app()

    def cleanup(self):
        """Clean up the process and pending timers."""
        # Cancel any pending reload
        with self.reload_lock:
            if self.pending_reload:
                self.pending_reload.cancel()
                self.pending_reload = None
            self.changed_files.clear()

        # Terminate the app process
        if self.process:
            self.process.send_signal(signal.SIGINT)
            try:
                self.process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                self.process.kill()
            self.process = None


def main():
    parser = argparse.ArgumentParser(description="Simple tkinter reloader with multi-directory watching")
    parser.add_argument(
        "main_file", nargs="?", default="main.py", help="Path to the main Tkinter application file (default: main.py)"
    )
    parser.add_argument(
        "--debug", action="store_true", help="Enable debug logging to see watched files"
    )
    parser.add_argument(
        "--debounce", type=float, default=0.5, help="Debounce delay in seconds (default: 0.5)"
    )

    args = parser.parse_args()

    if not Path(args.main_file).is_absolute():
        mt_package_dir = Path(__file__).parent.parent
        main_file = (mt_package_dir / args.main_file).resolve()
    else:
        main_file = Path(args.main_file).resolve()

    if not main_file.exists():
        print(f"Error: Main file '{main_file}' not found!")
        sys.exit(1)

    project_root = main_file.parent
    gitignore_path = project_root / ".gitignore"
    gitignore_patterns = parse_gitignore(gitignore_path)

    pid_file = project_root / ".repeater.pid"
    if pid_file.exists():
        try:
            with open(pid_file) as f:
                old_pid = int(f.read().strip())
            os.kill(old_pid, 0)
            print("Another repeater instance is already running.")
            sys.exit(1)
        except (OSError, ValueError):
            pid_file.unlink(missing_ok=True)

    with open(pid_file, 'w') as f:
        f.write(str(os.getpid()))

    print("repeater")
    print("====================")
    print(f"Watching project root: {project_root}")
    print(f"Main file: {main_file}")
    print(f"Gitignore patterns loaded: {len(gitignore_patterns)}")
    print(f"Debounce delay: {args.debounce}s")
    if args.debug:
        print("Debug mode: ON")
    print("\nPress Ctrl+C to stop\n")

    log_level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(level=log_level, format='%(asctime)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

    event_handler = ReloadEventHandler(main_file, project_root, gitignore_patterns, debounce_seconds=args.debounce)

    observer = Observer()

    observer.schedule(event_handler, str(project_root), recursive=True)

    observer.start()

    try:
        while observer.is_alive():
            observer.join(1)
            # Check if the subprocess has terminated
            if event_handler.process and event_handler.process.poll() is not None:
                print("\nApplication exited, stopping reloader...")
                break
    except KeyboardInterrupt:
        print("\nStopping observer...")
    finally:
        observer.stop()
        observer.join()
        event_handler.cleanup()
        pid_file.unlink(missing_ok=True)
        print("Reloader stopped.")


if __name__ == "__main__":
    main()
