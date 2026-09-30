"""Object storage abstraction.

Local-disk implementation for development; the interface is shaped so a
future S3-compatible backend is a drop-in swap (07_Backend §5.5,
15_Deployment). Never construct a storage path from client input directly
— always route through build_key() so tenant isolation (14_Security §5)
holds even if a caller forgets to check tenant_id.
"""

from __future__ import annotations

import os

import uuid
from pathlib import Path
from typing import BinaryIO, Protocol

from app.core.config import get_settings

settings = get_settings()


def build_key(tenant_id: str, filename: str) -> str:
    """Tenant-namespaced, collision-resistant storage key."""
    safe_name = Path(filename).name  # strip any path components from client input
    return f"{tenant_id}/{uuid.uuid4().hex}_{safe_name}"


class StorageBackend(Protocol):
    def save(self, key: str, data: BinaryIO) -> int:
        """Persist `data` under `key`; returns size in bytes."""
        ...

    def open(self, key: str) -> BinaryIO:
        """Return a readable binary stream for `key`."""
        ...

    def delete(self, key: str) -> None:
        ...

    def exists(self, key: str) -> bool:
        ...

    def list_prefix(self, prefix: str) -> list[str]:
        """List tenant-namespaced keys under a prefix."""
        ...


class LocalDiskStorage:
    def __init__(self, base_dir: str | None = None):
        self.base_dir = Path(base_dir or settings.storage_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _path(self, key: str) -> Path:
        path = (self.base_dir / key).resolve()
        if self.base_dir.resolve() not in path.parents and path != self.base_dir.resolve():
            raise ValueError("Invalid storage key (path traversal attempt)")
        return path

    def save(self, key: str, data: BinaryIO) -> int:
        path = self._path(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        size = 0
        with open(path, "wb") as f:
            for chunk in iter(lambda: data.read(1024 * 1024), b""):
                f.write(chunk)
                size += len(chunk)
        return size

    def open(self, key: str) -> BinaryIO:
        return open(self._path(key), "rb")

    def delete(self, key: str) -> None:
        path = self._path(key)
        if path.exists():
            path.unlink()

    def exists(self, key: str) -> bool:
        return self._path(key).exists()

    def list_prefix(self, prefix: str) -> list[str]:
        base = self._path(prefix)
        if base.is_file():
            return [prefix]
        if not base.exists():
            return []
        root = self.base_dir.resolve()
        return [str(p.relative_to(root)).replace(os.sep, "/") for p in base.rglob("*") if p.is_file()]


_backend: StorageBackend | None = None


def get_storage_backend() -> StorageBackend:
    global _backend
    if _backend is None:
        _backend = LocalDiskStorage()
    return _backend
