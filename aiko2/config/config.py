from dataclasses import dataclass, field
from json import loads, dumps
import os

class ConfigClass:
    """
    A class that can be used to create a configuration object.
    Objects can be loaded from or saved to a file.
    Date in files is stored in the following schema:
    
    ```python
        # A comment
        key=value
        key2=[value1, value2] #json array
        key3={key4=value4, key5=value5} #json object
    ```
        
    All attributes starting with an underscore (_) are considered private and will not be saved or loaded.
    
    Attributes starting with an "cc_" are treated as comments and will be written to the file 
    as comments, but will not be loaded.
    If an attribute starting with "cc_" followed by the name of another attribute is found, 
    it will be treated as a comment for that attribute
    and will be written in the line before the attribute.
    
    Comments should either be a string or a callable that returns a string.
    
    Other attributes are considered public and will be saved and loaded.
    """
    
    def __init__(self, file_name="config.txt", attributes=None):
        """
        Initialize the configuration object.
        This can either be used by inheriting from this class or by creating an instance of this class and passing the attributes as a dictionary.

        Parameters
        ----------
        file_name : str, optional
            The name of the file to load the configuration from.
            If None, the default file name will be used.
        attributes : dict, optional
            A dictionary of attributes to initialize the configuration
        """
        super().__init__()
        
        self.__file_name = file_name
        if attributes:
            for key, value in attributes.items():
                if not hasattr(self, key):
                    setattr(self, key, value)
        
    def load(self, file_name, create_if_missing=True) -> object:
        """
        Load the configuration from the file.
        
        Parameters
        ----------
        file_name : str
            The name of the file to load the configuration from.
            If None, the default file name will be used.
        create_if_missing : bool, optional
            Whether to create a new file if the file does not exist. The default is True.
            
        Returns
        -------
        ConfigClass (or subclass)
            The configuration object itself.
        """
        fields = {}
        
        if hasattr(self, "__file_name"):
            file_name = file_name or self.__file_name or "config.txt"
        else:
            file_name = file_name or "config.txt"
            self.__file_name = file_name
            
        if not os.path.exists(file_name):
            if create_if_missing:
                print(f"File {file_name} does not exist. Creating a new one.")
                self.save(file_name)
            else:
                print(f"File {file_name} does not exist.")
            return self
            
        annotations = getattr(self, "__annotations__", {})
        has_annotations = bool(annotations)
        
        with open(file_name, "r") as file:
            for line in file:
                try:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    key, value = line.split("=", 1)
                    value = value.strip()
                    
                    if value.startswith("["):
                        value = loads(value)
                    elif value.startswith("{"):
                        value = loads(value)
                    else:
                        value_type = str
                        try:
                            # try to get a type annotation from the default value
                            if has_annotations and key in annotations:
                                value_type = annotations[key]
                            else:
                                value_type = type(getattr(self, key))
                                
                            if value_type == type(None):
                                # if we can't get the type from the default value, we try to guess it from the loaded value
                                # this is not 100% reliable, but it's better than nothing
                                if value == "None":
                                    value = None
                                elif value.lower() == "true" or value.lower() == "false":
                                    value_type = bool
                                elif value.isdigit():
                                    value_type = int
                                elif value.replace(".", "", 1).isdigit():
                                    value_type = float
                                else:
                                    value_type = str
                        except:
                            print(f"Error getting type for {key}")
                    
                        if value == None:
                            fields[key] = None
                        else:
                            if value_type == bool:
                                value = bool(value)
                            elif value_type == int:
                                value = int(value)
                            elif value_type == float:
                                value = float(value)
                            elif value_type == str:
                                value = str(value)
                                # replace any escaped newlines
                                value = value.replace("\\n", "\n")
                    fields[key] = value
                except Exception as e:
                    print(f"Error loading line: {line}")
                    print(e)
        for key, value in fields.items():
            if hasattr(self, key) and not key.startswith("_"):
                setattr(self, key, value)
                
        return self
        
        
    def save(self, file_name=None):
        """
        Save the configuration to the file.
        
        Parameters
        ----------
        file_name : str, optional
            The name of the file to save the configuration to.
            If None, the file name that was used to load will be used.
        """
        file_name = file_name or self.__file_name
        
        with open(file_name, "w") as file:
            for key, value in self.__dict__.items():
                try:
                    # skip private attributes
                    if key.startswith("_"):
                        continue
                    
                    # write comments at position if they don't belong to an attribute
                    if key.startswith("cc_"):
                        no_under = key[3:]
                        if not hasattr(self, no_under):
                            comment = value
                            if callable(comment):
                                comment = comment()
                            comment = str(comment)
                            for line in comment.split("\n"):
                                file.write(f"# {line}\n")
                        continue
                    
                    # write comments for attributes
                    comment = getattr(self, f"cc_{key}", None)
                    if comment:
                        if callable(comment):
                            comment = comment()
                        comment = str(comment)
                        for line in comment.split("\n"):
                            file.write(f"# {line}\n")
                    
                    # write the attribute
                    if isinstance(value, list) or isinstance(value, dict):
                        value = dumps(value)
                    elif isinstance(value, str):
                        # escape newlines
                        value = value.replace("\n", "\\n")
                    file.write(f"{key}={value}\n")
                    
                except Exception as e:
                    print(f"Error saving {key}")
                    print(e)
            
            
        

@dataclass
class Config(ConfigClass):
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
    
    
def config_test():
    import time
    class TestClass1(ConfigClass):
        def __init__(self):
            super().__init__()
            self.cc_start_comment = lambda: f"Configuration for the test assistant\nCreated on {time.ctime()}"
            self.name = "Test Assistant"
            self.description = "A test assistant."
            self.version = "0.1"
            self.nicknames = ["Testy", "Testo"]
            self.adress = {"street": "Test Street", "city": "Test City"}
            
            self.cc_name = "The name of the assistant"
            self.cc_description = "The description of the assistant"
            self.cc_version = "The version of the assistant"
        
    @dataclass
    class TestClass2(ConfigClass):
        cc_start_comment:callable = field(default_factory=lambda: f"Configuration for the test assistant\nCreated on {time.ctime()}")
        cc_name = "The name of the assistant"
        cc_description = "The description of the assistant"
        cc_version = "The version of the assistant"
        
        name: str = "Test Assistant"
        description: str = "A test assistant."
        version: str = "0.1"
        
    config1 = TestClass1()
    config1.name = "Test Assistant Changed"
    config1.description = "A test assistant changed."
    config1.version = "0.2"
    config1.nicknames = ["Testy", "Testo", "Testi"]
    config1.adress = {"street": "Test Street", "city": "Test City", "zip": "12345"}
    config2 = TestClass2()
    
    config1.save("test1.txt")
    config2.save("test2.txt")
    
    config3 = TestClass1()
    config3.load("test1.txt")
    
    assert config3.name == config1.name
    assert config3.description == config1.description
    assert config3.version == config1.version
    assert config3.nicknames == config1.nicknames
    assert config3.adress == config1.adress
    
    print("Config test passed.")
    
if __name__ == "__main__":
    config_test()