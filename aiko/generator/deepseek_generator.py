from .openai_generator import OpenAIGenerator
import openai
from aiko2.core import User, Role
from enum import Enum

class DeepSeekModel(Enum):
    """
    A collection of DeepSeek models available for use.

    Parameters
    ----------
    Enum : str
        The model name used by the DeepSeek API.
    """
    
    CHAT = "deepseek-chat"
    REASONER = "deepseek-reasoner"

DEEPSEEK_API_KEY_NAME = "DEEPSEEK_API_KEY"

class DeepSeekGenerator(OpenAIGenerator):
    
    def __init__(self, model: DeepSeekModel=DeepSeekModel.CHAT):
        """
        Initialize the DeepSeek generator.
        
        Parameters
        ----------
        model : DeepSeekModel, optional
            The model to use for generating responses, by default DeepSeekModel.CHAT
        """
        super().__init__(model=model)
    
    def _setup_client(self):
        """
        Setup the DeepSeek client.
        """
        
        if self.get_config() is None:
            raise ValueError("Generator not setup. Config not set.")
        
        self.assistant = User(self.get_config_value("name", "Assistant"), Role.ASSISTANT)
        
        
        # Retrieve the OpenAI API key from the .env file
        API_KEY = self.getenv(DEEPSEEK_API_KEY_NAME)
        
        # Initialize the OpenAI client
        self.client = openai.OpenAI(
            api_key=API_KEY,
            base_url="https://api.deepseek.com"
        )