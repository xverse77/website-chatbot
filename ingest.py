import os
import glob
from dotenv import load_dotenv
import google.generativeai as genai
from pinecone import Pinecone

CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
EMBED_MODEL = "models/gemini-embedding-001"
EMBED_DIMENSIONS = 768
PINECONE_INDEX_NAME = "website-chatbot"

load_dotenv()
genai.configure(api_key=os.environ["GEMINI_API_KEY"])
pc = Pinecone(api_key=os.environ["PINECONE_API_KEY"])
pinecone_index = pc.Index(PINECONE_INDEX_NAME)

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
    result=genai.embed_content(
        model=EMBED_MODEL,
        content=text,
        output_dimensionality=EMBED_DIMENSIONS,
    )
    return result["embedding"]

def ingest(site_id):
    data_dir = os.path.join("data", site_id)
    if not os.path.isdir(data_dir):
        raise SystemExit(f"No scraped data found at {data_dir}. Run crawler.py first.")

    files = glob.glob(os.path.join(data_dir, "*.txt"))
    print(f"Found {len(files)} documents for site '{site_id}'")

    total_chunks = 0
    for filepath in files:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        lines = content.split("\n", 3)
        source_url = lines[0].replace("SOURCE: ", "") if len(lines) > 0 else filepath
        title = lines[1].replace("TITLE: ", "") if len(lines) > 1 else os.path.basename(filepath)
        body = lines[3] if len(lines) > 3 else content

        chunks = chunk_text(body)
        vectors_to_upsert = []
        for i, chunk in enumerate(chunks):
            embedding = embed_text(chunk)
            chunk_id = f"{site_id}_{os.path.basename(filepath)}_{i}"
            vectors_to_upsert.append({
                "id": chunk_id,
                "values": embedding,
                "metadata": {"text": chunk, "source_url": source_url, "title": title},
            })
            total_chunks += 1

        pinecone_index.upsert(vectors=vectors_to_upsert, namespace=site_id)
        print(f"  [OK] {title} -> {len(chunks)} chunks")

    print(f"\nDone. {total_chunks} chunks embedded into Pinecone (namespace '{site_id}')")

if __name__ == "__main__":
    SITE_ID = "aps-college"
    ingest(SITE_ID)