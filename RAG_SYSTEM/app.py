from __future__ import annotations

from flask import Flask, jsonify, request

from src.ingestion import ingest_sources
from src.rag_engine import RagEngine
from src.structured_transform import transform_chunks
from src.web_ui import get_html_ui

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
    return jsonify({"error": message}), status_code


@app.get("/")
def home() -> tuple:
    return get_html_ui(), 200, {"Content-Type": "text/html; charset=utf-8"}


@app.get("/health")
def health() -> tuple:
    return jsonify({"status": "ok"}), 200


@app.get("/api/v1/health")
def api_health() -> tuple:
    return jsonify({"status": "ok", "service": "rag-esg", "version": "v1"}), 200


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
    return transform()


@app.post("/ask")
def ask() -> tuple:
    payload = request.get_json(silent=True) or {}
    question = (payload.get("question") or "").strip()
    top_k = int(payload.get("top_k", 5))

    if not question:
        return _json_error("question is required", 400)

    try:
        answer, sources = rag.answer(query=question, top_k=top_k)
        return jsonify({"answer": answer, "sources": sources}), 200
    except Exception as exc:
        return _json_error(str(exc), 400)


@app.post("/api/v1/ask")
def api_ask() -> tuple:
    return ask()


@app.post("/api/v1/query")
def api_query() -> tuple:
    payload = request.get_json(silent=True) or {}
    question = (payload.get("question") or payload.get("message") or "").strip()
    top_k = int(payload.get("top_k", 5))

    if not question:
        return _json_error("question or message is required", 400)

    try:
        answer, sources = rag.answer(query=question, top_k=top_k)
        return (
            jsonify(
                {
                    "input": {"question": question, "top_k": top_k},
                    "output": {"answer": answer, "sources": sources},
                }
            ),
            200,
        )
    except Exception as exc:
        return _json_error(str(exc), 400)


@app.post("/api/v1/search")
def api_search() -> tuple:
    payload = request.get_json(silent=True) or {}
    query = (payload.get("query") or "").strip()
    top_k = int(payload.get("top_k", 5))

    if not query:
        return _json_error("query is required", 400)

    try:
        sources = rag.search(query=query, top_k=top_k)
        return jsonify({"query": query, "top_k": top_k, "results": sources}), 200
    except Exception as exc:
        return _json_error(str(exc), 400)


@app.get("/api/v1/docs")
def api_docs() -> tuple:
    return (
        jsonify(
            {
                "name": "RAG ESG API",
                "version": "v1",
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
                        "request_example": {"message": "What are the main ESG risks?", "top_k": 5},
                    },
                },
            }
        ),
        200,
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
