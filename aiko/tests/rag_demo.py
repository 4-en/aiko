import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

# Load Sentence Transformer Model for embeddings
model = SentenceTransformer("all-MiniLM-L6-v2")

# Knowledge Base (stores document text)
documents = []

# FAISS Index for fast vector search (HNSW for real-time updates)
dimension = model.get_sentence_embedding_dimension()
index = faiss.IndexHNSWFlat(dimension, 32)  # HNSW for efficient nearest neighbor search


class Retriever:
    """Custom retriever with FAISS"""
    
    def __init__(self, index, knowledge_base, model):
        self.index = index
        self.knowledge_base = knowledge_base
        self.model = model

    def add_document(self, text):
        """Add new knowledge dynamically to FAISS"""
        embedding = np.array([self.model.encode(text)]).astype('float32')
        self.index.add(embedding)  # Add new knowledge without reindexing
        self.knowledge_base.append(text)  # Store original text
        print(f"✅ New document added: {text}")

    def retrieve(self, query, top_k=2):
        """Perform vector-based retrieval"""
        query_embedding = np.array([self.model.encode(query)]).astype('float32')
        distances, indices = self.index.search(query_embedding, top_k)
        
        results = []
        for j, i in enumerate(indices[0]):
            if i < len(self.knowledge_base):  # Ensure index is valid
                results.append((self.knowledge_base[i], distances[0][j]))
        
        return results


# Initialize the Retriever
retriever = Retriever(index, documents, model)

# Add Initial Knowledge
initial_docs = [
    "Machine learning is a subset of artificial intelligence.",
    "Neural networks are a type of machine learning algorithm.",
    "Redis is a powerful in-memory database for fast data retrieval."
]

for doc in initial_docs:
    retriever.add_document(doc)

# Query Function
def query_flashrag(query):
    results = retriever.retrieve(query)
    print("\n🔍 Query Results:")
    for doc, score in results:
        print(f"- {doc} (Similarity: {score:.4f})")


# Example Usage
print("\nBefore Adding New Knowledge:")
query_flashrag("What is machine learning?")

# Add new knowledge dynamically
retriever.add_document("Deep learning is a subset of machine learning that uses neural networks.")

print("\nAfter Adding New Knowledge:")
query_flashrag("What is deep learning?")