"""BƯỚC 3a — PII gate TRƯỚC KHI vào context/store (12')."""
from __future__ import annotations

import re


_CCCD_RE = re.compile(r"(?<!\d)\d{12}(?!\d)")
_PHONE_RE = re.compile(r"(?<!\d)0\d{9,10}(?!\d)")
_BANK_ACCOUNT_RE = re.compile(r"(?i)(?:STK|số\s+tài\s+khoản)\s*:?\s*(\d{8,16})")
_EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")


def detect(text: str) -> list[dict]:
    entities: list[dict] = []

    # 1. Email
    for m in _EMAIL_RE.finditer(text):
        entities.append({"type": "EMAIL", "start": m.start(), "end": m.end()})

    # 2. Bank Account
    for m in _BANK_ACCOUNT_RE.finditer(text):
        start, end = m.start(1), m.end(1)
        entities.append({"type": "VN_BANK_ACCOUNT", "start": start, "end": end})

    # 3. CCCD (12 digits)
    for m in _CCCD_RE.finditer(text):
        start, end = m.start(), m.end()
        # Avoid overlapping with already detected bank accounts or emails
        if not any(e["start"] <= start < e["end"] or e["start"] < end <= e["end"] for e in entities):
            entities.append({"type": "VN_CCCD", "start": start, "end": end})

    # 4. Phone (0 + 9-10 digits)
    for m in _PHONE_RE.finditer(text):
        start, end = m.start(), m.end()
        # Avoid overlapping
        if not any(e["start"] <= start < e["end"] or e["start"] < end <= e["end"] for e in entities):
            entities.append({"type": "VN_PHONE", "start": start, "end": end})

    # Sort by start offset
    entities.sort(key=lambda x: (x["start"], x["end"]))
    return entities


def redact(text: str) -> str:
    entities = detect(text)
    if not entities:
        return text

    # Merge overlapping or duplicate entities if any
    merged: list[dict] = []
    for ent in sorted(entities, key=lambda x: (x["start"], -x["end"])):
        if not merged:
            merged.append(ent)
        else:
            prev = merged[-1]
            if ent["start"] < prev["end"]:
                continue
            merged.append(ent)

    # Redact from end to start to preserve character offsets
    result = list(text)
    for ent in reversed(merged):
        start, end = ent["start"], ent["end"]
        label = f"[REDACTED_{ent['type']}]"
        result[start:end] = list(label)

    return "".join(result)
