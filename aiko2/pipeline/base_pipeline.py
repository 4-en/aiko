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
        
        # TODO: Add more generation parameters, such as:
        # - domain: str (for retrieval or memory storage)
        # - context: str (context regardless of conversation and retrieval)
        # - retrieval: bool (whether to retrieve memories or not)
        # - memory: bool (whether to store the conversation in memory or not)
        # - reply-chance-multiplier: float (multiplier for the reply chance, ie how likely the AI is to reply)
        # - reply-chance-threshold: float (threshold for the reply chance, ie how likely the AI is to reply)
        # - probably more...
        
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