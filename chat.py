import chromadb
import ollama
from fastapi import FastAPI
from pydantic import BaseModel

CHROMA_PATH = "./chroma_db"
EMBED_MODEL = "nomic-embed-text"
CHAT_MODEL = "qwen3:8b"

app = FastAPI()
chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)

