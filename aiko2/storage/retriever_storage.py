import numpy as np
from dataclasses import dataclass
from abc import ABC, abstractmethod
import uuid

@dataclass
class VectorDBQueryResult:
    """
    A result from a vector database query.
    """
    
    vector: np.ndarray
    key: str
    distance: float
    

class VectorDB(ABC):
    """
    A database for storing vectors and querying them,
    returning the most similar vectors and their """
    
    def __init__(self, path: str, dimension: int, metric: str="cosine"):
        self.path = path
        self.dimension = dimension
        self.metric = metric

    @abstractmethod
    def save(self):
        """
        Save the vector database to disk.
        """
        pass

    @abstractmethod
    def load(self):
        """
        Load the vector database from disk.
        """
        pass
    
    @abstractmethod
    def insert(self, vector: np.ndarray, key: str):
        """
        Insert a vector into the database.
        
        Parameters
        ----------
        vector : np.ndarray
            The vector to insert.
        key : str
            The key for the K-V store.
        """
        
        pass
    
    @abstractmethod
    def delete(self, key: str) -> bool:
        """
        Delete a vector from the database.
        
        Parameters
        ----------
        key : str
            The key to delete.
        
        Returns
        -------
        bool
            True if the key was deleted, False otherwise.
        """
        pass
    
    @abstractmethod
    def query(self, vector: np.array, k: int) -> list[VectorDBQueryResult]:
        """
        Query the database for the most similar vectors to the given vector.
        
        Parameters
        ----------
        vector : np.array
            The vector to query for.
        k : int
            The number of most similar vectors to return.
        
        Returns
        -------
        list[VectorDBQueryResult]
            A list of query results.
        """
        pass
    

class KVStore(ABC):
    """
    A key-value store for storing data.
    """
    
    def __init__(self, path: str):
        self.path = path

    @abstractmethod
    def save(self):
        """
        Save the key-value store to disk.
        """
        pass

    @abstractmethod
    def load(self):
        """
        Load the key-value store from disk.
        """
        pass
    
    @abstractmethod
    def set(self, key: str, value: dict):
        """
        Set a value in the key-value store.
        
        Parameters
        ----------
        key : str
            The key to set.
        value : dict
            The value to set.
        """
        pass
    
    @abstractmethod
    def get(self, key: str) -> dict:
        """
        Get a value from the key-value store.
        
        Parameters
        ----------
        key : str
            The key to get.
        
        Returns
        -------
        dict
            The value associated with the key.
        """
        pass
    
    @abstractmethod
    def delete(self, key: str) -> bool:
        """
        Delete a value from the key-value store.
        
        Parameters
        ----------
        key : str
            The key to delete.
        
        Returns
        -------
        bool
            True if the key was deleted, False otherwise.
        """
        pass
        
    
    @abstractmethod
    def __contains__(self, key: str) -> bool:
        """
        Check if a key is in the key-value store.
        
        Parameters
        ----------
        key : str
            The key to check.
        
        Returns
        -------
        bool
            True if the key is in the store, False otherwise.
        """
        pass

@dataclass
class KnowledgebaseQueryResult:
    """
    A result from a knowledge base query.
    """
    
    key: str
    value: dict
    vector: np.ndarray
    distance: float
    domain: str | None = None

import os
class KnowledgeBase:
    """
    A knowledge base for storing and retrieving information.
    Internally, it uses a key-value store to store the information and a vector database
    to index and query the information.
    """
    
    def __init__(self, kvstore: KVStore, vector_db: VectorDB, path: str=None):
        self.kvstore = kvstore
        self.vector_db = vector_db
        
        if path is not None:
            dir_path = os.path.dirname(path)
            self.kvstore.path = os.path.join(dir_path, "kvstore")
            self.vector_db.path = os.path.join(dir_path, "vector_db")
            
    def save(self):
        """
        Save the knowledge base to disk.
        """
        self.kvstore.save()
        self.vector_db.save()
        
    def load(self):
        """
        Load the knowledge base from disk.
        """
        self.kvstore.load()
        self.vector_db.load()
        
    def _generate_key(self) -> str:
        """
        Generate a random key.
        
        Returns
        -------
        str
            A random key.
        """
        return str(uuid.uuid4())
        
    def insert(self, value: dict, vector: np.ndarray, key: str = None):
        """
        Insert a key-value pair into the knowledge base.
        
        Parameters
        ----------
        value : dict
            The value to insert.
        vector : np.ndarray
            The vector associated with the value.
        key : str, optional
            The key to insert, by default None
            If None, a random key will be generated.
        """
        if key is None:
            key = self._generate_key()
        
        self.kvstore.set(key, value)
        self.vector_db.insert(vector, {"key": key})
        
    def query(self, vector: np.ndarray, k: int) -> list[KnowledgebaseQueryResult]:
        """
        Query the knowledge base for the most similar values to the given vector.
        
        Parameters
        ----------
        vector : np.ndarray
            The vector to query for.
        k : int
            The number of most similar values to return.
            
        Returns
        -------
        list[KnowledgebaseQueryResult]
            A list of query results.
        """
        
        results = self.vector_db.query(vector, k)
        
        query_results = []
        
        for result in results:
            key = result.data["key"]
            value = self.kvstore.get(key)
            query_results.append(KnowledgebaseQueryResult(key, value, result.vector, result.distance))
            
        return query_results
    
    def delete(self, key: str) -> bool:
        """
        Delete a value from the knowledge base.
        
        Parameters
        ----------
        key : str
            The key to delete.
        
        Returns
        -------
        bool
            True if the key was deleted, False otherwise.
        """
        if key in self.kvstore:
            self.kvstore.delete(key)
            self.vector_db.delete(key)
            return True
        else:
            return False
        
    def __contains__(self, key: str) -> bool:
        """
        Check if a key is in the knowledge base.
        
        Parameters
        ----------
        key : str
            The key to check.
        
        Returns
        -------
        bool
            True if the key is in the knowledge base, False otherwise.
        """
        return key in self.kvstore
    
    def __getitem__(self, key: str) -> dict:
        """
        Get a value from the knowledge base.
        Directly get the value from the key-value store.
        
        Parameters
        ----------
        key : str
            The key to get.
        
        Returns
        -------
        dict
            The value associated with the key.
        """
        return self.kvstore.get(key)
        

class MultiKnowledgeBase:
    """
    A multi-knowledge base for storing and retrieving information.
    It contains multiple knowledge bases, each with its own domain.
    The knowledge bases are stored in a dict and can be accessed by their domain name,
    or all knowledge bases can be queried at once.
    """

    def __init__(self, knowledge_bases: dict[str, KnowledgeBase]=None):
        self.knowledge_bases = knowledge_bases if knowledge_bases is not None else {}
        
    def add_knowledge_base(self, domain: str, knowledge_base: KnowledgeBase):
        """
        Add a knowledge base to the multi-knowledge base.
        
        Parameters
        ----------
        domain : str
            The domain of the knowledge base.
        knowledge_base : KnowledgeBase
            The knowledge base to add.
        """
        self.knowledge_bases[domain] = knowledge_base

    def remove_knowledge_base(self, domain: str):
        """
        Remove a knowledge base from the multi-knowledge base.
        
        Parameters
        ----------
        domain : str
            The domain of the knowledge base to remove.
        """
        del self.knowledge_bases[domain]

    def contains_knowledge_base(self, domain: str) -> bool:
        """
        Check if a knowledge base is in the multi-knowledge base.
        
        Parameters
        ----------
        domain : str
            The domain of the knowledge base to check.
        
        Returns
        -------
        bool
            True if the knowledge base is in the multi-knowledge base, False otherwise.
        """
        return domain in self.knowledge_bases
        
    def save(self):
        """
        Save the multi-knowledge base to disk.
        """
        for _, knowledge_base in self.knowledge_bases.items():
            knowledge_base.save()
            
    def load(self):
        """
        Load the multi-knowledge base from disk.
        """
        for _, knowledge_base in self.knowledge_bases.items():
            knowledge_base.load()
        
    def insert(self, domain: str, value: dict, vector: np.ndarray, key: str = None):
        """
        Insert a key-value pair into the knowledge base for a specific domain.
        
        Parameters
        ----------
        domain : str
            The domain of the knowledge base.
        value : dict
            The value to insert.
        vector : np.ndarray
            The vector associated with the value.
        key : str, optional
            The key to insert, by default None
            If None, a random key will be generated.
        """
        knowledge_base = self.knowledge_bases[domain]
        knowledge_base.insert(value, vector, key)
        
    def query(self, vector: np.ndarray, k: int, domain: str = None) -> list[KnowledgebaseQueryResult]:
        """
        Query the multi-knowledge base for the most similar values to the given vector.
        
        Parameters
        ----------
        vector : np.ndarray
            The vector to query for.
        k : int
            The number of most similar values to return.
        domain : str, optional
            The domain to query, by default None
            If None, all knowledge bases will be queried.
            
        Returns
        -------
        list[KnowledgebaseQueryResult]
            A list of query results.
        """
        query_results = []
        
        if domain is None:
            for domain, knowledge_base in self.knowledge_bases.items():
                results = knowledge_base.query(vector, k)
                query_results.extend(results)
        else:
            knowledge_base = self.knowledge_bases[domain]
            query_results = knowledge_base.query(vector, k)
            
        return query_results
        
    
    def delete(self, domain: str, key: str) -> bool:
        """
        Delete a value from the knowledge base for a specific domain.
        
        Parameters
        ----------
        domain : str
            The domain of the knowledge base.
        key : str
            The key to delete.

        Returns
        -------
        bool
            True if the key was deleted, False otherwise.
        """

        knowledge_base = self.knowledge_bases[domain]
        return knowledge_base.delete(key)
    
    def __contains__(self, domain: str, key: str) -> bool:
        """
        Check if a key is in the knowledge base for a specific domain.
        
        Parameters
        ----------
        domain : str
            The domain of the knowledge base.
        key : str
            The key to check.
        
        Returns
        -------
        bool
            True if the key is in the knowledge base, False otherwise.
        """
        knowledge_base = self.knowledge_bases[domain]
        return key in knowledge_base