from aiko2.core import Conversation, Message, User
from abc import ABC, abstractmethod

class BaseEvaluator(ABC):
    """
    Base class for an evaluator.
    An evaluator decides whether to retrieve information or not.
    It generates one or more queries to retrieve information if needed.
    """

    @abstractmethod
    def evaluate(self, conversation:Conversation) -> list[str]:
        """
        Evaluate the conversation and return one or more queries to retrieve information.

        Parameters
        ----------
        conversation : Conversation
            The conversation to evaluate.

        Returns
        -------
        List[str]
            A list of queries to retrieve information.
            If no queries are generated, return an empty list.
        """
        pass