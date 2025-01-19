from dataclasses import dataclass
from uuid import uuid4

@dataclass
class User:
    """
    User class to represent a user.

    Attributes
    ----------
    name : str
        The user's name.
    role : str
        The user's role.
    id : str
        The user's id.
    """

    # The user's name.
    name: str

    # The user's role
    role: str = "USER"

    # The user's id
    id: str = None

    def __post_init__(self):
        """
        Initialize the user.
        """
        if not self.id:
            self.id = str(uuid4())
        if not self.role:
            self.role = "USER"

    def __str__(self) -> str:
        """
        Return the string representation of the user.

        Returns
        -------
        str
            The string representation of the user.
        """
        return self.name
    
    def __repr__(self) -> str:
        """
        Return the string representation of the user.

        Returns
        -------
        str
            The string representation of the user.
        """
        return self.name