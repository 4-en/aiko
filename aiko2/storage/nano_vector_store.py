# nano vector db based store

from .retriever_storage import VectorDB, VectorDBQueryResult
import numpy as np
import os

from nano_vectordb import NanoVectorDB

class NanoVectorStore(VectorDB):
    """
    A simple key-value store that uses NanoVectorDB to store data.
    """

    def __init__(self, path: str, dimension: int, metric: str="cosine"):
        super().__init__(path, dimension, metric)
        self.db = NanoVectorDB(dimension, storage_file=os.path.join(path, 'vectors.json'))

    def save(self):
        self.db.storage_file = os.path.join(self.path, 'vectors.json')
        self.db.save()

    def load(self):
        pass


    def insert(self, key: str, value: np.ndarray):
        data = [ {
            '__vector__': value,
            '__id__': key
        }]
        self.db.upsert(data)

    def delete(self, key: str):
        _get = self.db.get([key])
        if _get:
            self.db.delete([key])
            return True
        return False

    
    def __len__(self):
        return len(self.db)
    
    def __contains__(self, key):
        _get = self.db.get([key])
        if _get:
            return True
        return False
    
    def query(self, vector, k):
        nvdb_res = self.db.query(vector, k)
        if nvdb_res:
            results = []
            for res in nvdb_res:
                results.append(VectorDBQueryResult(None, res['__id__'], res["__metrics__"]))
            return results
        return []