from __future__ import annotations

from flask import Blueprint, current_app, jsonify, request

from backend.services.conversation_service import (
    add_turn,
    build_history_block,
    clear_history,
    get_history,
    new_session,
)
from backend.services.integration_service import build_integration_response
from backend.services.speech_service import (
    ALLOWED_EXTENSIONS,
    SUPPORTED_LANGUAGES,
    detect_command,
    resolve_language,
    transcribe_audio,
)

voice_bp = Blueprint("voice", __name__)

MAX_AUDIO_BYTES = 25 * 1024 * 1024  # 25 MB (Whisper limit)


def _allowed(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def _transcribe_from_request() -> tuple[str, str | None]:
    """Transcribe the 'audio' file from the current request. Returns (transcript, error_msg)."""
    if "audio" not in request.files:
        return "", "audio file is required (field name: 'audio')"

    f = request.files["audio"]
    if not f.filename or not _allowed(f.filename):
        return "", f"Unsupported format. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}"

    audio_bytes = f.read()
    if len(audio_bytes) == 0:
        return "", "Audio file is empty (0 bytes)"
    if len(audio_bytes) > MAX_AUDIO_BYTES:
        return "", "File exceeds 25 MB limit"

    language = resolve_language(request.form.get("language"))
    try:
        transcript = transcribe_audio(audio_bytes, f.filename, language=language)
        return transcript, None
    except RuntimeError as exc:
        return "", str(exc)
    except Exception:
        current_app.logger.exception("Whisper transcription error")
        return "", "Transcription failed — check server logs"


# ---------------------------------------------------------------------------
# POST /api/v1/transcribe
# Accepts: multipart/form-data with 'audio' file + optional 'language'
# Returns: { transcript, command, query, language_hint }
# ---------------------------------------------------------------------------
@voice_bp.post("/v1/transcribe")
def transcribe() -> object:
    transcript, err = _transcribe_from_request()
    if err:
        return jsonify({"error": err}), 400

    if not transcript:
        return jsonify({"error": "Empty transcription result"}), 422

    language = resolve_language(request.form.get("language"))
    cmd = detect_command(transcript)
    return jsonify(
        {
            "transcript": transcript,
            "command": cmd["command"],
            "query": cmd["query"],
            "language_hint": language,
            "supported_languages": list(SUPPORTED_LANGUAGES.keys()),
        }
    )
# POST /api/v1/voice-query
# Accepts: multipart/form-data with 'audio' OR 'text', plus optional
#          'session_id', 'language', 'top_k'
# Returns: { transcript, command, query, answer, sources, confidence, session_id }
# ---------------------------------------------------------------------------
@voice_bp.post("/v1/voice-query")
def voice_query() -> object:
    session_id = (request.form.get("session_id") or "").strip() or None
    top_k_raw = request.form.get("top_k", "5")
    try:
        top_k = max(1, min(20, int(top_k_raw)))
    except (TypeError, ValueError):
        top_k = 5

    # Transcribe audio OR accept pre-transcribed text (for retry / re-send)
    if "audio" in request.files:
        transcript, err = _transcribe_from_request()
        if err:
            return jsonify({"error": err}), 400
    else:
        transcript = (request.form.get("text") or "").strip()

    if not transcript:
        return jsonify({"error": "Provide an 'audio' file or 'text' field"}), 400

    cmd = detect_command(transcript)
    query = cmd["query"]

    # Build message with conversation history prepended when a session exists
    history_block = build_history_block(session_id) if session_id else ""
    full_message = f"{history_block}\n\n{query}" if history_block else query

    try:
        rag_result = build_integration_response(
            {
                "client_request_id": f"voice-{session_id or 'anon'}",
                "message": full_message,
                "top_k": top_k,
                "include_recommendations": False,
            }
        )
    except Exception:
        current_app.logger.exception("RAG integration error in voice-query")
        return jsonify({"error": "RAG query failed — check server logs"}), 500

    resp = rag_result.get("response", {})
    answer = str(resp.get("answer", "")).strip()
    sources = resp.get("sources", [])
    confidence = float(resp.get("confidence", 0.0))

    if session_id and answer:
        add_turn(session_id, query, answer)

    return jsonify(
        {
            "transcript": transcript,
            "command": cmd["command"],
            "query": query,
            "answer": answer,
            "sources": sources,
            "confidence": confidence,
            "session_id": session_id,
        }
    )


# ---------------------------------------------------------------------------
# Conversation history management
# ---------------------------------------------------------------------------

@voice_bp.post("/v1/conversations")
def create_conversation() -> object:
    sid = new_session()
    return jsonify({"session_id": sid}), 201


@voice_bp.get("/v1/conversations/<session_id>")
def get_conversation(session_id: str) -> object:
    history = get_history(session_id)
    return jsonify(
        {
            "session_id": session_id,
            "history": history,
            "turn_count": len(history),
        }
    )


@voice_bp.delete("/v1/conversations/<session_id>")
def delete_conversation(session_id: str) -> object:
    clear_history(session_id)
    return jsonify({"session_id": session_id, "cleared": True})
