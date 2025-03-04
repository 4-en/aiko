from .base_retriever import BaseRetriever
from aiko2.storage import SimpleMultiKnowledgeBase, KnowledgebaseQueryResult
from aiko2.core.retrieval_results import RetrievalResults, Query, QueryResult, RetrieverType
from aiko2.core import Conversation, Message
import aiko2.pipeline.pipeline_components as pipeline_components
from .ranking import BaseRanker
import sentence_transformers
from aiko2.core import Memory

import os

# A memory retriever is a retriever with a dynamic memory that can be updated
# using results from the evaluator.
# Like the base retriever, it also retrieves information based on the queries generated.

class MemoryRetriever(BaseRetriever, pipeline_components.ComponentMixin, pipeline_components.MemoryHandler):
    """
    A retriever with a dynamic memory that can be updated using results from the evaluator.
    """
    
    def __init__(self, storage_name:str="memory", embedding_dim:int=384):
        """
        Initialize the memory retriever.
        
        Parameters
        ----------
        storage_name : str, optional
            The name of the storage, by default "memory"
        embedding_dim : int, optional
            The dimension of the embeddings, by default 384
        """

        self.knowledge_base = None
        self.embedder = None
        self.storage_name = storage_name
        self.embedding_dim = embedding_dim
    

    def save(self):
        if self.knowledge_base is not None:
            self.knowledge_base.save()

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
        
        # base path
        base_path = self.get_root_dir()
        memory_path = os.path.join(base_path, self.storage_name)
        self.knowledge_base = SimpleMultiKnowledgeBase(memory_path, self.embedding_dim)
        self.embedder = BaseRanker.get_ranker("cosine")._embedder
        if self.embedder is None:
            self.embedder = sentence_transformers.SentenceTransformer("sentence-transformers/multi-qa-MiniLM-L6-cos-v1")

    def _clean_domain(domain:str) -> str:
        """
        Clean the domain name.
        Removes all non-alphanumeric characters or non underscores and converts to lowercase.
        
        Parameters
        ----------
        domain : str
            The domain name to clean
        
        Returns
        -------
        str
            The cleaned domain name
        """
        no_spaces = domain.replace(" ", "_")
        return ''.join(e for e in no_spaces if e.isalnum() or e == "_").lower()

    def add_memory(self, memory:Memory, domain:str=None):
        """
        Add a memory to the knowledge base.
        
        Parameters
        ----------
        memory : Memory
            The memory to add
        domain : str, optional
            The domain of the memory, by default None
            If None, the domain is the person of the memory
        """


        # domain is the person if not provided otherwise
        domain = MemoryRetriever._clean_domain(memory.entities) if domain is None else MemoryRetriever._clean_domain(domain)
        content = memory.memory
        vector = self.embedder.encode(content, convert_to_numpy=True)

        # TODO: check for similar memories and either combine them or skip if same info

        self.knowledge_base.insert(domain, content, vector)

    def retrieve(self, conversation:Conversation, queries:list[Query], domain:str=None) -> RetrievalResults:
        '''
        Retrieve information based on the queries generated by the evaluator.
        
        Queries all available domains.
        
        Parameters
        ----------
        conversation : Conversation
            The conversation to retrieve information for.
        queries : List[Query]
            A list of queries to retrieve information.
            
        Returns
        -------
        RetrievalResults
            The retrieval context containing the results of the retrieval operation.
        '''
        return self.retrieve_in_domains(None, conversation, queries)

    def retrieve_in_domains(self, domains:list[str], conversation:Conversation, queries:list[Query]) -> RetrievalResults:
        """
        Retrieve information based on the queries generated by the evaluator.
        
        Parameters
        ----------
        domains : List[str]
            A list of domains to retrieve information from.
        conversation : Conversation
            The conversation to retrieve information for.
        queries : List[Query]
            A list of queries to retrieve information.
        
        Returns
        -------
        RetrievalResults
            The retrieval context containing the results of the retrieval operation.
        """
        
        # Initialize the retrieval results
        retrieval_results = RetrievalResults()
        
        query_embeddings = self.embedder.encode([query.query for query in queries], convert_to_numpy=True)

        # get the top k results from the knowledge base
        for query, query_embedding in zip(queries, query_embeddings):
            results: list[KnowledgebaseQueryResult] = []
            if domains is None:
                results = self.knowledge_base.query(query_embedding, k=5)
            else:
                for domain in domains:
                    results.extend(self.knowledge_base.query(query_embedding, k=5, domain=domain))

            for result in results:
                query_result = QueryResult(
                    result=result.value,
                    query=query,
                    source=result.domain + "-" + result.key if result.domain is not None else result.key,
                    retriever_type=RetrieverType.MEMORY,
                    embedding=result.vector, 
                    score=result.score,
                    scoring_method="cosine"
                )
                retrieval_results.add_result(query_result)

        return retrieval_results