#!/usr/bin/env python
"""Challenge 0 — seed the CLM corpus.

1. Uploads the `data/` documents to Blob Storage.
2. Creates an Azure AI Search index and pushes the documents (with a semantic
   configuration) so the Foundry IQ knowledge base in Challenge 1 can ground the
   agents with cited answers.

Run:  python scripts/seed_corpus.py
"""
from __future__ import annotations

import sys
from pathlib import Path

# Make `clm_common` importable when run from the repo root.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from clm_common.config import settings, DATA_DIR, credential  # noqa: E402

CORPUS_DIRS = ["contract_templates", "clause_library", "policies", "counterparty_drafts"]


def _iter_docs():
    for sub in CORPUS_DIRS:
        for path in (DATA_DIR / sub).glob("*.md"):
            yield sub, path


def upload_to_blob() -> int:
    if not settings.storage_connection_string:
        print("· AZURE_STORAGE_CONNECTION_STRING not set — skipping blob upload.")
        return 0
    from azure.storage.blob import BlobServiceClient

    svc = BlobServiceClient.from_connection_string(settings.storage_connection_string)
    container = svc.get_container_client(settings.storage_container)
    try:
        container.create_container()
    except Exception:
        pass  # already exists

    count = 0
    for sub, path in _iter_docs():
        blob_name = f"{sub}/{path.name}"
        with path.open("rb") as fh:
            container.upload_blob(name=blob_name, data=fh, overwrite=True)
        count += 1
    print(f"  ✓ uploaded {count} documents to blob container '{settings.storage_container}'")
    return count


def build_search_index() -> int:
    if not settings.search_endpoint:
        print("· AZURE_SEARCH_ENDPOINT not set — skipping search index.")
        return 0

    from azure.search.documents import SearchClient
    from azure.search.documents.indexes import SearchIndexClient
    from azure.search.documents.indexes.models import (
        SearchIndex,
        SimpleField,
        SearchableField,
        SearchFieldDataType,
        SemanticConfiguration,
        SemanticPrioritizedFields,
        SemanticField,
        SemanticSearch,
    )

    cred = credential()
    index_name = settings.search_index

    fields = [
        SimpleField(name="id", type=SearchFieldDataType.String, key=True),
        SearchableField(name="title", type=SearchFieldDataType.String),
        SearchableField(name="content", type=SearchFieldDataType.String),
        SimpleField(name="source", type=SearchFieldDataType.String, filterable=True, facetable=True),
    ]
    semantic = SemanticSearch(
        configurations=[
            SemanticConfiguration(
                name="clm-semantic",
                prioritized_fields=SemanticPrioritizedFields(
                    title_field=SemanticField(field_name="title"),
                    content_fields=[SemanticField(field_name="content")],
                ),
            )
        ]
    )

    idx_client = SearchIndexClient(endpoint=settings.search_endpoint, credential=cred)
    idx_client.create_or_update_index(
        SearchIndex(name=index_name, fields=fields, semantic_search=semantic)
    )
    print(f"  ✓ index '{index_name}' created/updated (semantic config: clm-semantic)")

    docs = []
    for i, (sub, path) in enumerate(_iter_docs()):
        docs.append(
            {
                "id": f"doc-{i}",
                "title": path.stem.replace("_", " "),
                "content": path.read_text(encoding="utf-8"),
                "source": sub,
            }
        )
    search_client = SearchClient(endpoint=settings.search_endpoint, index_name=index_name, credential=cred)
    search_client.upload_documents(documents=docs)
    print(f"  ✓ indexed {len(docs)} documents")
    return len(docs)


def main() -> None:
    print("Seeding CLM corpus…")
    upload_to_blob()
    build_search_index()
    print("Done. Expected: documents in Blob + a populated 'clm-corpus' search index.")


if __name__ == "__main__":
    main()
