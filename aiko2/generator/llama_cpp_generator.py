from .base_generator import BaseGenerator
from aiko2.core import Conversation, Message, User, Role

class LlamaCppGenerator(BaseGenerator):
    """Generator for local models that use the Llama C++ framework."""
    
    def __init__(self):
        self.assistant = User("Assistant", Role.ASSISTANT)
        
    
    def generate(self, conversation: Conversation) -> Message:
        """Generate a Llama C++ model from a conversation."""
        # TODO: Implement this method.
        return Message("This is a generated message.", self.assistant)
        
    