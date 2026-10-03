"""Full PDF text extract for the worker."""

from __future__ import annotations

from dataclasses import dataclass

import pymupdf


@dataclass(frozen=True)
class PageText:
    page_number: int
    text: str


def extract_pdf_pages(path: str) -> list[PageText]:
    doc = pymupdf.open(path)
    try:
        pages: list[PageText] = []
        for index in range(doc.page_count):
            page = doc.load_page(index)
            pages.append(PageText(page_number=index + 1, text=page.get_text("text") or ""))
        return pages
    finally:
        doc.close()


def join_extractable_text(pages: list[PageText]) -> str:
    return "\n\n".join(page.text.strip() for page in pages if page.text.strip()).strip()
