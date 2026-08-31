import os
import glob
import chromadb
import ollama

CHUNK_SIZE = 500      # characters per chunk
CHUNK_OVERLAP = 50    # overlap between consecutive chunks
EMBED_MODEL = "nomic-embed-text"
CHROMA_PATH = "./chroma_db"