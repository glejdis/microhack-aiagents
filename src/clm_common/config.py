"""Shared configuration for the Foundry CLM microhack.

Loads environment variables (from `.env` when present) and exposes a single
`settings` object plus small helpers so every challenge reads config the same
way. Import from any challenge with:

    from clm_common.config import settings
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

try:
    from dotenv import load_dotenv

    # Load the repo-root .env if it exists (search upward from CWD).
    load_dotenv()
except ImportError:  # dotenv is optional at runtime
    pass


# Repo root = two levels up from this file (src/clm_common/config.py).
REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = REPO_ROOT / "data"


def _get(name: str, default: str | None = None, required: bool = False) -> str | None:
    value = os.environ.get(name, default)
    if required and not value:
        raise RuntimeError(
            f"Missing required environment variable '{name}'. "
            f"Run Challenge 0's deploy script or copy .env.example → .env and fill it in."
        )
    return value


@dataclass(frozen=True)
class Settings:
    """Typed view over the microhack environment."""

    # Foundry project
    project_endpoint: str | None = field(default_factory=lambda: _get("AZURE_AI_PROJECT_ENDPOINT"))

    # Model deployments (multi-model fleet)
    model_orchestrator: str = field(default_factory=lambda: _get("MODEL_ORCHESTRATOR", "gpt-4.1"))
    model_drafting: str = field(default_factory=lambda: _get("MODEL_DRAFTING", "claude-sonnet-4-5"))
    model_clause_risk: str = field(default_factory=lambda: _get("MODEL_CLAUSE_RISK", "claude-sonnet-4-5"))
    model_renewal: str = field(default_factory=lambda: _get("MODEL_RENEWAL", "gpt-4o-mini"))

    # Grounding
    search_endpoint: str | None = field(default_factory=lambda: _get("AZURE_SEARCH_ENDPOINT"))
    search_index: str = field(default_factory=lambda: _get("AZURE_SEARCH_INDEX", "clm-corpus"))
    search_connection_name: str = field(default_factory=lambda: _get("AZURE_SEARCH_CONNECTION_NAME", "clm-search"))

    # Storage
    storage_connection_string: str | None = field(default_factory=lambda: _get("AZURE_STORAGE_CONNECTION_STRING"))
    storage_container: str = field(default_factory=lambda: _get("AZURE_STORAGE_CONTAINER", "clm-corpus"))

    # Observability
    appinsights_connection_string: str | None = field(
        default_factory=lambda: _get("APPLICATIONINSIGHTS_CONNECTION_STRING")
    )

    # Data plane
    sql_connection_string: str | None = field(default_factory=lambda: _get("AZURE_SQL_CONNECTION_STRING"))

    def require_project(self) -> str:
        """Return the project endpoint or raise a friendly error."""
        return _get("AZURE_AI_PROJECT_ENDPOINT", required=True)  # type: ignore[return-value]


settings = Settings()


def credential():
    """Return a DefaultAzureCredential (imported lazily so config has no hard SDK dep)."""
    from azure.identity import DefaultAzureCredential

    return DefaultAzureCredential()
