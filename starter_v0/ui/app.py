"""
Day 04 Research Agent — Streamlit demo UI.

Run from starter_v0/:
  streamlit run ui/app.py
"""
from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from chat import (  # noqa: E402
    json_text,
    now_iso,
    run_model_tool_loop,
    safe_slug,
    trim_history,
    write_transcript,
)
from env_loader import load_lab_env  # noqa: E402
from providers import make_provider  # noqa: E402
from tools import load_tool_declarations, to_openai_tools  # noqa: E402
from versioning import artifact_version_dict, build_artifact_version  # noqa: E402

ARTIFACTS_DIR = ROOT / "artifacts"
TRANSCRIPTS_DIR = ROOT / "transcripts"
DEFAULT_SYSTEM_PROMPT = ARTIFACTS_DIR / "system_prompt.md"
DEFAULT_TOOLS = ARTIFACTS_DIR / "tools.yaml"

DEMO_PROMPTS = [
    ("Tin AI hôm nay", "Tin tức AI hôm nay có gì nổi bật?"),
    ("Tweet thiếu handle", "Tóm tắt 5 tweet mới nhất giúp mình"),
    ("Đăng Telegram", "Đăng bản tin này lên Telegram giúp mình"),
]

load_lab_env(ROOT)


def init_session_state() -> None:
    defaults: dict[str, Any] = {
        "chat_history": [],
        "model_messages": [],
        "turn_index": 0,
        "pending_prompt": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value
    if "transcript" not in st.session_state:
        reset_transcript(st.session_state.get("version_label", "v3"))


def reset_transcript(version_label: str) -> None:
    artifact_version = build_artifact_version(version_label, DEFAULT_SYSTEM_PROMPT, DEFAULT_TOOLS)
    timestamp = datetime.now().strftime("%Y%m%dT%H%M%S%f")
    provider_name = st.session_state.get("provider_name", "openrouter")
    transcript_id = "_".join([safe_slug(version_label), safe_slug(provider_name), timestamp])
    path = TRANSCRIPTS_DIR / f"{transcript_id}.transcript.json"
    st.session_state.transcript_path = path
    st.session_state.transcript = {
        "transcript_id": transcript_id,
        **artifact_version_dict(artifact_version),
        "provider": provider_name,
        "model": None,
        "system_prompt": str(DEFAULT_SYSTEM_PROMPT),
        "tools": str(DEFAULT_TOOLS),
        "history_window": st.session_state.get("history_window", 5),
        "max_tool_rounds": st.session_state.get("max_tool_rounds", 4),
        "created_at": now_iso(),
        "updated_at": now_iso(),
        "turns": [],
        "source": "streamlit_ui",
    }


def clear_chat(version_label: str) -> None:
    st.session_state.chat_history = []
    st.session_state.model_messages = []
    st.session_state.turn_index = 0
    reset_transcript(version_label)


@st.cache_resource
def load_stack(provider_name: str) -> tuple[Any, list[dict[str, Any]], str]:
    load_lab_env(ROOT)
    system_prompt = DEFAULT_SYSTEM_PROMPT.read_text(encoding="utf-8")
    declarations = load_tool_declarations(DEFAULT_TOOLS)
    openai_tools = to_openai_tools(declarations)
    provider = make_provider(provider_name)
    return provider, openai_tools, system_prompt


def run_preflight(provider_name: str, model: str | None) -> tuple[bool, str]:
    try:
        provider, openai_tools, system_prompt = load_stack(provider_name)
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": "Tweet mới nhất của Sam Altman là gì?"},
        ]
        response = provider.complete(messages, openai_tools, model=model, temperature=0.0)
        if not response.tool_calls:
            return False, "Provider did not return tool_calls."
        first = response.tool_calls[0]
        selected = model or getattr(provider, "default_model", "default")
        return True, f"OK model={selected} tool={first.name}"
    except Exception as exc:
        return False, f"{type(exc).__name__}: {exc}"


def render_tool_trace(rounds: list[dict[str, Any]], tool_events: list[dict[str, Any]]) -> None:
    if rounds:
        with st.expander("Tool rounds", expanded=True):
            for round_record in rounds:
                st.caption(f"Round {round_record.get('round', '?')}")
                calls = round_record.get("tool_calls") or []
                if calls:
                    st.markdown("**Calls**")
                    st.code(json.dumps(calls, ensure_ascii=False, indent=2), language="json")
                results = round_record.get("tool_results") or []
                if results:
                    st.markdown("**Results**")
                    st.code(json_text(results, max_chars=8000), language="json")
    elif tool_events:
        with st.expander("Tool events", expanded=True):
            st.code(json_text(tool_events, max_chars=8000), language="json")


def process_user_message(
    user_text: str,
    *,
    provider_name: str,
    version_label: str,
    model: str | None,
    history_window: int,
    max_tool_rounds: int,
) -> None:
    provider, openai_tools, system_prompt = load_stack(provider_name)
    selected_model = model or getattr(provider, "default_model", None)
    st.session_state.transcript["provider"] = provider_name
    st.session_state.transcript["model"] = selected_model

    st.session_state.chat_history.append({"role": "user", "content": user_text})
    st.session_state.turn_index += 1

    messages = [
        {"role": "system", "content": system_prompt},
        *trim_history(st.session_state.model_messages, history_window),
        {"role": "user", "content": user_text},
    ]

    turn_record: dict[str, Any] = {
        "turn_index": st.session_state.turn_index,
        "started_at": now_iso(),
        "user": user_text,
        "status": "started",
        "assistant_text": None,
        "rounds": [],
        "tool_events": [],
    }

    try:
        result = run_model_tool_loop(
            provider=provider,
            messages=messages,
            tools=openai_tools,
            model=model,
            max_tool_rounds=max_tool_rounds,
            verbose=False,
        )
        turn_record.update(result)
        assistant_text = result.get("assistant_text") or ""
        status = result.get("status", "answered")

        entry: dict[str, Any] = {
            "role": "assistant",
            "content": assistant_text,
            "status": status,
            "rounds": result.get("rounds", []),
            "tool_events": result.get("tool_events", []),
        }
        st.session_state.chat_history.append(entry)
        st.session_state.model_messages.append({"role": "user", "content": user_text})
        st.session_state.model_messages.append({"role": "assistant", "content": assistant_text})
    except Exception as exc:
        turn_record.update({
            "status": "provider_error",
            "error": f"{type(exc).__name__}: {exc}",
        })
        st.session_state.chat_history.append({
            "role": "assistant",
            "content": f"Lỗi: {exc}",
            "status": "provider_error",
            "rounds": [],
            "tool_events": [],
        })

    turn_record["ended_at"] = now_iso()
    st.session_state.transcript["turns"].append(turn_record)
    write_transcript(st.session_state.transcript_path, st.session_state.transcript)


def render_sidebar() -> tuple[str, str, str | None, int, int]:
    st.sidebar.header("Cấu hình")
    provider_name = st.sidebar.selectbox(
        "Provider",
        ["openrouter", "openai", "anthropic", "gemini"],
        index=0,
    )
    version_label = st.sidebar.text_input("Version label", value=st.session_state.get("version_label", "v3"))
    st.session_state.version_label = version_label

    artifact_version = build_artifact_version(version_label, DEFAULT_SYSTEM_PROMPT, DEFAULT_TOOLS)
    st.sidebar.caption(f"artifact_version: `{artifact_version.artifact_version}`")

    model_override = st.sidebar.text_input("Model override (optional)", value="")
    model = model_override.strip() or None

    history_window = st.sidebar.slider("History window (pairs)", 1, 10, 5)
    max_tool_rounds = st.sidebar.slider("Max tool rounds", 1, 8, 4)
    st.session_state.history_window = history_window
    st.session_state.max_tool_rounds = max_tool_rounds
    st.session_state.provider_name = provider_name

    if st.sidebar.button("Kiểm tra kết nối"):
        ok, msg = run_preflight(provider_name, model)
        if ok:
            st.sidebar.success(msg)
        else:
            st.sidebar.error(msg)

    st.sidebar.divider()
    st.sidebar.subheader("Demo nhanh")
    for label, prompt in DEMO_PROMPTS:
        if st.sidebar.button(label, use_container_width=True):
            st.session_state.pending_prompt = prompt

    if st.sidebar.button("Xóa hội thoại", type="secondary", use_container_width=True):
        clear_chat(version_label)
        st.rerun()

    transcript_path = st.session_state.get("transcript_path")
    if transcript_path:
        st.sidebar.caption(f"Transcript: `{transcript_path.name}`")

    return provider_name, version_label, model, history_window, max_tool_rounds


def render_chat_history() -> None:
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg["role"] == "assistant":
                status = msg.get("status")
                if status == "waiting_for_user":
                    st.info("Agent đang chờ bạn bổ sung thông tin (clarify).")
                elif status == "max_tool_rounds":
                    st.warning("Đã đạt giới hạn vòng tool.")
                render_tool_trace(msg.get("rounds", []), msg.get("tool_events", []))


def main() -> None:
    st.set_page_config(page_title="Research Agent Demo", page_icon="🔬", layout="wide")
    init_session_state()

    provider_name, version_label, model, history_window, max_tool_rounds = render_sidebar()

    st.title("Day 04 — Research Agent Demo")
    st.caption(f"Provider: **{provider_name}** · Version: **{version_label}**")

    render_chat_history()

    prompt = st.chat_input("Nhập câu hỏi research...")
    if st.session_state.pending_prompt:
        prompt = st.session_state.pending_prompt
        st.session_state.pending_prompt = None

    if prompt:
        with st.spinner("Agent đang xử lý..."):
            process_user_message(
                prompt.strip(),
                provider_name=provider_name,
                version_label=version_label,
                model=model,
                history_window=history_window,
                max_tool_rounds=max_tool_rounds,
            )
        st.rerun()


if __name__ == "__main__":
    main()
