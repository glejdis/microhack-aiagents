#!/usr/bin/env python
"""Challenge 0 — seed the CLM corpus from SharePoint.

The original contract PDFs (executed contracts, approved templates, clause
library, policy, and inbound counterparty drafts) live in a **SharePoint
document library** — the corpus source of truth. This script wires that library
into Foundry IQ by creating, in Azure AI Search:

1. a **SharePoint Online data source** that connects to the library (app-only
   Microsoft Entra auth),
2. the **`clm-corpus` index** (semantic configuration `clm-semantic`), and
3. an **indexer** that crawls the library, extracts text + metadata, and
   populates the index.

Foundry IQ (Challenge 1) then grounds the agents on that index with cited
answers — no document upload happens here; SharePoint stays the system of
record. Populate the library first (bring-your-own), then run:

    python scripts/seed_corpus.py

Prerequisites (see the Challenge 0 README):
    - A SharePoint site + document library holding the corpus PDFs, arranged in
      the subfolders below.
    - A Microsoft Entra app registration (Graph app-only: Sites.Read.All /
      Files.Read.All, admin-consented) whose id/secret authorize the indexer.
    - .env values: SHAREPOINT_SITE_URL, SHAREPOINT_DOC_LIBRARY,
      SHAREPOINT_APP_ID, SHAREPOINT_APP_SECRET, SHAREPOINT_TENANT_ID.

Note: the Azure AI Search SharePoint Online indexer is a preview feature. If
your search SDK/service rejects the `sharepoint` data-source type, install a
preview `azure-search-documents` build (or create the data source in the portal)
and re-run.
"""
from __future__ import annotations

import sys
from pathlib import Path

# Make `clm_common` importable when run from the repo root.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from clm_common.config import settings, credential  # noqa: E402

# The corpus subfolders expected inside the SharePoint document library (they
# mirror the local `challenge-0/data/` layout the PDFs are authored from):
# contract_templates, clause_library, policies, contracts, counterparty_drafts,
# playbooks. The indexer crawls the whole library, so nested folders are fine.
DATA_SOURCE_NAME = "clm-corpus-sharepoint"
INDEXER_NAME = "clm-corpus-indexer"


def _sharepoint_connection_string() -> str | None:
    """Build the SharePoint Online data-source connection string (app auth)."""
    site = settings.sharepoint_site_url
    app_id = settings.sharepoint_app_id
    secret = settings.sharepoint_app_secret
    tenant = settings.sharepoint_tenant_id
    if not (site and app_id and secret and tenant):
        return None
    return (
        f"SharePointOnlineEndpoint={site};"
        f"ApplicationId={app_id};"
        f"ApplicationSecret={secret};"
        f"TenantId={tenant}"
    )


def create_index() -> None:
    """Create/update the clm-corpus index (fields the SharePoint indexer fills)."""
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

    fields = [
        # Key = the SharePoint item id (base64-encoded via an indexer mapping).
        SimpleField(name="id", type=SearchFieldDataType.String, key=True),
        SearchableField(name="title", type=SearchFieldDataType.String),
        SearchableField(name="content", type=SearchFieldDataType.String),
        SimpleField(name="source", type=SearchFieldDataType.String, filterable=True, facetable=True),
        SimpleField(name="url", type=SearchFieldDataType.String),
        SimpleField(
            name="last_modified",
            type=SearchFieldDataType.DateTimeOffset,
            filterable=True,
            sortable=True,
        ),
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

    idx_client = SearchIndexClient(endpoint=settings.search_endpoint, credential=credential())
    idx_client.create_or_update_index(
        SearchIndex(name=settings.search_index, fields=fields, semantic_search=semantic)
    )
    print(f"  ✓ index '{settings.search_index}' created/updated (semantic config: clm-semantic)")


def create_sharepoint_indexer() -> bool:
    """Create the SharePoint data source + indexer that populates the index."""
    conn = _sharepoint_connection_string()
    if not conn:
        print(
            "· SharePoint settings not set — skipping the SharePoint indexer.\n"
            "  Set SHAREPOINT_SITE_URL / SHAREPOINT_DOC_LIBRARY / SHAREPOINT_APP_ID /\n"
            "  SHAREPOINT_APP_SECRET / SHAREPOINT_TENANT_ID in .env (see challenge-0 README)."
        )
        return False

    from azure.search.documents.indexes import SearchIndexerClient
    from azure.search.documents.indexes.models import (
        SearchIndexerDataSourceConnection,
        SearchIndexerDataContainer,
        SearchIndexer,
        FieldMapping,
        FieldMappingFunction,
        IndexingParameters,
        IndexingParametersConfiguration,
    )

    client = SearchIndexerClient(endpoint=settings.search_endpoint, credential=credential())

    # Target the default document library ("Documents"/"Shared Documents") or a
    # named library via a crawl query.
    lib = (settings.sharepoint_doc_library or "").strip()
    if lib in ("", "Documents", "Shared Documents"):
        container = SearchIndexerDataContainer(name="defaultSiteLibrary")
    else:
        include = f"{settings.sharepoint_site_url.rstrip('/')}/{lib}"
        container = SearchIndexerDataContainer(name="useQuery", query=f"includeLibrary={include}")

    data_source = SearchIndexerDataSourceConnection(
        name=DATA_SOURCE_NAME,
        type="sharepoint",
        connection_string=conn,
        container=container,
    )
    client.create_or_update_data_source_connection(data_source)
    print(f"  ✓ SharePoint data source '{DATA_SOURCE_NAME}' created/updated")

    # Map SharePoint item metadata into the clm-corpus fields. The key is the
    # base64-encoded SharePoint item id; content is the extracted document text.
    field_mappings = [
        FieldMapping(
            source_field_name="metadata_spo_site_library_item_id",
            target_field_name="id",
            mapping_function=FieldMappingFunction(name="base64Encode"),
        ),
        FieldMapping(source_field_name="metadata_spo_item_name", target_field_name="title"),
        FieldMapping(source_field_name="metadata_spo_item_path", target_field_name="source"),
        FieldMapping(source_field_name="metadata_spo_item_weburi", target_field_name="url"),
        FieldMapping(source_field_name="metadata_spo_item_last_modified", target_field_name="last_modified"),
    ]

    indexer = SearchIndexer(
        name=INDEXER_NAME,
        data_source_name=DATA_SOURCE_NAME,
        target_index_name=settings.search_index,
        field_mappings=field_mappings,
        parameters=IndexingParameters(
            configuration=IndexingParametersConfiguration(
                data_to_extract="contentAndMetadata",
                parsing_mode="default",
            )
        ),
    )
    client.create_or_update_indexer(indexer)
    print(f"  ✓ indexer '{INDEXER_NAME}' created/updated")

    client.run_indexer(INDEXER_NAME)
    print(f"  ✓ indexer '{INDEXER_NAME}' run started — crawling the SharePoint library")
    return True


def build_search_index() -> None:
    if not settings.search_endpoint:
        print("· AZURE_SEARCH_ENDPOINT not set — skipping search index.")
        return
    create_index()
    create_sharepoint_indexer()


def main() -> None:
    print("Seeding CLM corpus from SharePoint…")
    build_search_index()
    print(
        "Done. Expected: the 'clm-corpus' index populated by the SharePoint "
        "indexer (check the indexer run status in the Azure portal)."
    )


if __name__ == "__main__":
    main()
