import importlib
import os
import sys
import time
from pathlib import Path
from watchdog.events import FileSystemEventHandler


class ConfigFileHandler(FileSystemEventHandler):
    def __init__(self, app_instance):
        self.app_instance = app_instance
        self.last_reload_time = 0
        self.reload_cooldown = 1.0  # seconds
        self.watched_files = {p.name for p in Path('.').glob('**/*.py') if '.venv' not in str(p) and len(p.parents) <= 2}
        self.watched_files.add('themes.json')

    def on_modified(self, event):
        if not self.app_instance.reload_enabled or event.is_directory:
            return

        current_time = time.time()
        if current_time - self.last_reload_time < self.reload_cooldown:
            return

        file_path = event.src_path
        file_name = os.path.basename(file_path)

        if file_name in self.watched_files:
            print(f"Detected change in {file_name}, reloading configuration...")
            self.last_reload_time = current_time

            try:
                if file_name == 'main.py':
                    # For main.py changes, we need to restart the entire process
                    if self.app_instance and self.app_instance.window:
                        self.app_instance.window.after(100, self.restart_process)
                else:
                    # For other files, reload config and restart window
                    if 'config' in sys.modules:
                        importlib.reload(sys.modules['config'])
                    if self.app_instance and self.app_instance.window:
                        self.app_instance.window.after(100, self.restart_application)
            except Exception as e:
                print(f"Error reloading configuration: {e}")

    def restart_process(self):
        """Restart the entire Python process"""
        try:
            if self.app_instance and self.app_instance.window:
                self.app_instance.window.destroy()
            python = sys.executable
            os.execl(python, python, *sys.argv)
        except Exception as e:
            print(f"Error restarting process: {e}")
            sys.exit(1)

    def restart_application(self):
        """Restart just the application window"""
        try:
            if self.app_instance and self.app_instance.window:
                self.app_instance.window.destroy()
                from main import main

                main()
        except Exception as e:
            print(f"Error restarting application: {e}")
            sys.exit(1)
