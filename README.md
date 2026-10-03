# AI-Powered Website Query Chatbot

A Retrieval-Augmented Generation (RAG) chatbot that answers natural-language questions using a website's own content — fully cloud-hosted, zero local dependencies, zero running cost.

**Live demo:** https://xverse77.github.io/website-chatbot/index.html

---

## What it does

Ask it a question about a website in plain English, and it answers using only that website's actual content — pulling relevant information from scraped pages and PDFs, rather than guessing from general knowledge. If the answer isn't in the content, it says so instead of making something up.

## How it works

**Offline (run once per website):**
1. `crawler.py` — auto-discovers and scrapes a website's pages and PDFs
2. `ingest.py` — splits the content into chunks, embeds each one with Gemini, and stores the vectors in Pinecone

**Online (every question):**
3. The chat widget sends a question to the backend
4. `chat.py` embeds the question, retrieves the most relevant chunks from Pinecone, and asks Gemini to generate an answer grounded in that content
5. The answer — with source links — is returned to the widget

## Tech stack

| Layer | Technology |
|---|---|
| Crawling | Python — Requests, BeautifulSoup, pypdf |
| Embeddings | Google Gemini Embedding API |
| Vector database | Pinecone |
| Generation | Google Gemini API (`gemini-2.0-flash-lite`) |
| Backend | FastAPI, deployed on Render |
| Frontend | HTML / CSS / JavaScript, deployed on GitHub Pages |

The system is designed to be site-agnostic — pointing the crawler at a different URL and re-running ingestion lets the same codebase serve any website, keyed by `site_id`.

## Project structure

```
crawler.py       — scrapes a website into data/<site_id>/*.txt
ingest.py        — chunks + embeds content into Pinecone
chat.py          — FastAPI backend: retrieval + answer generation
index.html       — chat widget (frontend)
requirements.txt — Python dependencies for deployment
```

## Running it locally

```bash
python -m venv venv
venv\Scripts\Activate.ps1        # Windows
pip install -r requirements.txt
```

Create a `.env` file in the project root:
```
GEMINI_API_KEY=your_key_here
PINECONE_API_KEY=your_key_here
```

Scrape and index a site, then start the backend:
```bash
python crawler.py
python ingest.py
python chat.py
```
Open `index.html` in a browser to chat with it.

## Limitations

- Render's free tier sleeps after 15 minutes of inactivity; the first request after that takes 30–60 seconds to wake up
- Gemini's free tier enforces a request-rate limit, suitable for demonstration and light use
- Embedding on the question side must always use the same model/dimensions as ingestion, or retrieval breaks

## Status

Working end-to-end: scraping, retrieval, and generation have all been tested against a real college website, including correct refusals when an answer isn't present in the source content.
