"""
Vector Store for Semantic Memory (RAG).
Allows entities to recall past decisions based on semantic similarity.
"""

import json
import os
import numpy as np
from typing import List, Dict, Any, Tuple
from datetime import datetime

# Try to import sentence_transformers, fallback to simple overlap if not installed
try:
    from sentence_transformers import SentenceTransformer
    HAS_TRANSFORMERS = True
except ImportError:
    HAS_TRANSFORMERS = False
    print("⚠️ sentence-transformers not found. Using keyword overlap for RAG.")

class VectorStore:
    """
    Manages embeddings and semantic retrieval.
    """
    def __init__(self, storage_path: str = "vector_memory.json"):
        self.storage_path = storage_path
        self.documents: List[Dict[str, Any]] = []
        self.embeddings: Optional[np.ndarray] = None
        
        if HAS_TRANSFORMERS:
            # Load a lightweight model
            self.model = SentenceTransformer('all-MiniLM-L6-v2')
        else:
            self.model = None
            
        self._load_memory()

    def _load_memory(self):
        """Load memory from disk."""
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, 'r') as f:
                    data = json.load(f)
                    self.documents = data.get("documents", [])
                    # Re-compute embeddings if needed (for MVP we won't store numpy arrays to disk to keep it simple)
                    # In a real app, we'd use ChromaDB or FAISS which handles persistence
                    if self.documents and self.model:
                        texts = [doc["text"] for doc in self.documents]
                        self.embeddings = self.model.encode(texts)
            except Exception as e:
                print(f"⚠️ Error loading vector memory: {e}")

    def _save_memory(self):
        """Save memory to disk."""
        data = {
            "documents": self.documents,
            "updated_at": datetime.utcnow().isoformat()
        }
        with open(self.storage_path, 'w') as f:
            json.dump(data, f, indent=2)

    def add_memory(self, text: str, metadata: Dict[str, Any]):
        """Add a text chunk to memory."""
        doc = {
            "text": text,
            "metadata": metadata,
            "timestamp": datetime.utcnow().isoformat()
        }
        self.documents.append(doc)
        
        if self.model:
            embedding = self.model.encode([text])[0]
            if self.embeddings is None:
                self.embeddings = np.array([embedding])
            else:
                self.embeddings = np.vstack([self.embeddings, embedding])
        
        self._save_memory()
        print(f"🧠 [VECTOR] Memory added: '{text[:30]}...'")

    def search(self, query: str, top_k: int = 3) -> List[Tuple[Dict[str, Any], float]]:
        """
        Semantic search for relevant memories.
        Returns list of (document, score).
        """
        if not self.documents:
            return []
            
        if self.model and self.embeddings is not None:
            query_embedding = self.model.encode([query])[0]
            
            # Cosine similarity
            scores = np.dot(self.embeddings, query_embedding) / (
                np.linalg.norm(self.embeddings, axis=1) * np.linalg.norm(query_embedding)
            )
            
            # Get top k
            top_indices = np.argsort(scores)[::-1][:top_k]
            results = []
            for idx in top_indices:
                results.append((self.documents[idx], float(scores[idx])))
            return results
            
        else:
            # Fallback: Keyword overlap
            query_words = set(query.lower().split())
            results = []
            for doc in self.documents:
                doc_words = set(doc["text"].lower().split())
                score = len(query_words.intersection(doc_words)) / len(query_words) if query_words else 0
                results.append((doc, score))
            
            results.sort(key=lambda x: x[1], reverse=True)
            return results[:top_k]
