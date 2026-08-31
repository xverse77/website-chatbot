import os
import io
import time
from collections import deque
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from pypdf import PdfReader

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; SiteBot/1.0)"}
SKIP_EXTENSIONS = (".jpg", ".jpeg", ".png", ".gif", ".svg", ".css", ".js",
                   ".zip", ".mp4", ".mp3", ".ico", ".woff", ".woff2")


def is_same_domain(url, base_domain):
    return urlparse(url).netloc.replace("www.", "") == base_domain.replace("www.", "")


def clean_html_text(soup):
    for tag in soup(["script", "style", "nav", "footer", "header", "noscript"]):
        tag.decompose()
    text = soup.get_text(separator="\n")
    return "\n".join(line.strip() for line in text.splitlines() if line.strip())

def extract_pdf_text(content_bytes):
    reader = PdfReader(io.BytesIO(content_bytes))
    text = "\n".join(page.extract_text() or "" for page in reader.pages)
    return text

def crawl(start_url, site_id, max_pages=30, delay=0.5):
    base_domain = urlparse(start_url).netloc
    visited = set()
    queue = deque([start_url])
    documents = []

    out_dir = os.path.join("data", site_id)
    os.makedirs(out_dir, exist_ok=True)

    while queue and len(visited) < max_pages:
        url = queue.popleft()
        if url in visited:
            continue
        visited.add(url)

        try:
            resp = requests.get(url, headers=HEADERS, timeout=15)
            resp.raise_for_status()
            content_type = resp.headers.get("Content-Type", "")

            if "application/pdf" in content_type or url.lower().endswith(".pdf"):
                text = extract_pdf_text(resp.content)
                title = os.path.basename(urlparse(url).path)

            elif "text/html" in content_type:
                soup = BeautifulSoup(resp.text, "html.parser")
                title = soup.title.string.strip() if soup.title else url
                text = clean_html_text(soup)

                for link in soup.find_all("a", href=True):
                    next_url = urljoin(url, link["href"]).split("#")[0]
                    if (is_same_domain(next_url, base_domain)
                            and next_url not in visited
                            and not next_url.lower().endswith(SKIP_EXTENSIONS)):
                        queue.append(next_url)
            else:
                print(f"  [SKIP - unsupported type: {content_type}] {url}")
                continue

            if text.strip():
                documents.append({"url": url, "title": title, "text": text})
                print(f"  [OK] {url} ({len(text)} chars)")

        except Exception as e:
            print(f"  [FAILED] {url} — {e}")

        time.sleep(delay)

    return documents, out_dir
