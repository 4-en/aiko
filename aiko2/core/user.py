from dataclasses import dataclass

@dataclass
class User:
    """
    User class to represent a user.

    Attributes
    ----------
    name : str
        The user's name.
    id : str
        The user's id.
    role : str
        The user's role.
        Usually one of: 'user', 'assistant', 'system'
    """

    # The user's name.
    name: str

    # The user's id
    id: str

    # The user's role
    role: str