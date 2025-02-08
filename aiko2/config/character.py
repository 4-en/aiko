from dataclasses import dataclass, field
from uuid import uuid4

@dataclass
class Character:
    """
    A class representing the configuration of a character.
    
    Attributes
    ----------
    name : str
        The name of the character.
    description : str
        The description of the character.
    image : str
        The image of the character.
    instruction : str
        The instruction for the character.
        This is the instruction used for the main generation process.
    eval_instruction : str
        The evaluation instruction for the character.
        This is the instruction used for the evaluation process.
        You can think of this as the instruction for the inner monologue of the character.
        If empty, the instruction will be used.
    style : list[float]
        Style embeddings for the character.
    domains : list[str]
        The domains of the character.
        These are the domains the character is associated with and can use to retrieve information.
    """
    
    name: str
    id: str = None
    description: str = ""
    image: str = ""

    instruction: str = ""
    eval_instruction: str = ""
    style: list[float] = field(default_factory=list)
    domains: list[str] = field(default_factory=list)

    def __post_init__(self):
        self.id = str(uuid4()) if self.id is None else self.id

    