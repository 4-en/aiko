from dataclasses import dataclass, field
import uuid

from enum import Enum
import numpy as np

_UNKNOWN_MULTIPLIER = 0.9

class TimeRelevance(Enum):
    """
    An enum to represent the relevance of a memory or query in time.
    """
    UNKNOWN = 0
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
        if time_relevance == "UNKNOWN":
            return TimeRelevance.UNKNOWN
        elif time_relevance == "NOW":
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
            return TimeRelevance.UNKNOWN
        
    
        
    def time_decay(self, value: float, sec_since: float) -> float:
        """
        Calculate the decayed value of a memory based on the time since the memory was created.
        """
        half_time = 1000
        # Half time is double the literal time relevance to include more
        # slightly older information if it's relevant enough.
        if self == TimeRelevance.UNKNOWN:
            # since we don't know the time relevance, we will use a default multiplier, instead of a decay function
            # this is slighly lower than a "perfect" relevance, to give a slight advantage to memories with known relevance
            return _UNKNOWN_MULTIPLIER * value
        elif self == TimeRelevance.NOW:
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
import math
from aiko.utils.ner import NER

@dataclass
class Memory:
    """
    A class to represent a memory.
    This can include personal information about a person or general knowledge.
    """
    memory: str # The memory to store
    entities: dict = field(default_factory=dict)
    topic: str = None # The topic of the memory
    time_relevance: TimeRelevance = TimeRelevance.ALWAYS
    truthfulness: float = 1.0 # The estimated truthfulness of the memory, 1.0 is probably completely true, 0.0 is probably completely false
    memory_time_point: float = field(default_factory=time.time) # The time the memory is about (not the time the memory was created)
    source: str = "unknown" # The source of the memory, e.g. a person or a website
    embedding: np.ndarray = None # The embedding of the memory
    creation_time: float = field(default_factory=time.time) # The time the memory was created
    last_access: float = field(default_factory=lambda: time()) # The last time this memory was accessed
    total_access_count: int = 0 # The total number of times this memory was accessed
    id: str = None # The ID of the memory

    # TODO: possible additional fields for future versions:
    # - access frequency / count / last access time
    # - avg / recent relevance (if a memory is often relevant for queries, it could be more relevant)
    # - references to other memories that often appear together with this memory

    def __post_init__(self):
        # add entities from memory string using NER

        if isinstance(self.entities, list):
            self.entities = {entity: 1 for entity in self.entities}
        elif isinstance(self.entities, dict):
            pass

        entities = NER.get_entities(self.memory)

        entities = [entity.lower() for entity in entities]
        for entity in entities:
            # find occurences of the entity in the memory
            i = 0
            occurences = 0
            while i != -1:
                i = self.memory.find(entity, i)
                if i != -1:
                    occurences += 1
                    i += 1
            occurences = max(1, occurences)
            self.entities[entity] += occurences

        if self.id is None:
            self.id = uuid.uuid4().hex

    def set_memory(self, memory: str):
        old_ner = NER.get_entities(self.memory)
        new_ner = NER.get_entities(memory)

        # remove entities that were in the old memory but not in the new one
        for entity in old_ner:
            if entity in self.entities:
                del self.entities[entity]

        # add entities that are in the new memory
        for entity in new_ner:
            i = 0
            occurences = 0
            while i != -1:
                i = memory.find(entity, i)
                if i != -1:
                    occurences += 1
                    i += 1
            occurences = max(1, occurences)
            self.entities[entity] += occurences

        self.memory = memory
        self.embedding = None

    
    def to_dict(self) -> dict:
        """
        Convert the memory to a dictionary ready to be stored in a database.
        
        Returns
        -------
        dict
            The dictionary representation of the memory, excluding the embedding.
        """

        # convert the numpy array to a list
        emb_accuracy = 5
        if self.embedding is not None:
            embedding = [round(val, emb_accuracy) if emb_accuracy > 0 else val for val in self.embedding]
        else:
            embedding = None

        return {
            "memory": self.memory,
            "entities": self.entities,
            "topic": self.topic,
            "time_relevance": self.time_relevance.name,
            "truthfulness": self.truthfulness,
            "memory_age": self.memory_time_point,
            "source": self.source,
            "creation_time": self.creation_time,
            "last_access": self.last_access,
            "total_access_count": self.total_access_count,
            "embedding": embedding,
            "id": self.id
        }
        
    @staticmethod
    def from_dict(memory_dict: dict, embedding: np.ndarray=None) -> 'Memory':
        """
        Create a memory from a dictionary.
        """
        if embedding is None:
            embedding = memory_dict.get("embedding", None)
            if embedding is not None:
                embedding = np.array(embedding)

        return Memory(
            memory=memory_dict["memory"],
            entities=memory_dict["entities"],
            topic=memory_dict["topic"],
            time_relevance=TimeRelevance[memory_dict["time_relevance"]],
            truthfulness=memory_dict["truthfulness"],
            memory_time_point=memory_dict["memory_age"],
            source=memory_dict["source"],
            embedding=embedding,
            creation_time=memory_dict["creation_time"],
            last_access=memory_dict["last_access"],
            total_access_count=memory_dict["total_access_count"],
            embedding=embedding,
            id=memory_dict["id"]
        )
        

    def get_access_score(self, current_time: float=None) -> float:

        # TODO: future improvements:
        # - keep track of average time between accesses, more spread out should be better when compared to more clustered accesses
        # - see Ebbinghaus forgetting curve for inspiration https://en.wikipedia.org/wiki/Forgetting_curve
        # - add importance factor. This could work by simply starting with a higher total_accesses, so that the memory is more important from the start
        # - use some kind of non-linear scaling for half-time, so that first accesses are more important than later ones

        if current_time is None:
            current_time = time()

        # calculate the score based on the time since last access and creation
        # the score should be higher if the memory was accessed recently and lower if it was accessed a long time ago
        # if the memory was accessed just now, the score should be 1.0

        time_since_access = current_time - self.last_access
        time_since_creation = current_time - self.creation
        
        # TODO: even for 1 access, the half-time is already much longer than 1 hours, so maybe fix this later
        min_half_time = 60 * 60 # one hour
        max_half_time = 60 * 60 * 24 * 30 * 12 # one year

        max_total_accesses = 100
        max_total_per_day = 0.1
        total_per_day = self.total_accesses / (time_since_creation / (60 * 60 * 24))
        # total_per_day *= 1000
        # true_total = min(1.0, (math.log( self.total_accesses + 5) - 1.5) / 3.0) # 0 to 1
        # true_total_per_day = min(1.0, (math.log( total_per_day + 5) - 1.5) / 3.0) # 0 to 1
        true_total = min(1.0, self.total_accesses / max_total_accesses)
        true_total_per_day = min(1.0, total_per_day / max_total_per_day)

        # calculate two half-lives, one for the time since last access and one for the time since creation
        # use higher half-life, as this allows to have a way to completely learn memories (when total accesses are >= max_total_accesses)

        total_scale = max(0.0, true_total, true_total_per_day)

        best_half_time = min_half_time + (max_half_time - min_half_time) * total_scale

        # apply half time to the time since last access
        access_score = math.exp(-time_since_access / best_half_time)

        return access_score
        
    
    def on_access(self, current_time: float=None, score: int = 1):
        if current_time is None:
            current_time = time()
        self.total_accesses += score
        self.last_access = current_time
    