import os
import glob
import chromadb
import ollama

CHUNK_SIZE = 500      # characters per chunk
CHUNK_OVERLAP = 50    # overlap between consecutive chunks
EMBED_MODEL = "nomic-embed-text"
CHROMA_PATH = "./chroma_db"

def chunk_text(text, chunk_size=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        start += chunk_size - overlap
    return chunks

def embed_text(text):
    response = ollama.embeddings(model=EMBED_MODEL, prompt=text)
    return response["embedding"]