import sqlite3
from pathlib import Path
import tkinter as tk
from config import DB_NAME, DB_TABLES
from utils.files import normalize_path, find_audio_files

class QueueManager:
    def __init__(self, listbox: tk.Listbox):
        self.queue = listbox
        self.db_conn = sqlite3.connect(DB_NAME)
        self.db_cursor = self.db_conn.cursor()
        self._initialize_db()

    def _initialize_db(self):
        for table_sql in DB_TABLES.values():
            self.db_cursor.execute(table_sql)
        self.db_conn.commit()

    def load_queue(self):
        self.db_cursor.execute('SELECT filepath FROM queue ORDER BY id')
        for (filepath,) in self.db_cursor.fetchall():
            if Path(filepath).exists():
                self.queue.insert(tk.END, filepath)
