from aiko2.core import Conversation, Message, User
from abc import ABC, abstractmethod

class BaseGenerator(ABC):
    """
    Base class for a generator.
    A generator generates a response based on the conversation.
    """

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

class TestGenerator(BaseGenerator):

    def __init__(self):
        self.assistant = User("Assistant", "ASSISTANT")

    def generate(self, conversation:Conversation) -> Message:
        return Message("Hello!", self.assistant)