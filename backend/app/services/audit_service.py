"""Transactional audit ledger write and verification path.

Every new audit row is assigned a tenant/platform-scoped sequence and a
SHA-256 hash chained to the previous ledger row. A PostgreSQL transaction
advisory lock serializes sequence allocation per ledger scope; the database
trigger prevents UPDATE/DELETE of hashed rows.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.privacy import redact_sensitive_data
from app.models.audit_log import AuditLog

GENESIS_HASH = hashlib.sha256(b"AI-EMPLOYEE-AUDIT-LEDGER-V1").hexdigest()
PLATFORM_SCOPE = "__platform__"


def _scope(tenant_id: UUID | str | None) -> str:
    return str(tenant_id) if tenant_id is not None else PLATFORM_SCOPE


def _lock_key(scope: str) -> int:
    # PostgreSQL advisory locks use a signed 64-bit application-defined key.
    return int.from_bytes(hashlib.sha256(scope.encode("utf-8")).digest()[:8], "big", signed=True)


def _canonical_payload(entry: AuditLog) -> str:
    payload = {
        "id": str(entry.id),
        "tenant_id": str(entry.tenant_id) if entry.tenant_id is not None else None,
        "actor_type": entry.actor_type,
        "actor_id": str(entry.actor_id) if entry.actor_id is not None else None,
        "action": entry.action,
        "resource_type": entry.resource_type,
        "resource_id": entry.resource_id,
        "request_id": entry.request_id,
        "status": entry.status,
        "metadata": entry.metadata_ or {},
        "created_at": entry.created_at.astimezone(timezone.utc).isoformat(),
        "ledger_scope": entry.ledger_scope,
        "ledger_sequence": entry.ledger_sequence,
        "previous_hash": entry.previous_hash,
    }
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str)


def _compute_entry_hash(entry: AuditLog) -> str:
    return hashlib.sha256(_canonical_payload(entry).encode("utf-8")).hexdigest()


async def record(
    db: AsyncSession,
    *,
    action: str,
    actor_type: str = "user",
    actor_id: UUID | str | None = None,
    tenant_id: UUID | str | None = None,
    resource_type: str | None = None,
    resource_id: str | None = None,
    status: str = "success",
    request_id: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> AuditLog:
    """Insert one immutable ledger entry.

    This is intentionally transactional: if the ledger cannot be written,
    the caller's transaction fails rather than silently losing governance
    evidence.
    """
    scope = _scope(tenant_id)
    await db.execute(select(func.pg_advisory_xact_lock(_lock_key(scope))))

    sequence_result = await db.execute(
        select(func.coalesce(func.max(AuditLog.ledger_sequence), 0)).where(
            AuditLog.ledger_scope == scope
        )
    )
    next_sequence = int(sequence_result.scalar_one()) + 1

    previous_result = await db.execute(
        select(AuditLog.entry_hash)
        .where(
            AuditLog.ledger_scope == scope,
            AuditLog.ledger_sequence.is_not(None),
        )
        .order_by(desc(AuditLog.ledger_sequence))
        .limit(1)
    )
    previous_hash = previous_result.scalar_one_or_none() or GENESIS_HASH
    created_at = datetime.now(timezone.utc)
    entry = AuditLog(
        tenant_id=tenant_id,
        actor_type=actor_type,
        actor_id=actor_id,
        action=action,
        resource_type=resource_type,
        resource_id=str(resource_id) if resource_id is not None else None,
        status=status,
        request_id=request_id,
        metadata_=redact_sensitive_data(metadata or {}),
        created_at=created_at,
        ledger_scope=scope,
        ledger_sequence=next_sequence,
        previous_hash=previous_hash,
    )
    entry.entry_hash = _compute_entry_hash(entry)
    db.add(entry)
    await db.flush()
    return entry


async def verify_ledger(
    db: AsyncSession,
    *,
    tenant_id: UUID | str | None,
    limit: int = 1000,
) -> dict[str, Any]:
    """Verify sequence continuity, previous-hash linkage, and entry hashes."""
    scope = _scope(tenant_id)
    result = await db.execute(
        select(AuditLog)
        .where(
            AuditLog.ledger_scope == scope,
            AuditLog.ledger_sequence.is_not(None),
            AuditLog.entry_hash.is_not(None),
        )
        .order_by(AuditLog.ledger_sequence.asc())
        .limit(min(max(limit, 1), 10000))
    )
    entries = list(result.scalars().all())
    expected_previous = GENESIS_HASH
    expected_sequence = 1
    errors: list[dict[str, Any]] = []
    for entry in entries:
        if entry.ledger_sequence != expected_sequence:
            errors.append({"type": "sequence_gap", "expected": expected_sequence, "actual": entry.ledger_sequence})
        if entry.previous_hash != expected_previous:
            errors.append({"type": "previous_hash_mismatch", "sequence": entry.ledger_sequence})
        calculated = _compute_entry_hash(entry)
        if entry.entry_hash != calculated:
            errors.append({"type": "entry_hash_mismatch", "sequence": entry.ledger_sequence})
        expected_previous = entry.entry_hash
        expected_sequence = int(entry.ledger_sequence or expected_sequence) + 1

    return {
        "valid": not errors,
        "scope": scope,
        "checked": len(entries),
        "errors": errors,
        "genesis_hash": GENESIS_HASH,
    }


async def list_logs(
    db: AsyncSession,
    *,
    tenant_id: UUID,
    limit: int = 100,
    action: str | None = None,
    status: str | None = None,
) -> list[AuditLog]:
    """Return tenant-scoped audit entries for operational/developer inspection."""
    stmt = (
        select(AuditLog)
        .where(AuditLog.tenant_id == tenant_id)
        .order_by(AuditLog.created_at.desc())
        .limit(min(max(limit, 1), 200))
    )
    if action:
        stmt = stmt.where(AuditLog.action == action)
    if status:
        stmt = stmt.where(AuditLog.status == status)
    result = await db.execute(stmt)
    return list(result.scalars().all())
