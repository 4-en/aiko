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
    instructions: str = "You are a helpful AI assistant. Please provide useful information to the user."

    # Maximum number of input characters.
    max_input_length: int = 4096

    # Length of window used to cut off tokens when len(tokens) > max_input_length
    cut_off_window: int = 2048

    # whether to log the conversations
    loggings: bool = False

    # where to log the conversations
    log_dir: str = "logs"
    
    # llm configs
    max_generated_tokens: int = 256
    temperature: float = 0.7
    top_k: int = 50
    top_p: float = 0.9

    