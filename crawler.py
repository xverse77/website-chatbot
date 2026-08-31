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

