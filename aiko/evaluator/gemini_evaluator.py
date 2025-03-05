from .base_evaluator import BaseEvaluator
from aiko2.generator import Gemini15Flash, Gemini15Flash8B, BaseGenerator

class GeminiEvaluator(BaseEvaluator):
    """
    A Gemini evaluator that generates queries using the Gemini API.
    """
    def __init__(self, generator:BaseGenerator=Gemini15Flash()):
        super().__init__(generator)
        

class Gemini15FlashEvaluator(GeminiEvaluator):
    """
    A Gemini 1.5 Flash evaluator.
    """
    
    def __init__(self):
        super().__init__(Gemini15Flash())
        
class Gemini15Flash8BEvaluator(GeminiEvaluator):
    """
    A Gemini 1.5 Flash 8B evaluator.
    """
    
    def __init__(self):
        super().__init__(Gemini15Flash8B())