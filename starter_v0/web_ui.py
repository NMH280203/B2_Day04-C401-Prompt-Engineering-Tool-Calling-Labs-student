"""
web_ui.py — Flask web server for the Research Agent UI.
Run: python web_ui.py --provider openrouter --version v0
"""
from __future__ import annotations

# Force UTF-8 stdout/stderr on Windows so emoji in chat.py prints don't crash.
import io
import sys
if hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "buffer"):
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

import argparse
import json
import re
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from flask import Flask, jsonify, request, send_from_directory

from chat import (
    assistant_tool_message,
    execute_tool_call,
    json_text,
    now_iso,
    run_model_tool_loop,
    safe_slug,
    tool_results_message,
    trim_history,
    write_transcript,
)
from env_loader import load_lab_env
from providers import make_provider
from tools import load_tool_declarations, to_openai_tools
from versioning import artifact_version_dict, build_artifact_version

ROOT = Path(__file__).parent
ARTIFACTS_DIR = ROOT / "artifacts"
load_lab_env(ROOT)

app = Flask(__name__, static_folder=str(ROOT / "ui"))

# ── Global state (single-session server) ──────────────────────────────────────
_state: dict[str, Any] = {}


def init_state(args: argparse.Namespace) -> None:
    system_prompt = args.system_prompt.read_text(encoding="utf-8")
    tool_declarations = load_tool_declarations(args.tools)
    openai_tools = to_openai_tools(tool_declarations)
    provider = make_provider(args.provider)
    selected_model = args.model or getattr(provider, "default_model", None)
    artifact_version = build_artifact_version(args.version, args.system_prompt, args.tools)

    timestamp = datetime.now().strftime("%Y%m%dT%H%M%S%f")
    transcript_id = "_".join([safe_slug(args.version), safe_slug(args.provider), timestamp])
    transcript_path = ROOT / "transcripts" / f"{transcript_id}.transcript.json"
    transcript: dict[str, Any] = {
        "transcript_id": transcript_id,
        **artifact_version_dict(artifact_version),
        "provider": args.provider,
        "model": selected_model,
        "system_prompt": str(args.system_prompt),
        "tools": str(args.tools),
        "created_at": now_iso(),
        "updated_at": now_iso(),
        "turns": [],
    }

    _state.update({
        "provider": provider,
        "system_prompt": system_prompt,
        "openai_tools": openai_tools,
        "model": args.model,
        "history_window": args.history_window,
        "max_tool_rounds": args.max_tool_rounds,
        "artifact_version": artifact_version.artifact_version,
        "provider_name": args.provider,
        "model_name": selected_model,
        "history": [],
        "turn_index": 0,
        "transcript": transcript,
        "transcript_path": transcript_path,
    })


# ── Routes ─────────────────────────────────────────────────────────────────────

@app.after_request
def add_headers(response):
    """Ensure JSON responses are properly typed and CORS-friendly for tunnel access."""
    if request.path.startswith("/api/"):
        response.headers["Content-Type"] = "application/json; charset=utf-8"
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["X-Content-Type-Options"] = "nosniff"
    return response


@app.route("/")
def index():
    return send_from_directory(ROOT / "ui", "index.html")


@app.route("/api/info")
def api_info():
    return jsonify({
        "artifact_version": _state.get("artifact_version"),
        "provider": _state.get("provider_name"),
        "model": _state.get("model_name"),
    })


@app.route("/api/chat", methods=["POST", "OPTIONS"])
def api_chat():
    # Handle CORS preflight (needed for cross-origin requests via tunnel)
    if request.method == "OPTIONS":
        return jsonify({"ok": True})

    body = request.get_json(force=True, silent=True) or {}
    user_text = (body.get("message") or "").strip()
    if not user_text:
        return jsonify({"error": "empty message", "reply": "Tin nhắn trống.", "status": "error", "tool_calls": [], "tool_events": []}), 400

    _state["turn_index"] += 1
    history: list[dict[str, str]] = _state["history"]
    messages = [
        {"role": "system", "content": _state["system_prompt"]},
        *trim_history(history, _state["history_window"]),
        {"role": "user", "content": user_text},
    ]

    turn_record: dict[str, Any] = {
        "turn_index": _state["turn_index"],
        "started_at": now_iso(),
        "user": user_text,
        "status": "started",
        "assistant_text": None,
        "rounds": [],
        "tool_events": [],
    }

    try:
        result = run_model_tool_loop(
            provider=_state["provider"],
            messages=messages,
            tools=_state["openai_tools"],
            model=_state["model"],
            max_tool_rounds=_state["max_tool_rounds"],
        )
        turn_record.update(result)
        assistant_text = result["assistant_text"]

        history.append({"role": "user", "content": user_text})
        history.append({"role": "assistant", "content": assistant_text})

        # Build tool call summary for UI
        tool_calls_summary = []
        for round_data in result.get("rounds", []):
            for tc in round_data.get("tool_calls", []):
                tool_calls_summary.append(tc)

        response_payload = {
            "reply": assistant_text,
            "status": result["status"],
            "tool_calls": tool_calls_summary,
            "tool_events": result.get("tool_events", []),
        }
    except Exception as exc:
        turn_record.update({
            "status": "provider_error",
            "error": f"{type(exc).__name__}: {str(exc)}",
        })
        response_payload = {
            "reply": f"⚠️ Lỗi: {turn_record['error']}",
            "status": "error",
            "tool_calls": [],
            "tool_events": [],
        }

    turn_record["ended_at"] = now_iso()
    _state["transcript"]["turns"].append(turn_record)
    write_transcript(_state["transcript_path"], _state["transcript"])

    return jsonify(response_payload)


@app.route("/api/reset", methods=["POST"])
def api_reset():
    _state["history"] = []
    _state["turn_index"] = 0
    return jsonify({"ok": True})


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Research Agent Web UI")
    parser.add_argument("--provider", choices=["openrouter", "openai", "anthropic", "gemini"], required=True)
    parser.add_argument("--model", default=None)
    parser.add_argument("--version", required=True)
    parser.add_argument("--system-prompt", type=Path, default=ARTIFACTS_DIR / "system_prompt.md")
    parser.add_argument("--tools", type=Path, default=ARTIFACTS_DIR / "tools.yaml")
    parser.add_argument("--history-window", type=int, default=5)
    parser.add_argument("--max-tool-rounds", type=int, default=4)
    parser.add_argument("--port", type=int, default=5000)
    args = parser.parse_args()

    init_state(args)
    print(f"[OK] Research Agent UI: http://localhost:{args.port}")
    print(f"     Provider: {args.provider} | Model: {_state['model_name']}")
    print(f"     Artifact version: {_state['artifact_version']}")
    app.run(debug=False, port=args.port)
