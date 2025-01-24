# some simple functions and classes to easily store and retrieve data

import os

def save_text(text:str, filename:str):
    """
    Save a text to a file.
    
    Parameters
    ----------
    text : str
        The text to save.
    filename : str
        The filename to save the text to.
    """
    if not os.path.exists(os.path.dirname(filename)):
        os.makedirs(os.path.dirname(filename))
        
    with open(filename, "w") as f:
        f.write(text)
        
def load_text(filename:str) -> str:
    """
    Load a text from a file.
    
    Parameters
    ----------
    filename : str
        The filename to load the text from.
    
    Returns
    -------
    str
        The loaded text.
    """
    
    if not os.path.exists(filename):
        raise FileNotFoundError(f"File {filename} not found.")
    
    with open(filename, "r") as f:
        return f.read()
    
import json

def save_json(data:dict, filename:str):
    """
    Save a JSON object to a file.
    
    Parameters
    ----------
    data : dict
        The JSON object to save.
    filename : str
        The filename to save the JSON object to.
    """
    if not os.path.exists(os.path.dirname(filename)):
        os.makedirs(os.path.dirname(filename))
        
    with open(filename, "w") as f:
        json.dump(data, f, indent=4)
        
def load_json(filename:str) -> dict:
    """
    Load a JSON object from a file.
    
    Parameters
    ----------
    filename : str
        The filename to load the JSON object from.
    
    Returns
    -------
    dict
        The loaded JSON object.
    """
    
    if not os.path.exists(filename):
        raise FileNotFoundError(f"File {filename} not found.")
    
    with open(filename, "r") as f:
        return json.load(f)
    
def save_list(data:list, filename:str):
    """
    Save a list to a file.
    
    Parameters
    ----------
    data : list
        The list to save.
    filename : str
        The filename to save the list to.
    """
    if not os.path.exists(os.path.dirname(filename)):
        os.makedirs(os.path.dirname(filename))
        
    with open(filename, "w") as f:
        for item in data:
            f.write(f"{item}\n")
            
def load_list(filename:str) -> list:
    """
    Load a list from a file.
    
    Parameters
    ----------
    filename : str
        The filename to load the list from.
    
    Returns
    -------
    list
        The loaded list.
    """
    
    if not os.path.exists(filename):
        raise FileNotFoundError(f"File {filename} not found.")
    
    with open(filename, "r") as f:
        return [line.strip() for line in f.readlines()]