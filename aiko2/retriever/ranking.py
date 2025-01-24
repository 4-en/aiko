# contains different functions for ranking the retrieval results.

from abc import ABC, abstractmethod
from . import QueryResult, Query, RetrievalResults

from dataclasses import dataclass
import numpy as np

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
    embedding: np.array | None = None

class BaseRanker(ABC):
    
    _ranker: dict[str, "BaseRanker"] = {}
    
    @staticmethod
    def register_ranker(metric: str, ranker: "BaseRanker"):
        """
        Register a ranker.
        
        Parameters
        ----------
        metric : str
            The metric to register the ranker for.
        ranker : BaseRanker
            The ranker to register.
        """
        
        BaseRanker._ranker[metric] = ranker
        
    @staticmethod
    def get_ranker(metric: str) -> "BaseRanker":
        """
        Get a ranker by metric.
        
        Parameters
        ----------
        metric : str
            The metric of the ranker to get.
        
        Returns
        -------
        BaseRanker
            The ranker.
        """
        if not metric in BaseRanker._ranker:
            raise ValueError(f"Ranker for metric {metric} not found.")
        
        return BaseRanker._ranker[metric]
    
    def __init__(self, metric: str):
        self.metric = metric
        BaseRanker.register_ranker(metric, self)
        
    @staticmethod
    def _rank_retrieval_results(retrieval_results: RetrievalResults, metric: str) -> RetrievalResults:
        """
        Rank the retrieval results.
        
        Parameters
        ----------
        retrieval_results : RetrievalResults
            The retrieval results to rank.
        
        Returns
        -------
        RetrievalResults
            The ranked retrieval results.
        """
        for k, v in retrieval_results.results.items():
            retrieval_results.results[k] = BaseRanker._rank_query_results(v, metric)
            
        return retrieval_results
    
    @staticmethod
    def _rank_query_results(query_results: list[QueryResult], metric: str) -> list[QueryResult]:
        """
        Rank the query results.
        
        Parameters
        ----------
        query_results : list[QueryResult]
            The query results to rank.
        
        Returns
        -------
        list[QueryResult]
            The ranked query results.
        """
        
        ranker = BaseRanker.get_ranker(metric)
        if ranker is None:
            raise ValueError(f"Ranker for metric {metric} not found.")
        
        # ensure that queries really are the same:
        queries = {}
        for query_result in query_results:
            if query_result.query.query_id not in queries:
                queries[query_result.query.query_id] = [query_result]
            else:
                queries[query_result.query.query_id].append(query_result)
                
        ranked_query_results = []
        for query_results in queries.values():
            rankings = ranker.rank_results(query_results[0].query, [query_result.content for query_result in query_results])
            for query_result, ranking in zip(query_results, rankings):
                query_result.ranker_result = ranking
                if ranking.embedding is not None:
                    query_result.embedding = ranking.embedding
                ranked_query_results.append(query_result)
                
        return ranked_query_results
    
    @staticmethod
    def _rank_query_result(query_result: QueryResult, metric: str) -> QueryResult:
        """
        Rank the query result.
        
        Parameters
        ----------
        query_result : QueryResult
            The query result to rank.
        
        Returns
        -------
        QueryResult
            The ranked query result.
        """
        return BaseRanker._rank_query_results([query_result], metric)[0]
        
    @staticmethod
    def rank(query_results: RetrievalResults | list[QueryResult] | QueryResult, metric: str) -> RetrievalResults | list[QueryResult] | QueryResult:
        """
        Rank the query results.
        
        Parameters
        ----------
        query_results : RetrievalResults | list[QueryResult] | QueryResult
            The query results to rank.
        metric : str
            The metric to rank the results by.
            
        Returns
        -------
        RetrievalResults | list[QueryResult] | QueryResult
            The ranked results.
            Based on the input type.
        """
        
        if isinstance(query_results, RetrievalResults):
            return BaseRanker._rank_retrieval_results(query_results, metric)
        elif isinstance(query_results, list):
            return BaseRanker._rank_query_results(query_results, metric)
        elif isinstance(query_results, QueryResult):
            return BaseRanker._rank_query_result(query_results, metric)
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
        