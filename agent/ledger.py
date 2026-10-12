"""BƯỚC 3d — audit ledger append-only, tamper-evident (10')."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path


def _calculate_hash(entry_without_hash: dict) -> str:
    serialized = json.dumps(entry_without_hash, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def append(entry: dict, path: Path) -> dict:
    path.parent.mkdir(parents=True, exist_ok=True)

    prev_hash = "0" * 64
    if path.exists() and path.stat().st_size > 0:
        lines = [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
        if lines:
            last_entry = json.loads(lines[-1])
            prev_hash = last_entry.get("hash", "0" * 64)

    record = dict(entry)
    record["prev_hash"] = prev_hash
    # Calculate hash over record without "hash" key
    record_hash = _calculate_hash(record)
    record["hash"] = record_hash

    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")

    return record


def verify(path: Path) -> bool:
    if not path.exists():
        return False
    if path.stat().st_size == 0:
        return True

    lines = [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not lines:
        return True

    expected_prev = "0" * 64
    for line in lines:
        try:
            record = json.loads(line)
        except Exception:
            return False

        # Every entry must have non-empty reason
        reason = record.get("reason")
        if not reason or not str(reason).strip():
            return False

        if record.get("prev_hash") != expected_prev:
            return False

        stored_hash = record.get("hash")
        record_without_hash = {k: v for k, v in record.items() if k != "hash"}
        calculated = _calculate_hash(record_without_hash)
        if stored_hash != calculated:
            return False

        expected_prev = stored_hash

    return True
