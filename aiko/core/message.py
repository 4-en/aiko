from dataclasses import dataclass, field
from .user import User
from time import time
from uuid import uuid4
from aiko2.utils.estimate_tokens import estimate_tokens
from enum import Enum
from abc import ABC, abstractmethod

class ContentType(Enum):
    """
    Enum class to represent the content type of a message.
    """
    TEXT = "text"
    IMAGE = "image"
    VIDEO = "video"
    THOUGHT = "thought"


class MessagePart:
    """
    MessagePart class to represent base class for message parts.
    """

    @abstractmethod
    def to_dict(self) -> dict:
        """
        Convert the message part to a dictionary.

        Returns
        -------
        dict
            The dictionary representation of the message part.
        """
        pass

    


@dataclass
class TextPart(MessagePart):
    """
    TextPart class to represent a text part of a message.

    Attributes
    ----------
    text : str
        The text content of the message part.
    """
    text: str = ""

    def to_dict(self) -> dict:
        """
        Convert the message part to a dictionary.

        Returns
        -------
        dict
            The dictionary representation of the message part.
        """
        return {
            "type": ContentType.TEXT.value,
            "text": self.text
        }

    def __str__(self) -> str:
        """
        Return the string representation of the text part.

        Returns
        -------
        str
            The string representation of the text part.
        """
        return self.text
    
    def __repr__(self) -> str:
        """
        Return the string representation of the text part.

        Returns
        -------
        str
            The string representation of the text part.
        """
        return self.text
    
@dataclass
class ThoughtPart(MessagePart):
    """
    ThoughtPart class to represent a thought part of a message.

    Attributes
    ----------
    thought : str
        The thought content of the message part.
    """
    thought: str = ""

    def to_dict(self) -> dict:
        """
        Convert the message part to a dictionary.

        Returns
        -------
        dict
            The dictionary representation of the message part.
        """
        return {
            "type": ContentType.THOUGHT.value,
            "text": f"<think>{self.thought}</think>"
        }

    def __str__(self) -> str:
        """
        Return the string representation of the thought part.

        Returns
        -------
        str
            The string representation of the thought part.
        """
        return self.thought
    
    def __repr__(self) -> str:
        """
        Return the string representation of the thought part.

        Returns
        -------
        str
            The string representation of the thought part.
        """
        return self.thought

@dataclass
class Message:
    """
    Message class to represent a message.

    Attributes
    ----------
    content : str | list[MessagePart]
        The message content.
    user : User
        The user who sent the message.
    timestamp : str
        The timestamp of the message.
    id : str
        The message id.
    """

    # The message content.
    content: str | list[MessagePart] = field(default_factory=list)

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

    @property
    def message_text(self) -> str:
        """
        Return the text content of the message.

        Returns
        -------
        str
            The text content of the message.
        """
        if self.content is None:
            return ""
        
        if type(self.content) is list:
            return "\n".join([part.text for part in self.content if type(part) is TextPart])
        
        return self.content
        
    @message_text.setter
    def message_text(self, value: str):
        """
        Set the text content of the message.

        Parameters
        ----------
        value : str
            The text content of the message.
        """
        self.content = [TextPart(value)]

    @property
    def reasoning_text(self) -> str:
        """
        Return the reasoning text content of the message.

        Returns
        -------
        str
            The reasoning text content of the message.
        """
        if self.content is None:
            return ""
        
        if type(self.content) is list:
            return "\n".join([part.text for part in self.content if type(part) is ThoughtPart or type(part) is TextPart])
        
        if type(self.content) is str:
            return self.content
        
        return ""


    def add_text(self, text: str):
        """
        Add text content to the message.

        Parameters
        ----------
        text : str
            The text content to add to the message.
        """
        if type(self.content) is str:
            self.content = [TextPart(self.content)]

        if self.content is None:
            self.content = []
        
        self.content.append(TextPart(text))

    def add_thought(self, thought: str):
        """
        Add thought content to the message.

        Parameters
        ----------
        thought : str
            The thought content to add to the message.
        """
        if type(self.content) is str:
            self.content = [TextPart(self.content)]

        if self.content is None:
            self.content = []
        
        self.content.append(ThoughtPart(thought))
    
    def get_parts(self) -> list[MessagePart]:
        """
        Return the message parts.

        Returns
        -------
        list[MessagePart]
            The message parts.
        """
        if self.content is None:
            return []
        
        if type(self.content) is list:
            return self.content

        return [TextPart(self.content)]


    def __str__(self) -> str:
        """
        Return the string representation of the message.

        Returns
        -------
        str
            The string representation of the message.
        """
        return f"{self.user.name}: {self.message_text}"
    
    def __repr__(self) -> str:
        """
        Return the string representation of the message.

        Returns
        -------
        str
            The string representation of the message.
        """
        return f"{self.user.name}: {self.message_text}"
    
    def estimate_tokens(self) -> int:
        """
        Estimate the number of tokens in the message content.

        Returns
        -------
        int
            The estimated number of tokens in the message content.
        """
        return estimate_tokens(f"<{self.user.name}> {self.message_text}")

