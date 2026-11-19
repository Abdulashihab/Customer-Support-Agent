from pathlib import Path

import chromadb
from chromadb.utils import embedding_functions

from src.rag.chunker import load_chunks

# The search database is stored in a folder in the main project folder.
CHROMA_DIR = Path(__file__).resolve().parents[2] / "chroma_db"
COLLECTION_NAME = "help_docs"
MODEL_NAME = "all-MiniLM-L6-v2"   # small, free model that turns text into numbers


def get_collection(reset=False):
    """Open the search database. With reset=True, start from an empty one."""
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    if reset:
        try:
            client.delete_collection(COLLECTION_NAME)
        except Exception:
            pass   # nothing to delete the first time
    embedder = embedding_functions.SentenceTransformerEmbeddingFunction(model_name=MODEL_NAME)
    return client.get_or_create_collection(name=COLLECTION_NAME, embedding_function=embedder)


def ingest():
    """Read all the chunks and store them in the search database."""
    chunks = load_chunks()
    collection = get_collection(reset=True)
    collection.add(
        ids=[c["id"] for c in chunks],
        documents=[c["text"] for c in chunks],
        metadatas=[
            {"source": c["source"], "title": c["title"], "section": c["section"]}
            for c in chunks
        ],
    )
    return len(chunks)


if __name__ == "__main__":
    count = ingest()
    print(f"Stored {count} chunks in {CHROMA_DIR}")