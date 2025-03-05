from dataclasses import dataclass, field

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
            half_time = 730 # for always, we will adjust the decay function later, to keep a minimum value
        
        days_since = sec_since / 86400
        
        decay_rate = np.log(2) / half_time
        
        if self == TimeRelevance.ALWAYS:
            # we want to keep a minimum value for memories that are always relevant
            # we don't just return the value, because we want a soft ranking, even for always relevant memories
            # in a "real" brain, even if the memory is always relevant, newer/recently used memories should be more relevant
            # than older ones. This is to simulate that effect.
            # alternatively, we could implements a separate mechanism for this, which also tracks access frequency
            # TODO: consider implementing a separate mechanism for
            # tracking access frequency, to make always relevant memories
            # more relevant if they are accessed more frequently.
            return 0.8 * value + 0.2 * value * np.exp(-decay_rate * days_since)
        
        return value * np.exp(-decay_rate * days_since)
    
    @staticmethod
    def query_relevance(q_relevance: "TimeRelevance", q_time: float, m_relevance: "TimeRelevance", m_time: float, value: float=1.0) -> float:
        """
        Calculate the relevance of a query based on the time relevance of the query and the memory.
        
        Parameters
        ----------
        q_relevance : TimeRelevance
            The time relevance of the query.
        q_time : float
            The time of the query.
        m_relevance : TimeRelevance
            The time relevance of the memory.
        m_time : float
            The time of the memory.
        value : float, optional
            The value of the memory, by default 1.0
        """
        # we want to weight memories that are more relevant in time higher
        # if the q_relevance is ALWAYS, time difference should not or only barely matter
        # if the q_relevance is NOW, time difference should matter a lot
        # the m_relevance should also matter, but not as much as the q_relevance
        # think of m_relevance as a modifier for that memory.
        #
        # Example:
        # query: "Who was the president of the US in 2000?"
        # q_relevance: YEAR
        # q_time: some_timestamp_for_y2000
        # memory1: "Bill Clinton is the president of the US"
        # m_relevance: YEAR
        # m_time: some_timestamp_for_bill_clinton
        # memory2: "George Bush is the president of the US"
        # m_relevance: YEAR
        # m_time: some_timestamp_for_george_bush
        # memory3: "Joe Biden is the president of the US"
        # m_relevance: YEAR
        # m_time: some_timestamp_for_joe_biden
        #
        # Based on these memories, we would expect memory1 to be the most relevant, then memory2, then memory3.
        # The time difference between the query and the memory should be the most important factor.
        # for time_relevance, we should probably use the more sensitive time_relevance, so we can filter out memories that
        # are only relevant for a short time.
        # At the same time, if q_relevance was lower than m_relevance, we should also use the more sensitive time_relevance.
        
        relevance = min(q_relevance.value, m_relevance.value)
        relevance = TimeRelevance(relevance)
        time_diff = abs(q_time - m_time)
        return relevance.time_decay(value, time_diff)
        

import time

@dataclass
class Memory:
    """
    A class to represent a memory.
    This can include personal information about a person or general knowledge.
    """
    memory: str # The memory to store
    entities: list[str] # The entities
    topic: str # The topic of the memory
    time_relevance: TimeRelevance = TimeRelevance.ALWAYS
    truthfulness: float = 1.0 # The estimated truthfulness of the memory, 1.0 is probably completely true, 0.0 is probably completely false
    memory_age: float = 0 # The age of the memory in seconds (what it is about, not when it was created)
    source: str = "unknown" # The source of the memory, e.g. a person or a website
    creation_time: float = field(default_factory=time.time)
    