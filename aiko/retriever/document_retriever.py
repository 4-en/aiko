from .base_retriever import BaseRetriever
from aiko2.storage import KnowledgebaseQueryResult
from aiko2.core import Conversation, Message, RetrievalResults, Query, QueryResult
import aiko2.pipeline.pipeline_components as pipeline_components
from .ranking import BaseRanker
import sentence_transformers


class DocumentRetriever(BaseRetriever, pipeline_components.ComponentMixin):
    """
    A retriever that retrieves information from a directory of documents.
    """
    
    def __init__(self, document_root:str, storage_name:str="documents"):
        """
        Initialize the document retriever.

        Parameters
        ----------
        document_root : str
            The root directory of the documents.
        storage_name : str, optional
            The name of the storage, by default "documents"
        """
        self.embedder = None
        self.document_root = document_root
        self.storage_name = storage_name
    
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
        
        self.embedder = BaseRanker.get_ranker("cosine")._embedder
        if self.embedder is None:
            self.embedder = sentence_transformers.SentenceTransformer("sentence-transformers/multi-qa-MiniLM-L6-cos-v1")
    
    def retrieve(self, query: Query) -> RetrievalResults:
        """
        Retrieve information based on the query.
        
        Parameters
        ----------
        query : Query
            The query to retrieve information for
        
        Returns
        -------
        RetrievalResults
            The retrieval results
        """
        # get the query text
        query_text = query.query

        return RetrievalResults()