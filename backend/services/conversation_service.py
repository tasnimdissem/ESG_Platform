from __future__ import annotations

from datetime import datetime, timezone
from threading import Lock
from typing import Any
from uuid import uuid4

_sessions: dict[str, list[dict[str, Any]]] = {}
_lock = Lock()

MAX_TURNS = 20
CONTEXT_TURNS = 5


def new_session() -> str:
    sid = uuid4().hex
    with _lock:
        _sessions[sid] = []
    return sid


def add_turn(session_id: str, question: str, answer: str) -> None:
    with _lock:
        if session_id not in _sessions:
            _sessions[session_id] = []
        _sessions[session_id].append(
            {
                "question": question,
                "answer": answer,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )
        if len(_sessions[session_id]) > MAX_TURNS:
            _sessions[session_id] = _sessions[session_id][-MAX_TURNS:]


def get_history(session_id: str) -> list[dict[str, Any]]:
    with _lock:
        return list(_sessions.get(session_id, []))


def clear_history(session_id: str) -> None:
    with _lock:
        _sessions.pop(session_id, None)


def build_history_block(session_id: str) -> str:
    """Return the last CONTEXT_TURNS turns formatted for inclusion in an LLM prompt."""
    turns = get_history(session_id)[-CONTEXT_TURNS:]
    if not turns:
        return ""
    lines = ["[Conversation so far]"]
    for t in turns:
        lines.append(f"User: {t['question']}")
        lines.append(f"Assistant: {t['answer']}")
    return "\n".join(lines)
