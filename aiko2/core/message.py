from dataclasses import dataclass
from .user import User
from time import time
from uuid import uuid4
from aiko2.utils.estimate_tokens import estimate_tokens

@dataclass
class Message:
    """
    Message class to represent a message.

    Attributes
    ----------
    content : str
        The message content.
    user : User
        The user who sent the message.
    timestamp : str
        The timestamp of the message.
    id : str
        The message id.
    """

    # The message content.
    content: str

    # The user who sent the message.
    user: User = None

    # The timestamp of the message.
    timestamp: str = None

    # The message id.
    id: str = None


    def __post_init__(self):
        """
        Initialize the message.
        """
        if self.timestamp is None or self.timestamp == "":
            self.timestamp = str(time())

        if self.user is None:
            self.user = User("Unknown", "USER", "-1")

        if self.id is None:
            self.id = str(uuid4())


    def __str__(self) -> str:
        """
        Return the string representation of the message.

        Returns
        -------
        str
            The string representation of the message.
        """
        return f"{self.user.name}: {self.content}"
    
    def __repr__(self) -> str:
        """
        Return the string representation of the message.

        Returns
        -------
        str
            The string representation of the message.
        """
        return f"{self.user.name}: {self.content}"
    
    def estimate_tokens(self) -> int:
        """
        Estimate the number of tokens in the message content.

        Returns
        -------
        int
            The estimated number of tokens in the message content.
        """
        return estimate_tokens(f"<{self.user.name}> {self.content}")

