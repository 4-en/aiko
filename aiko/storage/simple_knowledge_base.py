from .retriever_storage import KnowledgeBase, MultiKnowledgeBase
from .nano_vector_store import NanoVectorStore
from .json_kv_store import SimpleJsonStore

import os

# A simple, pre-built knowledge base that uses NanoVectorStore and SimpleJsonStore
class SimpleKnowledgeBase(KnowledgeBase):
    
    def __init__(self, path="./", dimension=384):
        nvs = NanoVectorStore(os.path.join(path, "vectors"), dimension)
        kv = SimpleJsonStore(os.path.join(path, "kv"))
        super().__init__(kv, nvs)
        

def nvs_factory(path, dimension):
    return NanoVectorStore(path, dimension)

def kv_factory(path):
    return SimpleJsonStore(path)

class SimpleMultiKnowledgeBase(MultiKnowledgeBase):
    
    def __init__(self, path="./", dimension=384):
        super().__init__(path, None, nvs_factory, kv_factory, True, dimension=dimension)