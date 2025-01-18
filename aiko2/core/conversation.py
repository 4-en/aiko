from dataclasses import dataclass, field
from .message import Message


@dataclass
class Conversation:
    """
    Conversation class to represent a conversation.

    Attributes
    ----------
    messages : list
        The list of messages in the conversation.
    """
    
    # The list of messages in the conversation.
    messages: list[Message] = field(default_factory=list)

    def add_message(self, message: Message):
        """
        Add a message to the conversation.
        
        Parameters
        ----------
        message : Message
            The message to be added.
        """
        self.messages.append(message)

    def get_last_messages(self, n: int):
        """
        Get the last n messages in the conversation.
        
        Parameters
        ----------
        n : int
            The number of messages to retrieve.
            If n is greater than the total number of messages,
            all messages will be returned.
            If n is less than or equal to 0, or the conversation is empty,
            an empty list will be returned.

        Returns
        -------
        list : list[Message]
            The list of the last n messages in the conversation.
        """
        if n <= 0 or not self.messages:
            return []
        
        if n >= len(self.messages):
            return self.messages
        
        return self.messages[-n:]
