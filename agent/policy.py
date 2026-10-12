"""BƯỚC 3b — PEP (Policy Enforcement Point) tại tool call (15')."""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
PRINCIPALS_FILE = BASE_DIR / "data" / "principals.json"


@dataclass(frozen=True)
class PolicyContext:
    data_classification: str
    request_purpose: str
    agent_owner: str
    delegation_depth: int
    egress_enabled: bool
    principal_id: str = ""
    requested_tool: str = ""
    agent_scopes: tuple[str, ...] = ()
    parent_scopes: tuple[str, ...] = ()
    expires_at: str = ""


def _is_expired(expires_at: str) -> bool:
    if not expires_at:
        return False
    try:
        # ISO-8601 parsing
        dt = datetime.fromisoformat(expires_at)
        now = datetime.now(timezone.utc)
        return now > dt
    except Exception:
        return True


def check(context: PolicyContext) -> tuple[bool, str]:
    """Policy check implementation.

    Rule tối thiểu:
        classification == "restricted" and egress_enabled is True -> DENY
    """
    # 1. Rule tối thiểu bắt buộc
    if context.data_classification == "restricted" and context.egress_enabled is True:
        return False, "Deny: restricted data classification with egress enabled is strictly prohibited"

    # 2. Check expiration nếu có
    if context.expires_at and _is_expired(context.expires_at):
        return False, f"Deny: execution context has expired at {context.expires_at}"

    # 3. Principal OBO verification nếu principal_id được cung cấp
    if context.principal_id:
        if not PRINCIPALS_FILE.exists():
            return False, "Deny: principals.json not found"

        principals = json.loads(PRINCIPALS_FILE.read_text(encoding="utf-8"))
        if context.principal_id not in principals:
            return False, f"Deny: unknown principal '{context.principal_id}'"

        principal_info = principals[context.principal_id]
        allowed_tools = set(principal_info.get("allowed_tools", []))
        allowed_purposes = set(principal_info.get("purposes", []))

        # Check requested tool vs principal allowed tools
        if context.requested_tool:
            if context.requested_tool not in allowed_tools:
                return False, f"Deny: tool '{context.requested_tool}' not allowed for principal '{context.principal_id}'"

            # Effective tool permission = principal.allowed_tools ∩ agent_scopes
            if context.agent_scopes and context.requested_tool not in context.agent_scopes:
                return False, f"Deny: tool '{context.requested_tool}' not in agent scopes"

            # If delegated (depth > 0), must also be within parent_scopes
            if context.delegation_depth > 0:
                if context.parent_scopes and context.requested_tool not in context.parent_scopes:
                    return False, f"Deny: tool '{context.requested_tool}' exceeds parent scopes at delegation depth {context.delegation_depth}"

        # Check request purpose
        if context.request_purpose and allowed_purposes and context.request_purpose not in allowed_purposes:
            return False, f"Deny: purpose '{context.request_purpose}' not allowed for principal '{context.principal_id}'"

    # Default allow with non-empty reason
    tool_desc = context.requested_tool or "action"
    return True, f"Allow: {tool_desc} complies with policy for principal '{context.principal_id or 'anonymous'}'"
