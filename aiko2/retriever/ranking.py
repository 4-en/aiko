# contains different functions for ranking the retrieval results.

from abc import ABC, abstractmethod
from aiko2.core import QueryResult, Query, RetrievalResults
from rank_bm25 import BM25Okapi

from dataclasses import dataclass
import numpy as np
from sentence_transformers import SentenceTransformer, util

@dataclass
class RankerResult:
    """
    A class representing the result of a ranking operation.
    
    Attributes
    ----------
    score : float
        The score of the ranking operation.
    embedding : np.array | None
        The embedding of the result (if applicable).
    """
    
    score: float
    embedding: np.ndarray | None = None
    
def register_ranker(method: str | list[str]):
    """
    Decorator to automatically register a ranker class.
    """
    def decorator(cls):
        instance = cls()  # Instantiate the ranker
        if isinstance(method, str):
            BaseRanker.register_ranker(method, instance)
        elif isinstance(method, list):
            for m in method:
                BaseRanker.register_ranker(m, instance)
        else:
            raise ValueError("Invalid metric type. Expected str or list[str].")
        return cls
    return decorator

class BaseRanker(ABC):
    
    _ranker: dict[str, "BaseRanker"] = {}
    
    @staticmethod
    def register_ranker(method: str, ranker: "BaseRanker"):
        """
        Register a ranker.
        
        Parameters
        ----------
        method : str
            The ranking method to register.
        ranker : BaseRanker
            The ranker to register.
        """
        
        BaseRanker._ranker[method] = ranker
        
    @staticmethod
    def get_ranker(method: str) -> "BaseRanker":
        """
        Get a ranker by metric.
        
        Parameters
        ----------
        method : str
            The ranking method to get.
        
        Returns
        -------
        BaseRanker
            The ranker.
        """
        if not method in BaseRanker._ranker:
            raise ValueError(f"Ranker for metric {method} not found.")
        
        return BaseRanker._ranker[method]
    
    @staticmethod
    def has_ranker(method: str) -> bool:
        """
        Check if a ranker exists for a metric.
        
        Parameters
        ----------
        method : str
            The method to check.
        
        Returns
        -------
        bool
            True if a ranker exists, False otherwise.
        """
        return method in BaseRanker._ranker
        
    @staticmethod
    def _rank_retrieval_results(retrieval_results: RetrievalResults, method: str) -> RetrievalResults:
        """
        Rank the retrieval results.
        
        Parameters
        ----------
        retrieval_results : RetrievalResults
            The retrieval results to rank.
        method : str
            The method to rank the results by.
        
        Returns
        -------
        RetrievalResults
            The ranked retrieval results.
        """
        for k, v in retrieval_results.results.items():
            retrieval_results.results[k] = BaseRanker._rank_query_results(v, method)
            
        return retrieval_results
    
    @staticmethod
    def _rank_query_results(query_results: list[QueryResult], method: str) -> list[QueryResult]:
        """
        Rank the query results.
        
        Parameters
        ----------
        query_results : list[QueryResult]
            The query results to rank.
        method : str
            The method to rank the results by.
        
        Returns
        -------
        list[QueryResult]
            The ranked query results.
        """
        
        ranker = BaseRanker.get_ranker(method)
        if ranker is None:
            raise ValueError(f"Ranker for method {method} not found.")
        
        # ensure that queries really are the same:
        queries = {}
        for query_result in query_results:
            if query_result.query.query_id not in queries:
                queries[query_result.query.query_id] = [query_result]
            else:
                queries[query_result.query.query_id].append(query_result)
                
        ranked_query_results = []
        for query_results in queries.values():
            rankings = ranker.rank_results(query_results[0].query, [query_result.result for query_result in query_results])
            for query_result, ranking in zip(query_results, rankings):
                query_result.score = ranking.score
                if ranking.embedding is not None:
                    query_result.embedding = ranking.embedding
                    
                query_result.scoring_method = method
                ranked_query_results.append(query_result)
                
        return ranked_query_results
    
    @staticmethod
    def _rank_query_result(query_result: QueryResult, method: str) -> QueryResult:
        """
        Rank the query result.
        
        Parameters
        ----------
        query_result : QueryResult
            The query result to rank.
        method : str
            The method to rank the result by.
        
        Returns
        -------
        QueryResult
            The ranked query result.
        """
        return BaseRanker._rank_query_results([query_result], method)[0]
        
    @staticmethod
    def rank(query_results: RetrievalResults | list[QueryResult] | QueryResult, method: str) -> RetrievalResults | list[QueryResult] | QueryResult:
        """
        Rank the query results.
        
        Parameters
        ----------
        query_results : RetrievalResults | list[QueryResult] | QueryResult
            The query results to rank.
        method : str
            The method to rank the results by.
            
        Returns
        -------
        RetrievalResults | list[QueryResult] | QueryResult
            The ranked results.
            Based on the input type.
        """
        
        if isinstance(query_results, RetrievalResults):
            return BaseRanker._rank_retrieval_results(query_results, method)
        elif isinstance(query_results, list):
            return BaseRanker._rank_query_results(query_results, method)
        elif isinstance(query_results, QueryResult):
            return BaseRanker._rank_query_result(query_results, method)
        else:
            raise TypeError("Unsupported type for ranking. Expected RetrievalResults, list[QueryResult], or QueryResult.")
        
    @abstractmethod
    def rank_results(self, query: Query, results: list[str]) -> list[RankerResult]:
        """
        Rank the query results.
        
        Parameters
        ----------
        query : Query
            The query to rank the results for.
            (Query is the same for all results)
        results : list[str]
            The results to rank.
            
        Returns
        -------
        list[RankerResult]
            The ranked results in order of input results.
        """
        pass

    def get_embedder(self) -> SentenceTransformer:
        """
        Get the embedding model for this ranker.
        
        Returns
        -------
        SentenceTransformer
            The embedding model.
        """
        raise NotImplementedError("Embedding not implemented for this ranker.")

    def _embed_text(self, text:str | list[str]) -> np.ndarray:
        """
        Embed a text using an embedding model.
        
        Parameters
        ----------
        text : str | list[str]
            The text to embed.
            If a list of strings is provided, result will have shape (n, embedding_size).
        
        Returns
        -------
        np.array
            The embedding of the text.
        """
        raise NotImplementedError("Embedding not implemented for this ranker.")

    @staticmethod
    def embed_text(text:str | list[str], method: str) -> np.ndarray:
        """
        Embed a text using an embedding model.
        
        Parameters
        ----------
        text : str | list[str]
            The text to embed.
            If a list of strings is provided, result will have shape (n, embedding_size).
        method : str
            The method to use for embedding.

        Returns
        -------
        np.array
            The embedding of the text.
        """
        ranker = BaseRanker.get_ranker(method)
        if ranker is None:
            raise ValueError(f"Ranker for method {method} not found.")
        
        return ranker._embed_text(text)
    
    def _embed_query(self, query: str) -> np.ndarray:
        """
        Embed a query using an embedding model.
        
        Parameters
        ----------
        query : str
            The query to embed.
        
        Returns
        -------
        np.array
            The embedding of the query.
        """
        # Default implementation is to embed the text
        # some rankers may use different methods for queries and passages
        return self._embed_text(query)
    
    @staticmethod
    def embed_query(query: str, method: str) -> np.ndarray:
        """
        Embed a query using an embedding model.
        
        Parameters
        ----------
        query : str
            The query to embed.
        method : str
            The method to use for embedding.

        Returns
        -------
        np.array
            The embedding of the query.
        """
        ranker = BaseRanker.get_ranker(method)
        if ranker is None:
            raise ValueError(f"Ranker for method {method} not found.")
        
        return ranker._embed_query(query)
    

    def _calculate_scores(self, query_embedding: np.ndarray, result_embeddings: np.ndarray) -> np.ndarray:
        """
        Calculate the scores for the query and result embeddings.
        
        Parameters
        ----------
        query_embedding : np.ndarray
            The embedding of the query.
        result_embeddings : np.ndarray
            The embeddings of the results.
        
        Returns
        -------
        np.ndarray
            The scores for the results.
        """
        raise NotImplementedError("Scoring not implemented for this ranker.")
    
    @staticmethod
    def calculate_scores(query_embedding: np.ndarray, result_embeddings: np.ndarray, method: str) -> np.ndarray:
        """
        Calculate the scores for the query and result embeddings.
        
        Parameters
        ----------
        query_embedding : np.ndarray
            The embedding of the query.
        result_embeddings : np.ndarray
            The embeddings of the results.
        method : str
            The method to use for scoring.
        
        Returns
        -------
        np.ndarray
            The scores for the results.
        """
        ranker = BaseRanker.get_ranker(method)
        if ranker is None:
            raise ValueError(f"Ranker for method {method} not found.")
        
        return ranker._calculate_scores(query_embedding, result_embeddings)
    

@register_ranker("bm25")
class BM25Ranker(BaseRanker):
    """
    A ranker using the BM25 algorithm.
    """
        
    def rank_results(self, query: Query, results: list[str]) -> list[RankerResult]:
        
        ranked_results = []
        
        tokenized_results = [result.split() for result in results]
        bm25 = BM25Okapi(tokenized_results)
        scores = bm25.get_scores(query.query.split())
        
        for score in scores:
            ranked_results.append(RankerResult(score))
            
        return ranked_results


@register_ranker("cosine")
class MultiQARanker(BaseRanker):
    """
    The default ranker for embedding-based ranking with cosine similarity as scoring method.
    """
    
    _embedder = None
    
    def get_embedder(self) -> SentenceTransformer:
        if MultiQARanker._embedder is None:
            MultiQARanker._embedder = SentenceTransformer('sentence-transformers/multi-qa-MiniLM-L6-cos-v1')
        return MultiQARanker._embedder
    
    def rank_results(self, query: Query, results: list[str]) -> list[RankerResult]:
        
        ranked_results = []
        
        embedder = MultiQARanker.get_embedder()
        query_embedding = embedder.encode(query.query)
        result_embeddings = embedder.encode(results)
        
        # sentence transformer already normalizes the embeddings, so we can use dot product as cosine similarity
        scores = util.dot_score(query_embedding, result_embeddings)[0].cpu().tolist()

        for score, result_embedding in zip(scores, result_embeddings):
            ranked_results.append(RankerResult(score, result_embedding))
            
        return ranked_results
    
    def _embed_text(self, text:str | list[str]) -> np.ndarray:
        embedder = self.get_embedder()
        return embedder.encode(text)
    
    def _embed_query(self, query: str) -> np.ndarray:
        embedder = self.get_embedder()
        return embedder.encode(query)
    
    def _calculate_scores(self, query_embedding, result_embeddings):
        scores = util.dot_score(query_embedding, result_embeddings).cpu().tolist()
        return scores
        