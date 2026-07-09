from __future__ import annotations

import streamlit as st


def render_messages(messages: list[dict]) -> None:
    for message in messages:
        role = "assistant" if message["role"] == "assistant" else "user"
        with st.chat_message(role):
            if role == "assistant" and message.get("model_name"):
                st.caption(f"{message['model_name']} · {message.get('prompt_role') or ''}")
            st.markdown(message["content"])

