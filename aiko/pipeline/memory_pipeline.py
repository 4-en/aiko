from .pipeline import Pipeline
from aiko.pipeline.pipeline_components import MemoryHandler
from aiko.core import Conversation, Message, User, Role, Memory, RetrievalResults, QueryType
from aiko.config import Config

from aiko.evaluator import BaseEvaluator
from aiko.generator import BaseGenerator
from aiko.refiner import BaseRefiner
from aiko.retriever import BaseRetriever, MemoryRetriever
from aiko.utils import get_storage_location
from aiko.generator import Gemini15Flash8B, GeminiGenerator
from aiko.evaluator import BaseEvaluator


class MemoryPipeline(Pipeline):
    """
    A pipeline with dynamic memory.
    """
    
    
    def __init__(
            self, 
            generator: BaseGenerator=None,
            evaluator: BaseEvaluator=None, 
            retriever: BaseRetriever=None,
            refiner: BaseRefiner=None,
            memory_handler: MemoryHandler=None,
            root_dir: str=None,
            config: Config=None
        ) -> None:
        
        if generator is None:
            # use gemini as the default generator
            generator = Gemini15Flash8B()
        
        if evaluator is None:
            # use generator as the default evaluator
            evaluator = BaseEvaluator(generator=generator)
            
        if retriever is None:
            # create a memory retriever
            retriever = MemoryRetriever()
            memory_handler = retriever
            
        super().__init__(generator, evaluator, retriever, refiner, memory_handler, root_dir, config)
            
            
        