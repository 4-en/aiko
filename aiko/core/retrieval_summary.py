from dataclasses import dataclass, field
from . import RetrievalResults

@dataclass
class RetrievalSummary:
    """
    A class representing a summary of a retrieval operation.
    
    Attributes
    ----------
    summary : str
        The summary of the retrieval operation.
    retrieval_results : RetrievalResults
        The retrieval results that were used to generate the summary.
    previous_summaries : list[str]
        The previous summaries that were used to generate the summary.
    """

    summary: str = ""
    retrieval_results: RetrievalResults = RetrievalResults()
    previous_summaries: list[str] = field(default_factory=list)
    


