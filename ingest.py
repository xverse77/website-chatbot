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

def ingest(site_id):
    data_dir = os.path.join("data", site_id)
    if not os.path.isdir(data_dir):
        raise SystemExit(f"No scraped data found at {data_dir}. Run crawler.py first.")

    client = chromadb.PersistentClient(path=CHROMA_PATH)
    collection_name = f"site_{site_id}"

    try:
        client.delete_collection(collection_name)
    except Exception:
        pass
    collection = client.create_collection(collection_name)

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
        for i, chunk in enumerate(chunks):
            embedding = embed_text(chunk)
            chunk_id = f"{os.path.basename(filepath)}_{i}"
            collection.add(
                ids=[chunk_id],
                embeddings=[embedding],
                documents=[chunk],
                metadatas=[{"source_url": source_url, "title": title}],
            )
            total_chunks += 1

        print(f"  [OK] {title} -> {len(chunks)} chunks")

    print(f"\nDone. {total_chunks} chunks embedded into collection '{collection_name}'")  

if __name__ == "__main__":
    SITE_ID = "aps-college"
    ingest(SITE_ID)