from dataclasses import dataclass

@dataclass
class Memory:
    """
    A class to represent a memory.
    This can include personal information about a person or general knowledge.
    """
    memory: str # The memory to store
    person: str # The person the memory is about
    topic: str # The topic of the memory