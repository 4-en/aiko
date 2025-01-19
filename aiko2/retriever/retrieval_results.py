from dataclasses import dataclass, field

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
    
@dataclass
class RetrievalResults:
    """
    A class to hold the results of a retrieval operation.
    This can include the results of multiple queries.

    Attributes
    ----------
    query_results : List[QueryResults]
        The results of the queries.
    scoring_method: str
        The method used to score the results.
    """

    search_results: list[QueryResults] = field(default_factory=list)
    scoring_method: str | None = None

    def __len__(self) -> int:
        """
        Return the number of results.
        
        Returns
        -------
        int
            The number of results.
        """
        return sum(len(qr) for qr in self.search_results)



    

