from dataclasses import dataclass
from .user import User
from time import time

@dataclass
class Message:
    """
    Message class to represent a message.

    Attributes
    ----------
    content : str
        The message content.
    timestamp : str
        The timestamp of the message.
    user : User
        The user who sent the message.
    """

    # The message content.
    content: str

    # The user who sent the message.
    user: User = None

    # The timestamp of the message.
    timestamp: str = None


    def __post_init__(self):
        """
        Initialize the message.
        """
        if self.timestamp is None or self.timestamp == "":
            self.timestamp = str(time())

        if self.user is None:
            self.user = User("Unknown", "USER", "-1")


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

