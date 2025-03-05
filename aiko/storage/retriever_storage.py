import numpy as np
from dataclasses import dataclass
from abc import ABC, abstractmethod
import uuid
import os

    
@dataclass
class TagEntry:
    """
    A tag entry in the graph database.
    """
    name: str
    occurences: int = 1
    
@dataclass
class GraphDBQueryResult:
    """
    A result from a graph database query.
    """
    
    doc_id: str
    tags: list[TagEntry]
    score: float



class GraphDB(ABC):
    """
    A graph database for storing document ids and tags in their relationship.
    """
    
    def __init__(self, path: str):
        self.path = path
        if path and not os.path.exists(path):
            os.makedirs(path)
         
    @abstractmethod   
    def get_total_tags(self) -> int:
        """
        Get the total number of tags in the graph database.
        
        Returns
        -------
        int
            The total number of tags.
        """
        pass
        
    @abstractmethod
    def get_unique_tags(self) -> int:
        """
        Get the number of unique tags in the graph database.
        
        Returns
        -------
        int
            The number of unique tags.
        """
        pass
    
    def calculate_score(self, tags: list[TagEntry], query_tags: list[str]) -> float:
        """
        Calculate the score of a document based on its tags and the query tags.
        
        Parameters
        ----------
        tags : list[TagEntry]
            The tags of the document.
        query_tags : list[str]
            The query tags.
        
        Returns
        -------
        float
            The score of the document.
        """
        # calculate a score between 0 and 1 based on the tags of the document and the query tags
        query_entries = self.get_tag_entries(query_tags)
        query_entries = list(filter(lambda x: x is not None, query_entries))
        
        # give more importance to query tags that are rarer in the db
        occurances = np.array([entry.occurences for entry in query_entries])
        total_occurences = np.sum(occurances)
        
        QUERY_FREQ_IMPORTANCE_SCALING = 1.0
        
        # if 0, then all tags are equally important, if higher, then rarer tags are more important, if lower, then more common tags are more important
        
        query_freq_importance = np.exp(-QUERY_FREQ_IMPORTANCE_SCALING * occurances / total_occurences)
        
        # normalize the query freq importance
        query_freq_importance = query_freq_importance / np.max(query_freq_importance)
        
        
        
        # if a tag occurs multiple times in a document, it should be more important
        # as that probably means its not only mentioned once but rather an important part of the document
        
        # TODO: consider some sort of outlier removal here
        # for example, if some useless tag is mentioned 100 times, it drags the score of relevant tags down
        # maybe also include document length in the calculation (although it indirectly is included with total_occurences, which should be higher for longer documents)
        
        # TODO: this score could be pre-calculated and stored in the db, so it doesn't have to be calculated every time
        # However, then we couldn't change the importance of tags without recalculating the scores
        DOC_FREQ_IMPORTANCE_SCALING = 1.0
        
        doc_occurances = np.array([entry.occurences for entry in tags])
        total_occurences = np.sum(doc_occurances)
        
        # basically opposite of query freq importance, since now multiple occurances are better
        doc_freq_importance = np.exp(DOC_FREQ_IMPORTANCE_SCALING * doc_occurances / total_occurences)
        doc_freq_importance = doc_freq_importance / np.max(doc_freq_importance)
        
        # calculate the score
        score = 0.0
        for query_entry in query_entries:
            for tag_entry in tags:
                if query_entry.name == tag_entry.name:
                    # TODO: consider some sort of weighting here, eg the importance of the query tag is more important than the focus of the document (or other way around)
                    score += query_freq_importance[query_entries.index(query_entry)] * doc_freq_importance[tags.index(tag_entry)]
                    break
        
        score = score / len(query_entries)
        
        # TODO: consider additional influences on score, such as:
        # - document date / recency
        # - last access or access frequency (think memory in brain where more accessed memories are more important/better remembered)
        #   something to consider: are less used memories forgotten because it improves the overall memory or are they forgotten because of capacity limitations?
        #                          if the latter, we wouldn't have to worry about it (probably), but if the former, we should consider it
        #   possible approach:
        #   - store total accesses in db
        #   - store document access times in db
        #   - store n_accesses when document was added (so that we can calculate frequency without favoring older documents)
        #   - other option: some kind of decay system, so that the most recent accesses are more important than older ones
        #   - if below a threshold, the document is forgotten (or at least not considered in the query)
        # - document type / source (eg scientific paper vs blog post)
        #   a scientific paper might be more important than a blog post, but a blog post might be more important than a random forum post
        #   it could stand for the quality or reliability of the source (but depends on the query, eg for a personal question, a forum post might be more relevant)
        # (most of these things should probably better be handled independently of GraphDB)
        
        return score
        

    @abstractmethod
    def save(self):
        """
        Save the graph database to disk.
        """
        pass

    @abstractmethod
    def load(self):
        """
        Load the graph database from disk.
        """
        pass
    
    @abstractmethod
    def insert(self, doc_id: str, tags: list[str]):
        """
        Insert a document id and its tags into the graph database.
        
        Parameters
        ----------
        doc_id : str
            The document id.
        tags : list[str]
            The tags associated with the document id.
        """
        pass
    
    @abstractmethod
    def delete(self, doc_id: str) -> bool:
        """
        Delete a document id from the graph database.
        
        Parameters
        ----------
        doc_id : str
            The document id to delete.
        
        Returns
        -------
        bool
            True if the document id was deleted, False otherwise.
        """
        pass
    
    @abstractmethod
    def query(self, tags: list[str]) -> list[GraphDBQueryResult]:
        """
        Query the graph database for document ids that have the given tags.
        
        Parameters
        ----------
        tags : list[str]
            The tags to query for.
        
        Returns
        -------
        list[GraphDBQueryResult]
            A list of query results.
        """
        pass
    
    @abstractmethod
    def get_tag_entries(self, tags: list[str]) -> list[TagEntry|None]:
        """
        Get the tag entries for the given tags.
        
        Parameters
        ----------
        tags : list[str]
            The tags to get the tag entries for.
        
        Returns
        -------
        list[TagEntry]
            The tag entries for the given tags.
        """
        pass
    
    @abstractmethod
    def get_tags(self, doc_id: str) -> list[str]:
        """
        Get the tags associated with a document id.
        
        Parameters
        ----------
        doc_id : str
            The document id.
        
        Returns
        -------
        list[str]
            The tags associated with the document id.
        """
        pass

@dataclass
class VectorDBQueryResult:
    """
    A result from a vector database query.
    """
    
    vector: np.ndarray
    key: str
    score: float
    

class VectorDB(ABC):
    """
    A database for storing vectors and querying them,
    returning the most similar vectors and their """
    
    def __init__(self, path: str, dimension: int, metric: str="cosine"):
        self.path = path
        if path and not os.path.exists(path):
            os.makedirs(path)
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
    def insert(self, key: str, vector: np.ndarray):
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
    def query(self, vector: np.array, top_k: int=1) -> list[VectorDBQueryResult]:
        """
        Query the database for the most similar vectors to the given vector.
        
        Parameters
        ----------
        vector : np.array
            The vector to query for.
        top_k : int
            The number of most similar vectors to return.
            Default is 1.
        
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
        if path and not os.path.exists(path):
            os.makedirs(path)

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
    score: float
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
            os.makedirs(self.kvstore.path, exist_ok=True)
            self.vector_db.path = os.path.join(dir_path, "vector_db")
            os.makedirs(self.vector_db.path, exist_ok=True)
            
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
        self.vector_db.insert(key, vector)
        
    def get_domain_name(self):
        # get the domain name from the path of kv store
        # eg if path is /home/user/some_dir/kvstore, return /home/user/some_dir
        return os.path.dirname(self.kvstore.path)
        
        
        
    def query(self, vector: np.ndarray, top_k: int=1) -> list[KnowledgebaseQueryResult]:
        """
        Query the knowledge base for the most similar values to the given vector.
        
        Parameters
        ----------
        vector : np.ndarray
            The vector to query for.
        top_k : int
            The number of most similar values to return.
            Default is 1.
            
        Returns
        -------
        list[KnowledgebaseQueryResult]
            A list of query results.
        """
        
        results = self.vector_db.query(vector, top_k)
        
        query_results = []
        
        for result in results:
            key = result.key
            value = self.kvstore.get(key)
            query_results.append(KnowledgebaseQueryResult(key, value, result.vector, result.score, self.get_domain_name()))
            
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

    def __init__(self, path=None, knowledge_bases: dict[str, KnowledgeBase]=None, vector_db_factory: callable=None, kvstore_factory: callable=None, allow_create: bool=True, dimension: int=None):
        """
        Create a multi-knowledge base.
        
        Parameters
        ----------
        path : str, optional
            The path to store the knowledge bases, by default None
        knowledge_bases : dict[str, KnowledgeBase], optional
            A dict of knowledge bases, by default None
        vector_db_factory : callable, optional
            A factory function for creating vector databases, by default None
        kvstore_factory : callable, optional
            A factory function for creating key-value stores, by default None
        allow_create : bool, optional
            Whether to allow creating new knowledge bases, by default True
        """
        self.path = path
        self.vector_db_factory = vector_db_factory
        self.kvstore_factory = kvstore_factory
        self.allow_create = allow_create
        self.knowledge_bases = knowledge_bases if knowledge_bases is not None else {}
        self.dimension = dimension

        if self.path is not None:
            self.load_all_domains()
        
    def can_create(self) -> bool:
        """
        Check if new knowledge bases can be created.
        
        Returns
        -------
        bool
            True if new knowledge bases can be created, False otherwise.
        """
        return self.allow_create and self.vector_db_factory is not None and self.kvstore_factory is not None and self.path is not None
    
    def load_all_domains(self):
        """
        Load all knowledge bases from subdirectories in the path.
        """

        if self.dimension is None:
            # cannot load knowledge bases without dimension
            return

        if not os.path.exists(self.path):
            return
        
        def is_db_dir(dir):
            return os.path.isdir(dir) and os.path.exists(os.path.join(dir, "vector_db")) and os.path.exists(os.path.join(dir, "kvstore"))

        for domain in os.listdir(self.path):
            domain_path = os.path.join(self.path, domain)
            if is_db_dir(domain_path):
                vector_db = self.vector_db_factory(os.path.join(domain_path, "vector_db"), self.dimension)
                vector_db.load()
                kvstore = self.kvstore_factory(os.path.join(domain_path, "kvstore"))
                kvstore.load()
                knowledge_base = KnowledgeBase(kvstore, vector_db)
                self.add_knowledge_base(domain, knowledge_base)

                print(f"Loaded knowledge base for domain {domain}")
    
    def create_knowledge_base(self, domain: str, dimension: int, metric: str="cosine"):
        """
        Create a new knowledge base or tries to load an existing one by domain.
        
        Parameters
        ----------
        domain : str
            The domain of the knowledge base.
        dimension : int
            The dimension of the vectors.
        metric : str, optional
            The metric to use for vector similarity, by default "cosine"
        """
        if not self.can_create():
            raise Exception("Cannot create new knowledge bases")
        
        knowledge_base_path = os.path.join(self.path, domain)
        if not os.path.exists(knowledge_base_path):
            os.makedirs(knowledge_base_path)
        vector_db = self.vector_db_factory(os.path.join(knowledge_base_path, "vector_db"), dimension)
        vector_db.load()
        kvstore = self.kvstore_factory(os.path.join(knowledge_base_path, "kvstore"))
        kvstore.load()
        
        knowledge_base = KnowledgeBase(kvstore, vector_db)
        self.add_knowledge_base(domain, knowledge_base)
        
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
        self.knowledge_bases[domain].save()
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
        if not self.contains_knowledge_base(domain):
            if not self.can_create():
                raise Exception("Cannot create new knowledge bases")
            self.create_knowledge_base(domain, vector.shape[0])
        
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
                for result in results:
                    result.domain = domain
                query_results.extend(results)
        else:
            if not self.contains_knowledge_base(domain):
                if self.can_create():
                    self.create_knowledge_base(domain, vector.shape[0])
                else:
                    return []
            knowledge_base = self.knowledge_bases[domain]
            results = knowledge_base.query(vector, k)
            for result in results:
                result.domain = domain
            query_results.extend(results)
            
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