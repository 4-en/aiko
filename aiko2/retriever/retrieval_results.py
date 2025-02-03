from dataclasses import dataclass, field
import sentence_transformers
import numpy as np
import rank_bm25
from uuid import uuid4
from aiko2.utils import split_text, chunk_text
from enum import Enum

class QueryType(Enum):
    GENERAL = 'GENERAL'
    PERSONAL = 'PERSONAL'
    NEWS = 'NEWS'
    RESEARCH = 'RESEARCH'
    OTHER = 'OTHER'

    def __str__(self):
        return self.value
    
    def __repr__(self):
        return self.value
    
    @staticmethod
    def from_string(value: str) -> 'QueryType':
        lower_value = value.lower()
        if lower_value == 'general':
            return QueryType.GENERAL
        elif lower_value == 'personal':
            return QueryType.PERSONAL
        elif lower_value == 'news':
            return QueryType.NEWS
        elif lower_value == 'research':
            return QueryType.RESEARCH
        elif lower_value == 'other':
            return QueryType.OTHER
        else:
            # Default to other
            return QueryType.OTHER

@dataclass
class Query:
    """
    A class to hold a query.
    
    Attributes
    ----------
    query : str
        The query string.
    topic : str
        The topic of the query.
    query_type : QueryType
        The type of the query.
    query_id : str
        The id of the query.
    """
    
    query: str
    topic: str
    query_type: QueryType
    query_id: str | None = None
    embedding: np.ndarray | None = None
    
    def __post_init__(self):
        if self.query_id is None:
            self.query_id = str(uuid4())
            
    def __eq__(self, value):
        if not isinstance(value, Query):
            return False
        
        if self.query_id or value.query_id:
            return self.query_id == value.query_id
        
        return self.query == value.query and self.topic == value.topic and self.query_type == value.query_type
 
@dataclass
class QueryResult:
    """
    A class to hold a query result.
    
    Attributes
    ----------
    result : str
        The result string.
    query : Query
        The query that generated the result.
    embedding : np.ndarray | None = None
        The embedding of the result.
    score : float | None = None
        The score of the result compared to the query.
    scoring_method : str | None = None
        The method used to score the result.
        cosine, bm25, etc.
    source : str | None = None
        The source of the result. For example, a URL.
    retriever : str | None = None
        The retriever that retrieved the result.
    parent : QueryResult | None = None
        The parent query result.
        In case a long result is split into multiple parts.
    parent_part_index : int | None = None
        The index of the parent part.
        Can be used to order the parts and combine them if needed.
    """
    
    result: str
    query: Query
    embedding: np.ndarray | None = None
    score: float | None = None
    scoring_method: str | None = None
    source: str | None = None
    retriever: str | None = None
    parent: 'QueryResult' = None
    parent_part_index: int | None = None
    
    def __eq__(self, value):
        if not isinstance(value, QueryResult):
            return False
        
        return self.result == value.result and self.query == value.query

    def __hash__(self):
        return hash((self.result, self.query))

    def __str__(self):
        return self.result
    
    def __repr__(self):
        return f"QueryResult({self.result}, {self.query})"
    
    def __len__(self):
        return len(self.result)
    
    def __getitem__(self, index):
        return self.result[index]
    
    def __iter__(self):
        return iter(self.result)
    
    def add_parent(self, parent: 'QueryResult', part_index: int):
        """
        Add a parent to the query result.
        
        Parameters
        ----------
        parent : QueryResult
            The parent query result.
        part_index : int
            The index of the parent part."""
        self.parent = parent
        self.parent_part_index = part_index
    
    def add_embedding(self, embedding: np.ndarray):
        self.embedding = embedding
    
    def add_score(self, score: float, method: str):
        self.score = score
        self.scoring_method = method
        
    def split_result(self, max_length: int) -> list['QueryResult']:
        if len(self.result) <= max_length:
            return [self]
        
        text_parts = split_text(self.result, max_length)
        query_parts = [QueryResult(text_part, self.query) for text_part in text_parts]
        for i, query_part in enumerate(query_parts):
            query_part.add_parent(self, i)
            query_part.source = self.source
            query_part.retriever = self.retriever
            
        return query_parts
    
    def chunk_result(self, chunk_size: int=700, overlap: int=400) -> list['QueryResult']:
        if len(self.result) <= chunk_size:
            return [self]
        
        text_parts = chunk_text(self.result, chunk_size, overlap)
        query_parts = [QueryResult(text_part, self.query) for text_part in text_parts]
        for i, query_part in enumerate(query_parts):
            query_part.add_parent(self, i)
            query_part.source = self.source
            query_part.retriever = self.retriever
            
        return query_parts

@dataclass
class QueryResults:
    """
    A class to hold the results of a query.
    
    Attributes
    ----------
    query : str
        The query that was executed.
    results : List[str]
        The results of the query.
    scores: List[float]
        The scores of the results.
    scoring_method: str
        The method used to score the results.
    """

    query: str
    results: list[str] = field(default_factory=list)
    scores: list[float] = field(default_factory=list)
    scoring_method: str | None = None

    def __len__(self) -> int:
        """
        Return the number of results.
        
        Returns
        -------
        int
            The number of results.
        """
        return len(self.results)
    
    def __getitem__(self, index: int) -> str:
        """
        Get the result at the given index.
        
        Parameters
        ----------
        index : int
            The index of the result to get.
        
        Returns
        -------
        str
            The result at the given index.
        """
        return self.results[index]
    
    def __iter__(self):
        """
        Iterate over the results.
        """
        return iter(self.results)
    
    def add_result(self, result: str, score: float = None):
        """
        Add a result to the query results.
        
        Parameters
        ----------
        result : str
            The result to add.
        score : float, optional
            The score of the result. The default is None.
        """
        self.results.append(result)
        self.scores.append(score)
    
    def extend(self, other):
        """
        Extend the results with the results from another QueryResults object.
        
        Parameters
        ----------
        other : QueryResults
            The other QueryResults object to extend the results with.
        """
        self.results.extend(other.results)
        self.scores.extend(other.scores)

        if other.scoring_method != self.scoring_method:
            # If scoring methods are different, set to None to indicate mixed scoring methods
            # To rank results, the results should be re-scored using a single
            # scoring method
            self.scoring_method = None
            self.scores = [None] * len(self)

    def top_k(self, k: int):
        """
        Get the top k results.
        
        Parameters
        ----------
        k : int
            The number of top results to get.
        
        Returns
        -------
        QueryResults
            The top k results.
        """
        top_results = QueryResults(self.query, self.results[:k], self.scores[:k], self.scoring_method)
        return top_results
    
    def rank_my_results(self, scoring_method: str = "cosine"):
        """
        Rank the results based on the scoring method.
        
        Parameters
        ----------
        scoring_method : str, optional
            The method used to score the results. The default is "cosine".
        """
        ranked_queries = QueryResults.rank_results(self.query, self.results, metric=scoring_method)
        self.results, self.scores = [], []
        for result, score in ranked_queries:
            self.add_result(result, score)
        self.scoring_method = scoring_method


    _sentence_transformer_model = None
    

    def model() -> sentence_transformers.SentenceTransformer:
        """
        Get the sentence transformer model.
        """
        if not QueryResults._sentence_transformer_model:
            QueryResults._sentence_transformer_model = sentence_transformers.SentenceTransformer('all-MiniLM-L6-v2')
        return QueryResults._sentence_transformer_model
    
    def embed(text:str) -> np.ndarray:
        """
        Embed a text into a vector.
        
        Parameters
        ----------
        text : str
            The text to embed.
        
        Returns
        -------
        np.ndarray
            The embedded text as a vector.
        """
        tensor = QueryResults.model().encode(text, convert_to_numpy=True)
        return tensor
    
    def calculate_similarity(embedding1:np.ndarray, embedding2:np.ndarray, metric:str='cosine') -> float:
        """
        Calculate the similarity between two embeddings.
        
        Parameters
        ----------
        embedding1 : np.ndarray
            The first embedding.
        embedding2 : np.ndarray
            The second embedding.
        metric : str, optional
            The metric to use for calculating the similarity. The default is 'cosine'.
        
        Returns
        -------
        float
            The similarity between the two embeddings.
        """
        if metric == 'cosine':
            return float(np.dot(embedding1, embedding2) / (np.linalg.norm(embedding1) * np.linalg.norm(embedding2)))
        else:
            raise ValueError(f"Unsupported metric: {metric}")
        
    def bm25_rank_results(query:str, results:list[str]) -> list[tuple[str, float]]:
        """
        Rank the results based on the similarity to the query using BM25.
        
        Parameters
        ----------
        query : str
            The query to rank the results against.
        results : List[str]
            The list of results to rank.
        
        Returns
        -------
        List[Tuple[str, float]]
            A list of tuples containing the result and its similarity to the query.
        """
        bm25 = rank_bm25.BM25Okapi(results)
        
        # Tokenizing the query
        tokenized_query = query.lower().split()

        # Get BM25 scores
        scores = bm25.get_scores(tokenized_query)

        # Rank documents by score
        ranked_results = sorted(zip(results, scores), key=lambda x: x[1], reverse=True)
        return ranked_results
        
    def rank_results(query:str, results:list[str], metric:str='cosine') -> list[tuple[str, float]]:
        """
        Rank the results based on the similarity to the query.
        
        Parameters
        ----------
        query : str
            The query to rank the results against.
        results : List[str]
            The list of results to rank.
        metric : str, optional
            The metric to use for calculating the similarity. The default is 'cosine'.
        
        Returns
        -------
        List[Tuple[str, float]]
            A list of tuples containing the result and its similarity to the query.
        """
        query_embedding = QueryResults.embed(query)
        result_embeddings = [QueryResults.embed(result) for result in results]
        similarities = [QueryResults.calculate_similarity(query_embedding, result_embedding, metric) for result_embedding in result_embeddings]
        ranked_results = sorted(zip(results, similarities), key=lambda x: x[1], reverse=True)
        return ranked_results
    

class RetrievalResults:
    """
    A class to hold the results of a retrieval operation.
    This can include the results of multiple queries.

    Attributes
    ----------
    results : Dict[str, QueryResults]
        The results of the retrieval operation, grouped by query.
    scoring_method: str
        The method used to score the results.
    """
    
    ranker = None
    
    def __init__(self):
        if RetrievalResults.ranker is None:
            from . import BaseRanker
            RetrievalResults.ranker = BaseRanker
            
        self.results: dict[str, QueryResult] = {}
        self.scoring_method: str | None = None
        self._sources = {} # stores results by soure to avoid duplicates
        


    
    def add_result(self, query_result: QueryResult, was_split: bool=False):
        """
        Add a result to the retrieval results.
        
        Parameters
        ----------
        query_result : QueryResult
            The result to add.
        """
        
        if query_result.source in self._sources and not was_split:
            # Avoid duplicates
            return
            
        
        # TODO: add more control over how results are split.
        # This should be controlled either by the pipeline or by the config file
        if len(query_result.result) > 750:
            # Split long results into smaller parts
            query_parts = query_result.chunk_result()
            for query_part in query_parts:
                self.add_result(query_part, was_split=True)
            return
        
        if query_result.query.query_id not in self.results:
            self.results[query_result.query.query_id] = [ query_result ]
        else:
            self.results[query_result.query.query_id].append(query_result)
            
        if self.scoring_method == None and query_result.scoring_method != None and len(self) == 1:
            self.scoring_method = query_result.scoring_method
            
        if query_result.scoring_method != self.scoring_method:
            self.scoring_method = None
            
        

    def __len__(self) -> int:
        """
        Return the number of results.
        
        Returns
        -------
        int
            The number of results.
        """
        n = 0
        for query_id in self.results:
            n += len(self.results[query_id])
        return n
    
    def rank_results(self, scoring_method: str = "cosine"):
        """
        Rank the results based on the scoring method and adjust their scores.
        """
        
        if not RetrievalResults.ranker.has_ranker(scoring_method):
            raise ValueError(f"Ranker not found: {scoring_method}")
        
        RetrievalResults.ranker.rank(self, scoring_method)
        self.scoring_method = scoring_method
        
    def is_ranked(self) -> bool:
        """
        Check if the results are ranked.
        
        Returns
        -------
        bool
            True if the results are ranked, False otherwise.
        """
        return self.scoring_method is not None
    

    def purge(self, min_score: float=0.0, max_results: int=None, min_query_results: int=1):
        """
        Purge the results based on the minimum score and the maximum number of results.
        
        Parameters
        ----------
        min_score : float, optional
            The minimum score of the results. The default is 0.0.
        max_results : int, optional
            The maximum number of results to keep. The default is None.
        min_query_results : int, optional
            The minimum number of results to keep for each query. The default is 1.
            This bypasses the max_results parameter (if n_queries * min_query_results > max_results), but not the min_score parameter.
        """
        top_results = self.top_k(max_results, min_score, min_query_results=min_query_results)
        self.results = {}
        self.scoring_method = None
        self._sources = {}
        for result in top_results:
            self.add_result(result)
        
    
    def top_k(self, k: int | None, min_score: float | None=None, query: Query | None=None, min_query_results: int=1) -> list[QueryResult]:
        """
        Get the top k results.
        
        Parameters
        ----------
        k : int
            The number of top results to get.
            If k is None, return all results.
        min_score : float, optional
            The minimum score of the results. The default is None.
        query : Query, optional
            The query to get the top results for. If None, get the top results for all queries in one ranking.
            The default is None.
        min_query_results : int, optional
            The minimum number of results to keep for each query.
            The default is 1.
            This bypasses the k parameter (if n_queries * min_query_results > k), but not the min_score parameter.
            
        Returns
        -------
        List[QueryResult]
            The top k results.
        """
        
        if not self.is_ranked():
            self.rank_results()
        
        results = []
        
        if query is not None:
            # Get results for a specific query
            if query.query_id in self.results:
                query_results = self.results[query.query_id]
                query_results.sort(key=lambda x: x.score, reverse=True)
                if k is not None:
                    results = query_results[:k]
                else:
                    results = query_results
            else:
                return []
        else:
            # Get results for all queries
            all_results = []
            for query_id in self.results:
                all_results.extend(self.results[query_id])
            all_results.sort(key=lambda x: x.score, reverse=True)
            if k is not None:
                included_queries = dict()
                results = []
                remaining = []
                if(min_query_results > 0):
                    # first make sure we have at least min_query_results for each query
                    for result in all_results:
                        if result.query.query_id not in included_queries:
                            results.append(result)
                            included_queries[result.query.query_id] = 1
                        elif included_queries[result.query.query_id] < min_query_results:
                            results.append(result)
                            included_queries[result.query.query_id] += 1
                        else:
                            remaining.append(result)
                        
                    # then add the remaining results if needed
                    if len(results) < k:
                        results.extend(remaining[:k-len(results)])
                        # sort again
                        results.sort(key=lambda x: x.score, reverse=True)
                else:
                    results = all_results[:k]
                
            else:
                results = all_results
                
        if min_score is not None:
            results = [result for result in results if result.score >= min_score]
            
        return results
        
    def extend(self, other):
        """
        Extend the results with the results from another RetrievalResults object.
        
        Parameters
        ----------
        other : RetrievalResults
            The other RetrievalResults object to extend the results with.
        """
        for query_id in other.results:
            if query_id not in self.results:
                self.results[query_id] = other.results[query_id]
            else:
                self.results[query_id].extend(other.results[query_id])

        if other.scoring_method != self.scoring_method:
            # If scoring methods are different, set to None to indicate mixed scoring methods
            # To rank results, the results should be re-scored using a single
            # scoring method
            self.scoring_method = None
            for query_id in self.results:
                for result in self.results[query_id]:
                    result.score = None





    

