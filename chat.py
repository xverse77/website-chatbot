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

    documents = results["documents"] or [[]]
    metadatas = results["metadatas"] or [[]]

    chunks = documents[0]
    sources = [meta["source_url"] for meta in metadatas[0]]
    return chunks, sources

def generate_answer(question, chunks, sources):
    context = "\n\n".join(
        f"[Source: {src}]\n{chunk}" for chunk, src in zip(chunks, sources)
    )

    prompt = f"""You are a helpful assistant answering questions about a website, using only the context provided below.

Context:
{context}

Question: {question}

Instructions:
- Answer using ONLY the information in the context above.
- If the answer isn't in the context, say you don't have that information — do not make anything up.
- Keep your answer concise and directly relevant to the question.

Answer:"""

    response = ollama.chat(
        model=CHAT_MODEL,
        messages=[{"role": "user", "content": prompt}],
    )

    return response["message"]["content"]

