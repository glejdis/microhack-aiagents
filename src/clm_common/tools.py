"""Shared function tools for CLM agents.

These plain Python functions become **Foundry function tools**: the Agents SDK
generates a JSON schema from the type hints + docstring, and the model calls
them during a run. Used by the Intake & Drafting agent (Ch1) and the Obligation
& Renewal agent (Ch4).

The contract-status lookup prefers Azure SQL (if AZURE_SQL_CONNECTION_STRING is
set) and otherwise falls back to data/contracts_seed.json so the hack works with
no database.
"""
from __future__ import annotations

import json
from datetime import date, datetime
from functools import lru_cache
from pathlib import Path
from typing import Any

from .config import DATA_DIR, settings


@lru_cache(maxsize=1)
def _seed() -> list[dict[str, Any]]:
    data = json.loads((DATA_DIR / "contracts_seed.json").read_text(encoding="utf-8"))
    return data["contracts"]


def _from_sql(contract_id: str) -> dict[str, Any] | None:
    import pyodbc

    conn = pyodbc.connect(settings.sql_connection_string)
    cur = conn.cursor()
    cur.execute(
        "SELECT contract_id, counterparty, type, status, effective_date, renewal_date, "
        "auto_renew, notice_days, risk, owner FROM dbo.contracts WHERE contract_id = ?",
        contract_id,
    )
    row = cur.fetchone()
    if not row:
        return None
    cols = [d[0] for d in cur.description]
    return {c: (v.isoformat() if isinstance(v, (date, datetime)) else v) for c, v in zip(cols, row)}


def get_contract_status(contract_id: str) -> str:
    """Look up a contract's status, renewal date, risk and owner by its ID.

    :param contract_id: The contract identifier, e.g. "CT-4821".
    :return: A JSON string with the contract's fields, or an error message if not found.
    """
    contract_id = (contract_id or "").strip().upper()
    record: dict[str, Any] | None = None
    if settings.sql_connection_string:
        try:
            record = _from_sql(contract_id)
        except Exception as exc:  # noqa: BLE001 — fall back to JSON on any DB error
            record = None
            note = f"(SQL lookup failed, used seed data: {exc})"
        else:
            note = "(source: Azure SQL)"
    else:
        note = "(source: contracts_seed.json)"

    if record is None:
        record = next((c for c in _seed() if c["contract_id"].upper() == contract_id), None)

    if record is None:
        known = ", ".join(c["contract_id"] for c in _seed())
        return json.dumps({"error": f"Contract '{contract_id}' not found.", "known_ids": known})

    return json.dumps({**record, "_note": note})


def list_upcoming_renewals(within_days: int = 90) -> str:
    """List contracts whose renewal date falls within the next N days.

    :param within_days: Look-ahead window in days (default 90).
    :return: A JSON string with a list of contracts sorted by renewal date.
    """
    today = date.today()
    rows = []
    for c in _seed():
        try:
            rdate = datetime.strptime(c["renewal_date"], "%Y-%m-%d").date()
        except (KeyError, ValueError):
            continue
        delta = (rdate - today).days
        if 0 <= delta <= within_days:
            rows.append({**c, "days_until_renewal": delta})
    rows.sort(key=lambda r: r["days_until_renewal"])
    return json.dumps({"within_days": within_days, "count": len(rows), "contracts": rows})
