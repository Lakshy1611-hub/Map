import sqlite3
from pathlib import Path
class MemoryStore:
    def __init__(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True); self.path=path
        with sqlite3.connect(path) as c: c.execute("CREATE TABLE IF NOT EXISTS preferences (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
    def set(self,key,value):
        with sqlite3.connect(self.path) as c: c.execute("INSERT OR REPLACE INTO preferences VALUES (?, ?)",(key,value))
    def get(self,key):
        with sqlite3.connect(self.path) as c:
            row=c.execute("SELECT value FROM preferences WHERE key=?",(key,)).fetchone(); return row[0] if row else None
    def clear(self):
        with sqlite3.connect(self.path) as c: c.execute("DELETE FROM preferences")
