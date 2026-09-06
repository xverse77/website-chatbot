import chromadb
import ollama
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv
import google.generativeai as genai

CHROMA_PATH = "./chroma_db"
EMBED_MODEL = "nomic-embed-text"
CHAT_MODEL = "gemini-3.6-flash" 

app = FastAPI()
load_dotenv()
genai.configure(api_key=os.environ["GEMINI_API_KEY"])
gemini_model = genai.GenerativeModel(CHAT_MODEL)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
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

    response = gemini_model.generate_content(prompt)
    return response.text

class ChatRequest(BaseModel):
    question: str
    site_id: str


@app.post("/api/chat")
def chat(request: ChatRequest):
    chunks, sources = retrieve_chunks(request.question, request.site_id)
    answer = generate_answer(request.question, chunks, sources)

    return {
        "answer": answer,
        "sources": list(set(sources)),
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
