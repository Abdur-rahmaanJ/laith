from __future__ import annotations
import hashlib
import json
import shutil
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional, Dict, Any


@dataclass(frozen=True)
class ArtifactKey:
    source_hash: str
    phase: str
    options_hash: str

    @classmethod
    def from_source(cls, source: str, phase: str, options: Optional[dict] = None) -> "ArtifactKey":
        norm = "\n".join(l.rstrip() for l in source.splitlines())
        while norm.endswith("\n\n"):
            norm = norm[:-1]
        norm += "\n"
        source_hash = hashlib.sha256(norm.encode()).hexdigest()
        opts_hash = hashlib.sha256(
            json.dumps(options or {}, sort_keys=True).encode()
        ).hexdigest()
        return cls(source_hash=source_hash, phase=phase, options_hash=opts_hash)

    def to_path(self) -> str:
        return f"{self.source_hash}/{self.phase}_{self.options_hash}.bin"


class CacheStore:
    def __init__(self, base_path: Path, max_size_mb: int = 1024):
        self._base = base_path / "cache"
        self._base.mkdir(parents=True, exist_ok=True)
        self._index_path = self._base / "index.json"
        self._index: Dict[str, str] = self._load_index()
        self._max_size = max_size_mb * 1024 * 1024

    def _load_index(self) -> Dict[str, str]:
        if self._index_path.exists():
            return json.loads(self._index_path.read_text())
        return {}

    def _save_index(self):
        self._index_path.write_text(json.dumps(self._index, sort_keys=True))

    def get(self, key: ArtifactKey) -> Optional[bytes]:
        path = self._base / key.to_path()
        if path.exists():
            return path.read_bytes()
        return None

    def set(self, key: ArtifactKey, value: bytes):
        path = self._base / key.to_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(value)
        self._index[f"{key.source_hash}:{key.phase}"] = key.options_hash
        self._save_index()

    def get_or_compute(self, key: ArtifactKey, compute: callable) -> bytes:
        cached = self.get(key)
        if cached is not None:
            return cached
        value = compute()
        self.set(key, value)
        return value

    def invalidate(self, source_hash: str):
        path = self._base / source_hash
        if path.exists():
            shutil.rmtree(path)

    def invalidate_all(self):
        if self._base.exists():
            shutil.rmtree(self._base)
        self._base.mkdir(parents=True)
        self._index = {}
        self._save_index()

    def stats(self) -> dict:
        total_size = 0
        total_files = 0
        for f in self._base.rglob("*.bin"):
            total_size += f.stat().st_size
            total_files += 1
        return {
            "files": total_files,
            "size_bytes": total_size,
            "size_mb": total_size / 1024 / 1024,
            "index_entries": len(self._index),
        }
