from abc import ABC, abstractmethod
from aiko2.core import Conversation, Message, User

class BasePipeline(ABC):
    """
    Base class for all pipelines.
    This class controls the retrieval and generation process.
    At minimum, the pipeline should be able to generate a response
    using the generate method.
    """

    @abstractmethod
    def generate(self, conversation: Conversation) -> Message | None:
        """
        Generate a response based on the conversation.

        Parameters
        ----------
        conversation : Conversation
            The conversation to generate a response from.

        Returns
        -------
        Message | None
            The generated response.
            If no response was generated, return None.
            This can happen if the pipeline is setup to decide 
            whether to generate a response or not, for example if
            the message wasn't directed at the AI.
        """
        pass

    def __call__(self, conversation: Conversation) -> Message | None:
        """
        Call the pipeline to generate a response.

        Parameters
        ----------
        conversation : Conversation
            The conversation to generate a response from.

        Returns
        -------
        Message | None
            The generated response.
            If no response was generated, return None.
            This can happen if the pipeline is setup to decide 
            whether to generate a response or not, for example if
            the message wasn't directed at the AI.
        """

        return self.generate(conversation)