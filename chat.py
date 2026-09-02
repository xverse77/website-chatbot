import chromadb
import ollama
from fastapi import FastAPI
from pydantic import BaseModel

CHROMA_PATH = "./chroma_db"
EMBED_MODEL = "nomic-embed-text"
CHAT_MODEL = "qwen3:8b"

app = FastAPI()
chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)

def retrieve_chunks(question, site_id, n_results=5):
    collection = chroma_client.get_collection(f"site_{site_id}")

    query_embedding = ollama.embeddings(model=EMBED_MODEL, prompt=question)["embedding"]

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results,
    )

    chunks = results["documents"][0]
    sources = [meta["source_url"] for meta in results["metadatas"][0]]

    return chunks, sources