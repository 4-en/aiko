from .base_retriever import BaseRetriever
from aiko2.storage import SimpleMultiKnowledgeBase, KnowledgebaseQueryResult
from .retrieval_results import RetrievalResults, Query, QueryResult, QueryType
from aiko2.core import Conversation, Message
import aiko2.utils.pipeline_components as pipeline_components
from .ranking import BaseRanker
import sentence_transformers
from typing import Callable

RoutingScoreFunction = Callable[[str, Query], float]
"""
A function that scores a query based on the domain and the query.
The function should return a score between 0 and 1, where 0 means that
the query should not be routed to the retriever and 1 means that the query
should be routed to the retriever.

Based on the router's configuration, the router will route the query to the
retriever with the n highest scores or all scores above a certain threshold.

Parameters
----------
domain : str
    The domain of the query.
query : Query
    The query to score.

Returns
-------
float
    The score of the query. (0 <= score <= 1)
"""

def domain_routing_function(domains: list[str] | str) -> RoutingScoreFunction:
    """
    Create a routing function that routes queries to retrievers based on the domain.

    Parameters
    ----------
    domains : List[str] | str
        The domain or domains to route queries to.

    Returns
    -------
    RoutingScoreFunction
        A function that scores a query based on the domain and the query.
    """
    if isinstance(domains, str):
        domains = [domains]

    def score_function(domain, query):
        if domain in domains:
            return 1.0
        return 0.0

    return score_function

def query_type_routing_function(query_types: list[QueryType] | QueryType) -> RoutingScoreFunction:
    """
    Create a routing function that routes queries to retrievers based on the query type.

    Parameters
    ----------
    query_types : List[QueryType] | QueryType
        The query type or query types to route queries to.

    Returns
    -------
    RoutingScoreFunction
        A function that scores a query based on the domain and the query.
    """
    if isinstance(query_types, QueryType):
        query_types = [query_types]

    def score_function(domain, query):
        if query.query_type in query_types:
            return 1.0
        return 0.0

    return score_function

def query_string_routing_function(query_strings: list[str] | str, compare_lower=True) -> RoutingScoreFunction:
    """
    Create a routing function that routes queries to retrievers based on the query string.

    Parameters
    ----------
    query_strings : List[str] | str
        The query string or query strings to route queries to.
    compare_lower : bool, optional
        Whether to compare the query strings in lowercase, by default True.

    Returns
    -------
    RoutingScoreFunction
        A function that scores a query based on the domain and the query.
    """
    if isinstance(query_strings, str):
        query_strings = [query_strings]

    if compare_lower:
        query_strings = [query_string.lower() for query_string in query_strings]

    def score_function(domain, query):
        if compare_lower:
            query_str = query.query.lower()
        else:
            query_str = query.query

        for query_string in query_strings:
            if query_string in query_str:
                return 1.0
        return 0.0

    return score_function


class RetrievalRouter(BaseRetriever, pipeline_components.ComponentMixin):
    """
    A retriever that routes queries to different retrievers based on
    the domain or query.
    """

    def __init__(self, retrievers: list[tuple[BaseRetriever, RoutingScoreFunction]]=[]):
        """
        Initialize the retrieval router.

        Parameters
        ----------
        retrievers : List[Tuple[BaseRetriever, RoutingScoreFunction]]
            A list of tuples containing the retriever and the routing function.
        """
        self.retrievers = retrievers

        # TODO: add configuration options to config file
        self.min_score = 0.00001 # minimum score to route a query
        self.max_retrievers = -1 # maximum number of retrievers to route to
        self.max_results = -1 # maximum number of results to return
        self.custom_filters = [] # custom filters to filter the results

    def add_retriever(self, retriever: BaseRetriever, score_function: RoutingScoreFunction):
        """
        Add a retriever to the router.

        Parameters
        ----------
        retriever : BaseRetriever
            The retriever to add.
        score_function : RoutingScoreFunction
            The score function that scores the query based on the domain and the query.
        """
        self.retrievers.append((retriever, score_function))

        return self
    
    def set_min_score(self, min_score: float):
        """
        Set the minimum score to route a query.

        Parameters
        ----------
        min_score : float
            The minimum score to route a query.
        """
        self.min_score = min_score

        return self
    
    def set_max_retrievers(self, max_retrievers: int):
        """
        Set the maximum number of retrievers to route to.

        Parameters
        ----------
        max_retrievers : int
            The maximum number of retrievers to route to.
        """
        self.max_retrievers = max_retrievers

        return self
    
    def set_max_results(self, max_results: int):
        """
        Set the maximum number of results to return.

        Parameters
        ----------
        max_results : int
            The maximum number of results to return.
        """
        self.max_results = max_results

        return self

    def _set_pipeline(self, pipeline):
        """
        Set the pipeline object.

        This method is called by the pipeline object to set itself

        Parameters
        ----------
        pipeline : Pipeline
            The pipeline object
        """
        super()._set_pipeline(pipeline)

        for retriever, _ in self.retrievers:
            if isinstance(retriever, pipeline_components.ComponentMixin):
                retriever._set_pipeline(pipeline)

    def _route_query(self, query: Query, domain: str) -> list[RetrievalResults]:
        """
        Route a query to the retrievers based on the domain and the query.

        Parameters
        ----------
        query : Query
            The query to route.
        domain : str
            The domain of the query.

        Returns
        -------
        List[RetrievalResults]
            A list of retrieval results from the routed queries.
        """
        # score the query for each retriever
        scores = []
        for retriever, score_function in self.retrievers:
            score = score_function(domain, query)
            scores.append((retriever, score))

        # filter the retrievers based on the score
        filtered_retrievers = [(retriever, score) for retriever, score in scores if score >= self.min_score]

        # sort the retrievers based on the score
        sorted_retrievers = sorted(filtered_retrievers, key=lambda x: x[1], reverse=True)

        # get the top retrievers
        if self.max_retrievers > 0:
            sorted_retrievers = sorted_retrievers[:self.max_retrievers]

        # route the query to the retrievers
        results = []
        for retriever, _ in sorted_retrievers:
            results.append(retriever.retrieve(query.conversation, [query], domain))

        return results



    def retrieve(self, conversation: Conversation, queries: list[Query], domain: str | list[str] = None) -> RetrievalResults:
        """
        Retrieve information based on the queries generated by the evaluator.
        
        Parameters
        ----------
        conversation : Conversation
            The conversation to retrieve information for.
        queries : List[Query]
            A list of queries to retrieve information.
        domain : str | list[str], optional
            The domain to retrieve information from, by default None.
            Can be used to only retrieve information from a specific domain, for example
            for a specific user or specific source.
            
        Returns
        -------
        RetrievalResults
            The retrieval context containing the results of the retrieval operation.
        """


        # route the queries to the retrievers
        results = []
        for query in queries:
            results.extend(self._route_query(query, domain))

        # merge the results
        if len(results) == 0:
            return RetrievalResults()
        
        
        merged_results: RetrievalResults = results[0]

        for result in results[1:]:
            merged_results.extend(result)

        # only return the top results
        if self.max_results > 0:
            merged_results.purge(max_results=self.max_results)

        return merged_results

        