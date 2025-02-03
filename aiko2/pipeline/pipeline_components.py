# from .pipeline import Pipeline, BasePipeline
from aiko2.config import Config
from abc import ABC, abstractmethod
from aiko2.core import Memory
import os

class MemoryHandler(ABC):
    """
    An abstract class that defines the interface for memory handlers.
    Memory handlers are used to store data from components that can be used for future training or analysis.
    """

    @abstractmethod
    def add_memory(self, memory: Memory, domain: str):
        """
        Add memory to the memory handler.

        Parameters
        ----------
        memory : Memory
            The memory object
        domain : str
            The domain of the memory
            This is used to group memories together, for example for different
            users. When retrieving memories, you can specify the domain to
            retrieve memories from, or you can retrieve all memories.

        """
        pass

    def save(self):
        """
        Save the memory handler before shutting down the pipeline.
        """
        pass

    def _set_pipeline(self, pipeline):
        """
        Set the pipeline object.

        This method is called by the pipeline object to set itself

        Parameters
        ----------
        pipeline : Pipeline
            The pipeline object
        """
        pass

class ComponentMixin:
    """
    A mixin class that provides a reference to the pipeline object
    and the config object. This is useful for components that need
    to access the pipeline object and the config object.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._pipeline = None

    def _set_pipeline(self, pipeline):
        """
        Set the pipeline object.

        This method is called by the pipeline object to set itself
        
        Parameters
        ----------
        pipeline : Pipeline
            The pipeline object
        """
        self._pipeline = pipeline

    def get_pipeline(self):
        """
        Get the pipeline object.
        
        Returns
        -------
        Pipeline
            The pipeline object
        """
        return self._pipeline

    def get_config(self) -> Config:
        """
        Get the config object.

        Returns
        -------
        Config
            The config object
        """
        if not self._pipeline:
            raise ValueError("Pipeline object is not set")
        return self._pipeline.get_config()
    
    def get_config_value(self, key: str, default: any=None) -> any:
        """
        Get the value of a key in the config object.
        
        Parameters
        ----------
        key : str
            The key
        default : any, optional
            The default value to return if the key does not exist, by default None
            
        Returns
        -------
        any
            The value of the key
        """
        return getattr(self.get_config(), key, default)
    
    def set_config_value(self, key: str, value: any):
        """
        Set the value of a key in the config object.
        
        Parameters
        ----------
        key : str
            The key
        value : any
            The value to set
        """
        setattr(self.get_config(), key, value)

    def get_root_dir(self) -> str:
        """
        Get the root directory of the pipeline.
        
        Returns
        -------
        str
            The root directory
        """
        if not self._pipeline:
            raise ValueError("Pipeline object is not set")
        return self.get_pipeline().get_root_dir()
    
    def get_data_dir(self) -> str:
        """
        Get the data directory of the pipeline.

        Returns
        -------
        str
            The data directory
        """
        if not self._pipeline:
            raise ValueError("Pipeline object is not set")
        return self.get_pipeline().get_data_dir()
    
    def get_config_dir(self) -> str:
        """
        Get the config directory of the pipeline.

        Returns
        -------
        str
            The config directory
        """
        if not self._pipeline:
            raise ValueError("Pipeline object is not set")
        return self.get_pipeline().get_config_dir()
    
    def getenv(self, var: str) -> str:
        """
        Get an environment variable or raise an error if it is missing.
        
        Parameters
        ----------
        var : str
            The environment variable that is missing
        """
        val = os.getenv(var)
        
        if val and val.strip() != "":
            return val
        
        root = self.get_root_dir()
        env_file = os.path.join(root, ".env")
        
        contents = []
        if os.path.exists(env_file):
            with open(env_file, 'r') as f:
                contents = f.readlines()
                
        # check if the variable is already in the file
        found = False
        for line in contents:
            if line.startswith(var):
                found = True
                break
            
        if not found:
            contents.append(f"{var}= \n")
            with open(env_file, 'w') as f:
                for line in contents:
                    if not line.endswith("\n"):
                        line += "\n"
                    f.write(line)
                
        raise ValueError(f"Missing environment variable {var}. Set the {var} environment variable in {env_file}")
    
import os
class LoggingMixin:
    """
    A mixin class that provides logging functionality.
    
    Used to store data from components that can be used for future training or analysis.

    Class needs to have a self.get_root_dir() method to work.

    TODO: implement this class

    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._log = []

    def log(self, data: any):
        """
        Log data.

        Parameters
        ----------
        data : any
            The data to log
        """
        self._log.append(data)

    def save_log(self, filename: str):
        """
        Save the log to a file.

        Parameters
        ----------
        filename : str
            The filename to save the log to
        """
        with open(os.path.join(self.get_root_dir(), filename), 'w') as f:
            for data in self._log:
                f.write(str(data) + '\n')



