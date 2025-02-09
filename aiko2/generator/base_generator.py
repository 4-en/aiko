from aiko2.core import Conversation, Message, User, Role
from abc import ABC, abstractmethod
from aiko2.config import Config
import aiko2.pipeline.pipeline_components as pipeline_components
from dataclasses import dataclass, field

@dataclass
class GeneratorConfig:
    """
    A configuration for a generator.
    This configuration is used to tune various parameters of the generator.
    
    Unifies different configurations for different generators.
    
    Attributes
    ----------
    temperature : float
        The temperature of the generator.
    max_tokens : int
        The maximum number of tokens to generate.
    top_p : float
        The nucleus sampling probability.
    top_k : int
        The nucleus sampling top-k value.
    frequency_penalty : float
        The frequency penalty.
    presence_penalty : float
        The presence penalty.
    stop : List[str]
        A list of stop words.
    """
    
    temperature: float = 0.7
    max_tokens: int = 1000
    top_p: float = 0.9
    top_k: int = 50
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    stop: list[str] = field(default_factory=lambda: [])
    
    

class BaseGenerator(ABC, pipeline_components.ComponentMixin):
    """
    Base class for a generator.
    A generator generates a response based on the conversation.
    """

    def __init__(self, accepts_images:bool=False):
        self.accepts_images = accepts_images

    @abstractmethod
    def generate(self, conversation:Conversation) -> Message:
        """
        Generate a response based on the conversation.

        Parameters
        ----------
        conversation : Conversation
            The conversation to generate a response for.

        Returns
        -------
        Message
            The response generated.
        """
        pass
    
    @abstractmethod
    def convert_conversation_to_input(self, conversation:Conversation) -> any:
        """
        Convert a conversation to an input string for the generator.

        Parameters
        ----------
        conversation : Conversation
            The conversation to convert.

        Returns
        -------
        any
            The input for the generator. 
            As different generators may require different input types, this method is abstract.
        """
        pass
    
    @abstractmethod
    def convert_output_to_message(self, output:any) -> Message:
        """
        Convert the output of the generator to a message.

        Parameters
        ----------
        output : any
            The output of the generator.
            As different generators may generate different types of output, this method is abstract.

        Returns
        -------
        Message
            The message generated.
        """
        pass

class TestGenerator(BaseGenerator):

    def __init__(self):
        self.assistant = User("Assistant", Role.ASSISTANT)

    def generate(self, conversation:Conversation) -> Message:
        return Message("Hello!", self.assistant)
    
    def convert_conversation_to_input(self, conversation:Conversation) -> str:
        return "Hello!"
    
    def convert_output_to_message(self, output:str) -> Message:
        return Message(output)