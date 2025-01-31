from .retriever_storage import KnowledgeBase, MultiKnowledgeBase
from .nano_vector_store import NanoVectorStore
from .json_kv_store import SimpleJsonStore

# A simple, pre-built knowledge base that uses NanoVectorStore and SimpleJsonStore
class SimpleKnowledgeBase(KnowledgeBase):
    
    def __init__(self, path="./", dimension=100):
        nvs = NanoVectorStore(path, dimension)
        kv = SimpleJsonStore(path)
        super().__init__(nvs, kv, path)
        

def nvs_factory(path, dimension):
    return NanoVectorStore(path, dimension)

def kv_factory(path):
    return SimpleJsonStore(path)

class SimpleMultiKnowledgeBase(MultiKnowledgeBase):
    
    def __init__(self, path="./", dimension=100):
        super().__init__(path, None, nvs_factory, kv_factory, True)