from abc import ABC, abstractmethod

class BasePipeline(ABC):
    """
    Base class for all pipelines.
    This class controls the retrieval and generation process.
    At minimum, the pipeline takes an input query and returns a response.
    """

    @abstractmethod
    def query(self, query: str) -> str:
        """
        Query the pipeline with a given input and return a response.
        """
        pass

    def __call__(self, query: str) -> str:
        """
        Allow the pipeline to be called as a function.
        """
        return self.query(query)