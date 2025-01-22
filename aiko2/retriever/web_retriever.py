from . import RetrievalResults, QueryResults, BaseRetriever
from aiko2.core import Conversation

class WebRetriever(BaseRetriever):
    """
    A retriever that retrieves information from the web using a query.
    
    """
    
    def retrieve(self, conversation, queries):
        """
        Retrieve information from the web using a query.
        
        Parameters
        ----------
        conversation : Conversation
            The conversation to retrieve information for.
        queries : List[str]
            A list of queries to retrieve information.
        
        Returns
        -------
        RetrievalResults
            The retrieval context containing the results of the retrieval operation.
        """
        pass