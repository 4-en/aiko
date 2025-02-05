from dataclasses import dataclass

from enum import Enum
import numpy as np

class TimeRelevance(Enum):
    """
    An enum to represent the relevance of a memory or query in time.
    """
    NOW = 1
    WEEK = 2
    MONTH = 3
    YEAR = 4
    ALWAYS = 5
    
    @staticmethod
    def from_string(time_relevance: str) -> 'TimeRelevance':
        """
        Get the TimeRelevance enum from a string.
        """
        time_relevance = time_relevance.upper()
        if time_relevance == "NOW":
            return TimeRelevance.NOW
        elif time_relevance == "WEEK":
            return TimeRelevance.WEEK
        elif time_relevance == "MONTH":
            return TimeRelevance.MONTH
        elif time_relevance == "YEAR":
            return TimeRelevance.YEAR
        elif time_relevance == "ALWAYS":
            return TimeRelevance.ALWAYS
        else:
            return TimeRelevance.ALWAYS
        
    def time_decay(self, value: float, sec_since: float) -> float:
        """
        Calculate the decayed value of a memory based on the time since the memory was created.
        """
        half_time = 1000
        # Half time is double the literal time relevance to include more
        # slightly older information if it's relevant enough.
        if self == TimeRelevance.NOW:
            half_time = 2
        elif self == TimeRelevance.WEEK:
            half_time = 14
        elif self == TimeRelevance.MONTH:
            half_time = 60
        elif self == TimeRelevance.YEAR:
            half_time = 730
        elif self == TimeRelevance.ALWAYS:
            half_time = 7300 # basically 20 years, probably doesn't do anything except slightly favor newer memories in edge cases
        
        days_since = sec_since / 86400
        
        decay_rate = np.log(2) / half_time
        
        return value * np.exp(-decay_rate * days_since)

@dataclass
class Memory:
    """
    A class to represent a memory.
    This can include personal information about a person or general knowledge.
    """
    memory: str # The memory to store
    person: str # The person the memory is about
    topic: str # The topic of the memory
    time_relevance: TimeRelevance = TimeRelevance.ALWAYS
    