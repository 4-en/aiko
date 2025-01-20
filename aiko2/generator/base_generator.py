from aiko2.core import Conversation, Message, User, Role
from abc import ABC, abstractmethod
from aiko2.config import Config

class BaseGenerator(ABC):
    """
    Base class for a generator.
    A generator generates a response based on the conversation.
    """
    
    def _setup(self, config:Config):
        """
        Setup the generator.
        This method is called by the pipeline to setup the generator.

        Parameters
        ----------
        config : Config
            The configuration to use for the generator.
        """
        self.config = config

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
    def convert_conversation_to_input(conversation:Conversation) -> any:
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
    
    def convert_conversation_to_input(conversation:Conversation) -> str:
        return "Hello!"
    
    def convert_output_to_message(self, output:str) -> Message:
        return Message(output)