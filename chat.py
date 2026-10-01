from pinecone import Pinecone
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv
import google.generativeai as genai
import time 

EMBED_MODEL = "models/gemini-embedding-001"
EMBED_DIMENSIONS = 768
CHAT_MODEL = "gemini-3.5-flash-lite"
PINECONE_INDEX_NAME = "website-chatbot"

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
pc = Pinecone(api_key=os.environ["PINECONE_API_KEY"])
pinecone_index = pc.Index(PINECONE_INDEX_NAME)

def retrieve_chunks(question, site_id, n_results=5):
    query_embedding = genai.embed_content(
        model=EMBED_MODEL,
        content=question,
        output_dimensionality=EMBED_DIMENSIONS,
    )["embedding"]

    results = pinecone_index.query(
        vector=query_embedding,
        top_k=n_results,
        namespace=site_id,
        include_metadata=True,
    )

    chunks = [match["metadata"]["text"] for match in results["matches"]]
    sources = [match["metadata"]["source_url"] for match in results["matches"]]

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

    for attempt in range(3):
        try:
            response = gemini_model.generate_content(prompt)
            return response.text
        except Exception as e:
            if "429" in str(e) and attempt < 2:
                time.sleep(5)
                continue
            raise

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
    port=int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
