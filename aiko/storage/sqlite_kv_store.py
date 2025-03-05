import sqlite3
from .retriever_storage import KVStore
from enum import Enum
from cachetools import LRUCache

class SQLiteColumnType(Enum):
    TEXT = 'TEXT'
    INTEGER = 'INTEGER'
    REAL = 'REAL'
    BLOB = 'BLOB'

class SQLiteKVStore(KVStore):
    """
    A simple key-value store that uses SQLite to store data.
    
    This is useful for storing large amounts of data, as it avoids having to load
    the entire dataset into memory.
    
    The columns parameter is a dictionary of column names and SQLiteColumnType values."""
    def __init__(self, path: str, columns: dict[str, SQLiteColumnType]):
        self.path = path
        self.columns = columns
        self.conn = sqlite3.connect(path)
        self.cursor = self.conn.cursor()
        self.cache = LRUCache(maxsize=100)
        self.create_table()

    def create_table(self):
        column_str = ', '.join([f'{key} {value.value}' for key, value in self.columns.items()])
        self.cursor.execute(f'CREATE TABLE IF NOT EXISTS kv_store ({column_str})')
        self.conn.commit()

    def get(self, key: str):
        if key in self.cache:
            return self.cache[key]

        self.cursor.execute('SELECT * FROM kv_store WHERE key = ?', (key,))
        result = self.cursor.fetchone()
        if result is None:
            return None
        self.cache[key] = result
        return result
    
    def set(self, key: str, value: str):
        self.cursor.execute('INSERT INTO kv_store (key, value) VALUES (?, ?)', (key, value))
        self.conn.commit()

        if key in self.cache:
            self.cache[key] = value

    def delete(self, key: str):
        self.cursor.execute('DELETE FROM kv_store WHERE key = ?', (key,))
        self.conn.commit()

        try:
            del self.cache[key]
        except KeyError:
            pass

    def keys(self):
        self.cursor.execute('SELECT key FROM kv_store')
        return [row[0] for row in self.cursor.fetchall()]
    
    def __len__(self):
        self.cursor.execute('SELECT COUNT(*) FROM kv_store')
        return self.cursor.fetchone()[0]
    
    def __contains__(self, key: str):
        self.cursor.execute('SELECT COUNT(*) FROM kv_store WHERE key = ?', (key,))
        return self.cursor.fetchone()[0] > 0
    
    def __del__(self):
        self.conn.close()

    def load(self):
        pass

    def save(self):
        pass