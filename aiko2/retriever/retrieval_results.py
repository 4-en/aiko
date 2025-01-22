from dataclasses import dataclass, field
import sentence_transformers
import numpy as np
import rank_bm25

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
    
    def rank_results(self, scoring_method: str = "cosine"):
        """
        Rank the results based on the scoring method.
        """
        self.scoring_method = scoring_method
        for query_results in self.search_results:
            query_results.rank_my_results(scoring_method)





    

