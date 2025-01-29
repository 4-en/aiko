import json
from .retriever_storage import KVStore
from cachetools import LRUCache
import os

class SimpleJsonStore(KVStore):
    def __init__(self, path):
        super().__init__(path)
        self.data = {}
        self.load()

    def _get_filename(self):
        return os.path.join(self.path, 'json_store.json')

    def load(self):
        try:
            with open(self._get_filename(), 'r') as f:
                self.data = json.load(f)
        except FileNotFoundError:
            pass

    def save(self):
        with open(self._get_filename(), 'w') as f:
            json.dump(self.data, f)

    def get(self, key):
        return self.data.get(key)

    def set(self, key, value):
        self.data[key] = value
        self.save()

    def delete(self, key):
        del self.data[key]
        self.save()

    def keys(self):
        return self.data.keys()
    
    def __len__(self):
        return len(self.data)
    
    def __contains__(self, key):
        return key in self.data
    

class JsonFileStore(KVStore):
    """
    A simple key-value store that uses a multiple JSON files to store data.
    
    Each key is hashed to a file, and the value is stored in that file.
    This is useful for storing large amounts of data, as it avoids having to load
    the entire dataset into memory.
    """

    def __init__(self, path):
        super().__init__(path)
        self.cache = LRUCache(maxsize=100)
        self.keys = set()
        self._keys_name = 'keys.txt'

    def load(self):
        # load keys if they exist
        try:
            with open(os.path.join(self.path, self._keys_name), 'r') as f:
                self.keys = set(f.read().splitlines())
        except FileNotFoundError:
            pass

    def save(self):
        with open(os.path.join(self.path, self._keys_name), 'w') as f:
            f.write('\n'.join(self.keys))
    
    def get(self, key):

        if not key in self.keys:
            return None

        if key in self.cache:
            return self.cache[key]
        
        try:
            with open(self._get_filename(key), 'r') as f:
                data = json.load(f)
                self.cache[key] = data
                return data
        except FileNotFoundError:
            return None

    def set(self, key, value):
        with open(self._get_filename(key), 'w') as f:
            json.dump(value, f)
        self.keys.add(key)

        if key in self.cache:
            self.cache[key] = value

    def delete(self, key):
        self.keys.remove(key)
        try:
            del self.cache[key]
        except KeyError:
            pass
        
        try:
            os.remove(self._get_filename(key))
        except FileNotFoundError:
            pass


    def _get_filename(self, key):
        return os.path.join(self.path, key + '.json')
    
    def __len__(self):
        return len(self.keys)
    
    def keys(self):
        return self.keys
    
    def __contains__(self, key):
        return key in self.keys