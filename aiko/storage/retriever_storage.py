import numpy as np
from dataclasses import dataclass
from abc import ABC, abstractmethod
import uuid
import os
from aiko.core import Memory
import math
    
@dataclass
class TagEntry:
    """
    A tag entry in the graph database.
    """
    id: str
    name: str
    occurences: int = 1
    
@dataclass
class GraphDBQueryResult:
    """
    A result from a graph database query.
    """
    id: str
    memory: Memory
    score: float

    def positive_feedback(self, query: str):
        # TODO: implement positive feedback
        pass

TIME_DECAY_WEIGHT = 0.5
BOOST_FACTOR = 0.5

@dataclass
class MemoryNode:
    """
    A node in the memory graph, containing the memory and metadata.
    """
    memory: Memory
    creation: int = 0
    last_access: int = 0
    total_access: int = 0
    access_score: float = 0.5

    def to_dict(self):
        return {
            "memory": self.memory.to_dict(),
            "creation": self.creation,
            "last_access": self.last_access,
            "total_access": self.total_access,
            "access_score": self.access_score
        }
    
    @staticmethod
    def from_dict(data):
        memory = Memory.from_dict(data["memory"])
        creation = data["creation"]
        last_access = data["last_access"]
        total_access = data["total_access"]
        access_score = data["access_score"]
        return MemoryNode(memory, creation, last_access, total_access, access_score)
    
    def get_access_score(self, current_time: int) -> float:
        # TODO: fix this
        # scoring system is not working as intended, fix later
        global_time_ratio = self.last_access / (current_time+1)
        creation_time_ratio = ( self.last_access - self.creation ) / (current_time - self.creation + 1)

        weighted_time_ratio = 0.5 * global_time_ratio + 0.5 * creation_time_ratio

        # factor in total access count
        # if last access was very recent (ie wtr is close to 1), then the total access count should not have much influence
        # total_influence = 1 - weighted_time_ratio ** 2
        # total_influence = max(0.0, total_influence)

        weighted_time_ratio = 1 - weighted_time_ratio


        return (1-TIME_DECAY_WEIGHT) * self.access_score + TIME_DECAY_WEIGHT * ((math.exp(-weighted_time_ratio))) * self.access_score
        
    
    def update_access(self, current_time: int):
        global_time_ratio = self.last_access / (current_time+1)
        creation_time_ratio = ( self.last_access - self.creation ) / (current_time - self.creation + 1)

        weighted_time_ratio = 0.5 * global_time_ratio + 0.5 * creation_time_ratio

        self.access_score = (1-TIME_DECAY_WEIGHT) * self.access_score + TIME_DECAY_WEIGHT * ((math.exp(-weighted_time_ratio))) * self.access_score
        
        # boost the access score since it was accessed
        self.access_score += (1 - self.access_score) * BOOST_FACTOR
        
        self.last_access = current_time
        self.total_access += 1


@dataclass
class GraphDBNode:
    """
    A node in the graph database.
    """
    
    label: str
    properties: dict
    node_id: str = None

@dataclass
class GraphDBRelationship:
    """
    A relationship in the graph database.
    """
    
    start_id: str
    rel_type: str
    end_id: str
    properties: dict
    bidirectional: bool = False
    rel_id: str = None


class GraphMemory(ABC):
    """
    A graph database for storing objects and their relationships,
    with a scoring system for ranking results based on tags, frequency, and other factors.
    """

    # TODO: IDEA:
    # - add a way to provide feedback on the results of a query, so that good results can be promoted and bad results can be demoted
    # - this could be done by also storing queries along with good/bad results
    # - the feedback could be used to adjust the scoring system, so that good results are more likely to be returned in the future
    
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

    @abstractmethod
    def create_node(self, label, properties=None, node_id=None) -> GraphDBNode:
        """
        Create a node in the graph database.

        Parameters
        ----------
        label : str
            The label of the node.
        properties : dict, optional
            The properties of the node, by default None
        node_id : str, optional
            The id of the node, by default None
            If None, a random id will be generated.

        Returns
        -------
        GraphDBNode
            The created node.
        """
        pass

    @abstractmethod
    def create_relationship(self, start_id, rel_type, end_id, properties=None, bidirectional=False, rel_id=None) -> GraphDBRelationship:
        """
        Create a relationship in the graph database.

        Parameters
        ----------
        start_id : str
            The id of the start node.
        rel_type : str
            The type of the relationship.
        end_id : str
            The id of the end node.
        properties : dict, optional
            The properties of the relationship, by default None
        bidirectional : bool, optional
            Whether the relationship is bidirectional, by default False
        rel_id : str, optional
            The id of the relationship, by default None
            If None, a random id will be generated.

        Returns
        -------
        GraphDBRelationship
            The created relationship.
        """
        pass

    @abstractmethod
    def match_nodes(self, label=None, **property_filter) -> list[GraphDBNode]:
        """
        Match nodes in the graph database.

        Parameters
        ----------
        label : str, optional
            The label of the nodes to match, by default None
        property_filter : dict
            The properties to filter the nodes by.
            A dict with the property name as key and the property value as value.
            Filters out nodes that don't have the property or have a different value.

        Returns
        -------
        list[GraphDBNode]
            A list of nodes that match the filter.
        """
        pass

    @abstractmethod
    def match_relationships(self, rel_type=None, property_filter=None) -> list[GraphDBRelationship]:
        """
        Match relationships in the graph database.

        Parameters
        ----------
        rel_type : str, optional
            The type of the relationships to match, by default None
        property_filter : dict, optional
            The properties to filter the relationships by, by default None
            A dict with the property name as key and the property value as value.
            Filters out relationships that don't have the property or have a different value.

        Returns
        -------
        list[GraphDBRelationship]
            A list of relationships that match the filter.
        """
        pass

    @abstractmethod
    def get_relationships_for_node(self, node_id, rel_type=None, direction='both') -> list[GraphDBRelationship]:
        """
        Get relationships for a node in the graph database.

        Parameters
        ----------
        node_id : str
            The id of the node.
        rel_type : str, optional
            The type of the relationships to get, by default None
        direction : str, optional
            The direction of the relationships to get, by default 'both'
            Can be 'both', 'in', or 'out'.

        Returns
        -------
        list[GraphDBRelationship]
            A list of relationships for the node.
        """
        pass

    @abstractmethod
    def update_node(self, node_id, properties):
        """
        Update a node in the graph database.

        Parameters
        ----------
        node_id : str
            The id of the node.
        properties : dict
            The properties to update.
        """
        pass

    @abstractmethod
    def update_relationship(self, rel_id, properties):
        """
        Update a relationship in the graph database.

        Parameters
        ----------
        rel_id : str
            The id of the relationship.
        properties : dict
            The properties to update.
        """
        pass

    @abstractmethod
    def delete_node(self, node_id) -> GraphDBNode:
        """
        Delete a node from the graph database.

        Parameters
        ----------
        node_id : str
            The id of the node.

        Returns
        -------
        GraphDBNode
            The deleted node.
        """
        pass

    @abstractmethod
    def delete_relationship(self, rel_id) -> GraphDBRelationship:
        """
        Delete a relationship from the graph database.

        Parameters
        ----------
        rel_id : str
            The id of the relationship.

        Returns
        -------
        GraphDBRelationship
            The deleted relationship.
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