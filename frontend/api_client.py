from __future__ import annotations

import os
from typing import Iterator

import requests


API_BASE_URL = os.getenv("BACKEND_API_URL", "http://localhost:8000/api").rstrip("/")


class ApiError(RuntimeError):
    pass


def _request(method: str, path: str, **kwargs):
    url = f"{API_BASE_URL}{path}"
    try:
        response = requests.request(method, url, timeout=30, **kwargs)
        response.raise_for_status()
        if response.content:
            return response.json()
        return None
    except requests.RequestException as exc:
        detail = getattr(exc.response, "text", "") if getattr(exc, "response", None) is not None else ""
        raise ApiError(f"API 请求失败：{url}\n{detail or exc}") from exc


def create_user(username: str) -> dict:
    return _request("POST", "/users", json={"username": username})


def list_models() -> list[dict]:
    return _request("GET", "/models")


def list_prompts() -> list[dict]:
    return _request("GET", "/prompts")


def create_conversation(user_id: int, model_name: str, prompt_role: str) -> dict:
    return _request(
        "POST",
        "/conversations",
        json={"user_id": user_id, "model_name": model_name, "prompt_role": prompt_role},
    )


def list_conversations(user_id: int) -> list[dict]:
    return _request("GET", "/conversations", params={"user_id": user_id})


def get_conversation(conversation_id: int, user_id: int) -> dict:
    return _request("GET", f"/conversations/{conversation_id}", params={"user_id": user_id})


def rename_conversation(conversation_id: int, user_id: int, title: str) -> dict:
    return _request("PATCH", f"/conversations/{conversation_id}/title", json={"user_id": user_id, "title": title})


def update_conversation_model(conversation_id: int, user_id: int, model_name: str) -> dict:
    return _request("PATCH", f"/conversations/{conversation_id}/model", json={"user_id": user_id, "model_name": model_name})


def update_conversation_prompt_role(conversation_id: int, user_id: int, prompt_role: str) -> dict:
    return _request(
        "PATCH",
        f"/conversations/{conversation_id}/prompt-role",
        json={"user_id": user_id, "prompt_role": prompt_role},
    )


def stream_chat(
    user_id: int,
    conversation_id: int,
    message: str,
    model_name: str,
    prompt_role: str,
) -> Iterator[str]:
    url = f"{API_BASE_URL}/chat/stream"
    payload = {
        "user_id": user_id,
        "conversation_id": conversation_id,
        "message": message,
        "model_name": model_name,
        "prompt_role": prompt_role,
    }
    try:
        with requests.post(url, json=payload, stream=True, timeout=(5, None)) as response:
            response.raise_for_status()
            for chunk in response.iter_content(chunk_size=1, decode_unicode=True):
                if chunk:
                    yield chunk
    except requests.RequestException as exc:
        detail = getattr(exc.response, "text", "") if getattr(exc, "response", None) is not None else ""
        raise ApiError(f"流式请求失败：{detail or exc}") from exc


def search_conversations(user_id: int, keyword: str) -> list[dict]:
    return _request("GET", "/search", params={"user_id": user_id, "keyword": keyword})


def get_stats(user_id: int) -> dict:
    return _request("GET", "/stats", params={"user_id": user_id})


def export_url(conversation_id: int, user_id: int, fmt: str) -> str:
    return f"{API_BASE_URL}/export/{conversation_id}?user_id={user_id}&format={fmt}"


def archive_conversation(conversation_id: int, user_id: int) -> dict:
    return _request("DELETE", f"/conversations/{conversation_id}", params={"user_id": user_id})

