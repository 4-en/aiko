from dataclasses import dataclass

@dataclass
class Config:
    """
    Config class to represent the configuration of the assistant.

    Attributes
    ----------
    name : str
        The name of the assistant.
    description : str
        The description of the assistant.
    version : str
        The version of the assistant.
    """
    
    # The name of the assistant.
    name: str = "Aiko"
    
    # id of the assistant
    id: str = "aiko"
    
    # The description of the assistant.
    description: str = "An AI assistant."
    
    # The version of the assistant.
    version: str = "1.0"

    # The system instructions for the assistant.
    instructions: str = "You are a helpful assistent named Aiko. You are generally helpful, unless someone gives you a reason not to be, in which case you can be a bit sassy."

    # Maximum number of input characters.
    max_input_length: int = 4096

    # Length of window used to cut off tokens when len(tokens) > max_input_length
    cut_off_window: int = 2048

    # whether to log the conversations
    loggings: bool = False

    # where to log the conversations
    log_dir: str = "logs"
    
    # generator configs
    max_generated_tokens: int = 256
    temperature: float = 0.7
    top_k: int = 50
    top_p: float = 0.9
    
    # evaluator configs
    max_generated_queries: int = 3
    max_evaluation_input_messages: int = 5

    