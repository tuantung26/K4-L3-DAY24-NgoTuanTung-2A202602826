"""BƯỚC 3c — trifecta split + egress allowlist (13')."""
from __future__ import annotations

import hashlib
import json
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path

from agent import ledger, pii, policy, tools

BASE_DIR = Path(__file__).resolve().parent.parent
CUSTOMERS_FILE = BASE_DIR / "data" / "customers.json"
REPORTS_DIR = BASE_DIR / "reports"
DEFAULT_LEDGER_PATH = REPORTS_DIR / "ledger.jsonl"

_TICKET_ID_RE = re.compile(r"ticket-(\d+)[a-z]*\.md", re.IGNORECASE)


class RunnerScaffoldPending(NotImplementedError):
    """Only the original 3c stub uses this to enable the CP1/CP2 baseline."""


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _hash_args(args_dict: dict) -> str:
    serialized = json.dumps(args_dict, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def handle(message: str, llm, log_dir: Path | None = None,
           principal_id: str = "support_l1") -> str:
    ledger_path = (log_dir / "ledger.jsonl") if log_dir else DEFAULT_LEDGER_PATH
    run_id = f"run-{uuid.uuid4().hex[:8]}"
    expires_at = "2099-01-01T00:00:00+00:00"

    # =========================================================================
    # RUN A: Untrusted content collection (search_docs only)
    # NO read_customer, NO http_post
    # =========================================================================
    run_a_owner = "lab24-agent/run-a"
    ctx_search = policy.PolicyContext(
        data_classification="internal",
        request_purpose="summarize-tickets",
        agent_owner=run_a_owner,
        delegation_depth=0,
        egress_enabled=False,
        principal_id=principal_id,
        requested_tool="search_docs",
        agent_scopes=("search_docs",),
        parent_scopes=(),
        expires_at=expires_at,
    )

    allow_search, reason_search = policy.check(ctx_search)
    ledger.append({
        "ts": _now_iso(),
        "agent_id": "lab24-agent",
        "run_id": f"{run_id}-a",
        "tool": "search_docs",
        "args_hash": _hash_args({"query": message}),
        "classification": "internal",
        "decision": "allow" if allow_search else "deny",
        "reason": reason_search,
        "on_behalf_of": principal_id,
        "expires_at": expires_at,
    }, ledger_path)

    if not allow_search:
        return "Không có quyền tra cứu tài liệu."

    docs = tools.search_docs(message)

    # Trích xuất số ticket ID DUY NHẤT TỪ TÊN FILE
    ticket_ids: set[int] = set()
    for d in docs:
        doc_id = d.get("id", "")
        match = _TICKET_ID_RE.search(doc_id)
        if match:
            ticket_ids.add(int(match.group(1)))

    # Kiểm tra injection trên nội dung docs (chỉ để kiểm tra mục đích tấn công)
    combined_raw_text = "\n\n".join(d["text"] for d in docs)
    injected = llm.find_injection(combined_raw_text)

    # Áp dụng PII redaction trước khi đưa text qua boundary
    redacted_docs = []
    for d in docs:
        redacted_docs.append({
            "id": d["id"],
            "text": pii.redact(d["text"]),
        })

    # =========================================================================
    # RUN B: Private store lookup (read_customer)
    # Map ticket_id -> customer_id từ NGUỒN TIN CẬY (data/customers.json)
    # =========================================================================
    run_b_owner = "lab24-agent/run-b"
    customers_data = json.loads(CUSTOMERS_FILE.read_text(encoding="utf-8"))

    # Map ticket_ids sang customer_ids
    trusted_customer_ids: set[str] = set()
    for cust in customers_data:
        c_tickets = set(cust.get("related_tickets", []))
        if ticket_ids.intersection(c_tickets):
            trusted_customer_ids.add(cust["customer_id"])

    collected_customers = []
    # Thử đọc hồ sơ của các khách hàng hợp lệ liên quan đến ticket
    for cid in sorted(trusted_customer_ids):
        ctx_read = policy.PolicyContext(
            data_classification="restricted",
            request_purpose="support-reply",
            agent_owner=run_b_owner,
            delegation_depth=0,
            egress_enabled=False,
            principal_id=principal_id,
            requested_tool="read_customer",
            agent_scopes=("search_docs", "read_customer"),
            parent_scopes=(),
            expires_at=expires_at,
        )

        allow_read, reason_read = policy.check(ctx_read)
        ledger.append({
            "ts": _now_iso(),
            "agent_id": "lab24-agent",
            "run_id": f"{run_id}-b",
            "tool": "read_customer",
            "args_hash": _hash_args({"customer_id": cid}),
            "classification": "restricted",
            "decision": "allow" if allow_read else "deny",
            "reason": reason_read,
            "on_behalf_of": principal_id,
            "expires_at": expires_at,
        }, ledger_path)

        if allow_read:
            try:
                cust_record = tools.read_customer(cid)
                collected_customers.append(cust_record)
            except tools.ToolError:
                pass

    # Nếu có chỉ thị injection đòi POST ra sink
    if injected is not None and injected.target_url:
        ctx_egress = policy.PolicyContext(
            data_classification="restricted",
            request_purpose="reconciliation",
            agent_owner=run_b_owner,
            delegation_depth=1,
            egress_enabled=True,
            principal_id=principal_id,
            requested_tool="http_post",
            agent_scopes=("search_docs", "read_customer", "http_post"),
            parent_scopes=(),
            expires_at=expires_at,
        )

        allow_egress, reason_egress = policy.check(ctx_egress)
        ledger.append({
            "ts": _now_iso(),
            "agent_id": "lab24-agent",
            "run_id": f"{run_id}-b",
            "tool": "http_post",
            "args_hash": _hash_args({"url": injected.target_url, "records_count": len(collected_customers)}),
            "classification": "restricted",
            "decision": "allow" if allow_egress else "deny",
            "reason": reason_egress,
            "on_behalf_of": principal_id,
            "expires_at": expires_at,
        }, ledger_path)

        if allow_egress:
            tools.http_post(injected.target_url, {"records": collected_customers})

    return llm.summarize(docs)
