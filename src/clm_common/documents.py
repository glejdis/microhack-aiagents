"""Shared document-reading helpers for the CLM microhack.

The corpus mixes Contoso-authored Markdown (templates, clause library, policy)
with **PDF** contract documents (executed contracts + inbound counterparty
drafts). `read_document_text` returns plain text for either, so the seeding
script and the Clause & Risk agent can treat every document the same way.
"""
from __future__ import annotations

from pathlib import Path


def read_document_text(path: str | Path) -> str:
    """Return the plain text of a corpus document.

    - `.md` / `.txt` / `.markdown` are read directly as UTF-8.
    - `.pdf` is text-extracted with **pypdf** (install: `pip install pypdf`).
    """
    path = Path(path)
    suffix = path.suffix.lower()

    if suffix == ".pdf":
        try:
            from pypdf import PdfReader
        except ImportError as exc:  # pragma: no cover - dependency hint
            raise RuntimeError(
                "Reading PDF documents requires 'pypdf'. Install it with "
                "`pip install pypdf` (it is listed in requirements.txt)."
            ) from exc

        reader = PdfReader(str(path))
        pages = [(page.extract_text() or "") for page in reader.pages]
        return "\n".join(pages).strip()

    return path.read_text(encoding="utf-8")
