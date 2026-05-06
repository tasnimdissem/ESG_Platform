from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple

from flask import Flask, jsonify, request

from .src import config
from .src.ingestion import ingest_sources
from .src.rag_engine import RagEngine
from .src.structured_transform import transform_chunks

app = Flask(__name__)
rag = RagEngine()


@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    return response


@app.route("/api/v1/<path:_>", methods=["OPTIONS"])
def options_preflight(_):
    return ("", 204)


def _json_error(message: str, status_code: int = 400) -> tuple:
    return jsonify({"error": message, "status": status_code}), status_code


def _is_api_protected() -> bool:
    return bool(config.API_AUTH_TOKEN.strip())


def _check_api_auth() -> Tuple[bool, tuple | None]:
    if not _is_api_protected():
        return True, None

    auth_header = (request.headers.get("Authorization") or "").strip()
    expected = f"Bearer {config.API_AUTH_TOKEN}"

    if auth_header != expected:
        return False, _json_error("unauthorized", 401)

    return True, None


def _require_api_auth_if_needed() -> tuple | None:
    allowed, error_response = _check_api_auth()
    if not allowed:
        return error_response
    return None


def _safe_int(value: Any, default: int, minimum: int = 1, maximum: int = 50) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default
    return max(minimum, min(maximum, parsed))


def _source_confidence(distance: float) -> float:
    # Convert FAISS L2 distance into an intuitive [0,1] confidence score.
    return round(1.0 / (1.0 + max(distance, 0.0)), 4)


def _normalize_sources(sources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    normalized: List[Dict[str, Any]] = []
    for item in sources:
        distance = float(item.get("distance", 0.0))
        normalized.append(
            {
                "rank": int(item.get("rank", 0) or 0),
                "source_type": item.get("source_type", "unknown"),
                "source_name": item.get("source_name", "unknown"),
                "chunk_id": item.get("chunk_id", "unknown"),
                "text": item.get("text", ""),
                "distance": distance,
                "confidence": _source_confidence(distance),
            }
        )
    return normalized


def _overall_confidence(sources: List[Dict[str, Any]]) -> float:
    if not sources:
        return 0.0
    values = [float(s.get("confidence", 0.0)) for s in sources]
    return round(sum(values) / len(values), 4)


def _wants_recommendations(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y", "on"}
    if isinstance(value, int):
        return value != 0
    return False


def _build_recommendations(
    question: str,
    retrieved: List[Dict[str, Any]],
    signals: Dict[str, Any] | None = None,
) -> List[Dict[str, Any]]:
    if not retrieved:
        return []

    structured = transform_chunks(retrieved)
    recommendations: List[Dict[str, Any]] = []
    company_name = (signals or {}).get("company") or "Organization"

    for idx, row in enumerate(structured[:5], start=1):
        pillar = row.get("category", "Environmental")
        insight_list = row.get("key_insights") or []
        first_insight = (
            insight_list[0]
            if isinstance(insight_list, list) and insight_list
            else "No explicit insight available"
        )
        source_name = row.get("source_name", "unknown")
        source_type = row.get("source_type", "unknown")

        if pillar == "Environmental":
            effort = "medium"
            timeline = "3-6 months"
            impact = "high"
        elif pillar == "Social":
            effort = "medium"
            timeline = "2-4 months"
            impact = "medium"
        else:
            effort = "low"
            timeline = "1-3 months"
            impact = "medium"

        priority = min(5, max(1, 6 - idx))
        rec_id = f"rec-{pillar[:1].lower()}-{idx}"

        recommendations.append(
            {
                "id": rec_id,
                "title": f"{pillar} improvement initiative #{idx}",
                "pillar": pillar,
                "impact": impact,
                "effort": effort,
                "timeline": timeline,
                "priority": priority,
                "justification": (
                    f"For {company_name}, the retrieved evidence indicates: {first_insight} "
                    f"(question: {question})."
                ),
                "sources": [
                    {
                        "source_name": source_name,
                        "source_type": source_type,
                        "chunk_id": row.get("chunk_id", "unknown"),
                    }
                ],
            }
        )

    return recommendations


@app.get("/")
def home() -> tuple:
    return jsonify({"status": "Rag Engine API is running", "endpoints": "/api/v1/docs"}), 200


@app.get("/health")
def health() -> tuple:
    return jsonify({"status": "ok"}), 200


@app.get("/api/v1/health")
def api_health() -> tuple:
    auth_mode = "bearer" if _is_api_protected() else "none"
    return (
        jsonify(
            {
                "status": "ok",
                "service": "rag-esg",
                "version": "v1",
                "auth_mode": auth_mode,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        ),
        200,
    )


@app.post("/ingest")
def ingest() -> tuple:
    try:
        chunks = ingest_sources()
        stats = rag.build_index(chunks)
        return (
            jsonify(
                {
                    "message": "Ingestion complete",
                    "stats": stats,
                }
            ),
            200,
        )
    except Exception as exc:
        return jsonify({"error": str(exc)}), 400


@app.post("/api/v1/ingest")
def api_ingest() -> tuple:
    auth_error = _require_api_auth_if_needed()
    if auth_error:
        return auth_error
    return ingest()


@app.post("/transform")
def transform() -> tuple:
    payload = request.get_json(silent=True) or {}
    chunks = payload.get("chunks") or []

    if not isinstance(chunks, list) or not chunks:
        return _json_error("chunks list is required", 400)

    try:
        structured = transform_chunks(chunks)
        return jsonify(structured), 200
    except Exception as exc:
        return _json_error(str(exc), 400)


@app.post("/api/v1/transform")
def api_transform() -> tuple:
    auth_error = _require_api_auth_if_needed()
    if auth_error:
        return auth_error
    return transform()


@app.post("/ask")
def ask() -> tuple:
    payload = request.get_json(silent=True) or {}
    question = (payload.get("question") or "").strip()
    top_k = _safe_int(payload.get("top_k", 5), default=5)

    if not question:
        return _json_error("question is required", 400)

    try:
        answer, sources = rag.answer(query=question, top_k=top_k)
        normalized_sources = _normalize_sources(sources)
        return (
            jsonify(
                {
                    "answer": answer,
                    "sources": normalized_sources,
                    "confidence": _overall_confidence(normalized_sources),
                }
            ),
            200,
        )
    except Exception as exc:
        return _json_error(str(exc), 400)


@app.post("/api/v1/ask")
def api_ask() -> tuple:
    auth_error = _require_api_auth_if_needed()
    if auth_error:
        return auth_error
    return ask()


@app.post("/api/v1/query")
def api_query() -> tuple:
    auth_error = _require_api_auth_if_needed()
    if auth_error:
        return auth_error

    payload = request.get_json(silent=True) or {}
    question = (payload.get("question") or payload.get("message") or "").strip()
    top_k = _safe_int(payload.get("top_k", 5), default=5)

    if not question:
        return _json_error("question or message is required", 400)

    try:
        answer, sources = rag.answer(query=question, top_k=top_k)
        normalized_sources = _normalize_sources(sources)
        return (
            jsonify(
                {
                    "input": {"question": question, "top_k": top_k},
                    "output": {
                        "answer": answer,
                        "sources": normalized_sources,
                        "confidence": _overall_confidence(normalized_sources),
                    },
                }
            ),
            200,
        )
    except Exception as exc:
        return _json_error(str(exc), 400)


@app.post("/api/v1/search")
def api_search() -> tuple:
    auth_error = _require_api_auth_if_needed()
    if auth_error:
        return auth_error

    payload = request.get_json(silent=True) or {}
    query = (payload.get("query") or "").strip()
    top_k = _safe_int(payload.get("top_k", 5), default=5)

    if not query:
        return _json_error("query is required", 400)

    try:
        sources = rag.search(query=query, top_k=top_k)
        normalized_sources = _normalize_sources(sources)
        return (
            jsonify(
                {
                    "query": query,
                    "top_k": top_k,
                    "results": normalized_sources,
                    "confidence": _overall_confidence(normalized_sources),
                }
            ),
            200,
        )
    except Exception as exc:
        return _json_error(str(exc), 400)


@app.post("/api/v1/recommendations")
def api_recommendations() -> tuple:
    auth_error = _require_api_auth_if_needed()
    if auth_error:
        return auth_error

    payload = request.get_json(silent=True) or {}
    question = (payload.get("question") or payload.get("message") or "").strip()
    top_k = _safe_int(payload.get("top_k", 5), default=5)
    signals = payload.get("signals") or {}
    filters = payload.get("filters") or {}

    if not question:
        return _json_error("question or message is required", 400)

    try:
        retrieved = rag.search(query=question, top_k=top_k)
        normalized_sources = _normalize_sources(retrieved)
        recommendations = _build_recommendations(
            question=question,
            retrieved=retrieved,
            signals=signals if isinstance(signals, dict) else {},
        )

        return (
            jsonify(
                {
                    "input": {
                        "question": question,
                        "top_k": top_k,
                        "signals": signals,
                        "filters": filters,
                    },
                    "output": {
                        "recommendations": recommendations,
                        "sources": normalized_sources,
                        "confidence": _overall_confidence(normalized_sources),
                        "notes": {
                            "filtering": "Filters are accepted for contract compatibility. Retrieval currently uses vector search only.",
                        },
                    },
                }
            ),
            200,
        )
    except Exception as exc:
        return _json_error(str(exc), 400)


@app.post("/api/v1/integration")
def api_integration() -> tuple:
    auth_error = _require_api_auth_if_needed()
    if auth_error:
        return auth_error

    payload = request.get_json(silent=True) or {}
    question = (payload.get("question") or payload.get("message") or "").strip()
    top_k = _safe_int(payload.get("top_k", 5), default=5)
    include_recommendations = _wants_recommendations(
        payload.get("include_recommendations", True)
    )
    signals = payload.get("signals") or {}
    filters = payload.get("filters") or {}
    client_request_id = (payload.get("client_request_id") or "").strip()

    if not question:
        return _json_error("question or message is required", 400)

    try:
        answer, sources = rag.answer(query=question, top_k=top_k)
        normalized_sources = _normalize_sources(sources)

        recommendations: List[Dict[str, Any]] = []
        if include_recommendations:
            recommendations = _build_recommendations(
                question=question,
                retrieved=sources,
                signals=signals if isinstance(signals, dict) else {},
            )

        return (
            jsonify(
                {
                    "request": {
                        "request_id": client_request_id,
                        "question": question,
                        "top_k": top_k,
                        "include_recommendations": include_recommendations,
                        "signals": signals,
                        "filters": filters,
                    },
                    "response": {
                        "answer": answer,
                        "recommendations": recommendations,
                        "sources": normalized_sources,
                        "confidence": _overall_confidence(normalized_sources),
                    },
                    "meta": {
                        "service": "rag-esg",
                        "version": "v1",
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    },
                }
            ),
            200,
        )
    except Exception as exc:
        return _json_error(str(exc), 400)


@app.get("/api/v1/docs")
def api_docs() -> tuple:
    auth_mode = "Bearer token" if _is_api_protected() else "None"
    auth_header = (
        "Authorization: Bearer <API_AUTH_TOKEN>"
        if _is_api_protected()
        else "No auth header required"
    )

    return (
        jsonify(
            {
                "name": "RAG ESG API",
                "version": "v1",
                "base_url_example": "http://localhost:8000",
                "auth": {
                    "method": auth_mode,
                    "expected_header": auth_header,
                },
                "endpoints": {
                    "GET /api/v1/health": "Service health check",
                    "POST /api/v1/ingest": "Ingest raw files and rebuild FAISS index",
                    "POST /api/v1/transform": {
                        "description": "Transform provided chunks into structured ESG rows",
                        "request_example": {
                            "chunks": [
                                {
                                    "source_type": "article",
                                    "source_name": "sample.txt",
                                    "chunk_id": "article-sample-0",
                                    "text": "CO2 emissions were reduced by 15% in 2025.",
                                }
                            ]
                        },
                    },
                    "POST /api/v1/search": {
                        "description": "Retrieve top-k similar chunks",
                        "request_example": {"query": "What are climate risks?", "top_k": 5},
                    },
                    "POST /api/v1/ask": {
                        "description": "RAG answer with retrieved sources",
                        "request_example": {"question": "What are the main ESG risks?", "top_k": 5},
                    },
                    "POST /api/v1/query": {
                        "description": "Integration-friendly endpoint for external platforms",
                        "request_example": {
                            "message": "What are the main ESG risks?",
                            "top_k": 5,
                        },
                        "response_contract": {
                            "output.answer": "string",
                            "output.sources": "array",
                            "output.confidence": "number in [0,1]",
                        },
                    },
                    "POST /api/v1/recommendations": {
                        "description": "Return ESG recommendations based on retrieved evidence",
                        "request_example": {
                            "question": "How can we improve ESG performance in manufacturing?",
                            "top_k": 5,
                            "signals": {
                                "company": "Acme Corp",
                                "esg_score": 58,
                                "sector": "Manufacturing",
                                "country": "FR",
                                "goals": ["Reduce Scope 2 emissions", "Improve board diversity"],
                            },
                            "filters": {
                                "language": "en",
                                "region": "EU",
                                "period": "2022-2026",
                                "source_types": ["pdf", "article", "dataset"],
                            },
                        },
                        "response_contract": {
                            "output.recommendations": "array of {title,pillar,impact,effort,timeline,priority,justification,sources}",
                            "output.sources": "array",
                            "output.confidence": "number in [0,1]",
                        },
                    },
                    "POST /api/v1/integration": {
                        "description": "Single endpoint for external platform integration (chat + optional recommendations)",
                        "request_example": {
                            "client_request_id": "ext-req-001",
                            "message": "What ESG actions should we prioritize this quarter?",
                            "top_k": 5,
                            "include_recommendations": True,
                            "signals": {
                                "company": "Acme Corp",
                                "sector": "Manufacturing",
                                "esg_score": 58,
                            },
                            "filters": {
                                "region": "EU",
                                "period": "2022-2026",
                            },
                        },
                        "response_contract": {
                            "request": "echo of normalized request payload",
                            "response.answer": "string",
                            "response.recommendations": "array",
                            "response.sources": "array",
                            "response.confidence": "number in [0,1]",
                            "meta.timestamp": "ISO-8601 UTC",
                        },
                    },
                },
                "errors": {
                    "400": "Bad request payload or missing mandatory field",
                    "401": "Unauthorized (invalid/missing bearer token when auth is enabled)",
                    "500": "Unexpected internal error",
                },
            }
        ),
        200,
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
