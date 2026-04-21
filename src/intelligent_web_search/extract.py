from __future__ import annotations

import re

from bs4 import BeautifulSoup
from markdownify import markdownify as to_markdown
from readability import Document

from .config import MAX_CONTENT_CHARS


WHITESPACE_RE = re.compile(r"\s+")


def normalize_text(text: str) -> str:
    text = WHITESPACE_RE.sub(" ", text or "").strip()
    return text[:MAX_CONTENT_CHARS]


def html_title(html: str) -> str:
    soup = BeautifulSoup(html, "lxml")
    if soup.title and soup.title.string:
        return normalize_text(soup.title.string)
    return ""


def extract_main_html(html: str) -> str:
    try:
        doc = Document(html)
        summary = doc.summary(html_partial=True)
        return summary or html
    except Exception:
        return html


def html_to_text_and_markdown(html: str) -> tuple[str, str]:
    main_html = extract_main_html(html)
    soup = BeautifulSoup(main_html, "lxml")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    text = normalize_text(soup.get_text(separator=" "))
    markdown = to_markdown(str(soup), heading_style="ATX")
    markdown = normalize_text(markdown)
    return text, markdown
