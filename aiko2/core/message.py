from dataclasses import dataclass
from .user import User

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

    # The timestamp of the message.
    timestamp: str

    # The user who sent the message.
    user: User

