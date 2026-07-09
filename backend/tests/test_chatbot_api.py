from __future__ import annotations


def create_user_and_conversation(client):
    user = client.post("/api/users", json={"username": "alice"}).json()
    conversation = client.post(
        "/api/conversations",
        json={"user_id": user["id"], "model_name": "mock", "prompt_role": "通用助手"},
    ).json()
    return user, conversation


def test_user_conversation_and_chat(client):
    user, conversation = create_user_and_conversation(client)

    response = client.post(
        "/api/chat",
        json={
            "user_id": user["id"],
            "conversation_id": conversation["conversation_id"],
            "message": "解释一下数据库索引",
            "model_name": "mock",
            "prompt_role": "数据库教授",
        },
    )

    assert response.status_code == 200
    assert "mock 模型" in response.json()["answer"]

    detail = client.get(
        f"/api/conversations/{conversation['conversation_id']}",
        params={"user_id": user["id"]},
    ).json()
    assert detail["title"].startswith("解释一下数据库索引")
    assert len(detail["messages"]) == 2


def test_stream_search_stats_and_export(client):
    user, conversation = create_user_and_conversation(client)

    with client.stream(
        "POST",
        "/api/chat/stream",
        json={
            "user_id": user["id"],
            "conversation_id": conversation["conversation_id"],
            "message": "写一个 FastAPI 示例",
            "model_name": "mock",
            "prompt_role": "编程助手",
        },
    ) as response:
        text = "".join(response.iter_text())

    assert response.status_code == 200
    assert "mock 模型" in text

    search = client.get("/api/search", params={"user_id": user["id"], "keyword": "FastAPI"}).json()
    assert search

    stats = client.get("/api/stats", params={"user_id": user["id"]}).json()
    assert stats["conversation_count"] == 1
    assert stats["message_count"] == 2
    assert stats["model_usage"]["mock"] == 1

    exported = client.get(
        f"/api/export/{conversation['conversation_id']}",
        params={"user_id": user["id"], "format": "markdown"},
    )
    assert exported.status_code == 200
    assert "# 写一个 FastAPI 示例" in exported.text

