# LLM Chat-bot

一个基于 FastAPI、Streamlit、SQLite、SQLAlchemy 和 LangChain 封装的本地化智能对话系统。项目支持多用户、多会话、多模型切换、Prompt 角色切换、流式输出、会话搜索、统计、导出、结构化日志和配置化模型接入。

## 功能

- 用户名进入系统，用户不存在时自动创建。
- 每个用户只能查看自己的会话。
- 支持新建、切换、重命名、归档历史会话。
- 每个会话独立保存上下文，默认携带最近 20 条消息。
- 支持 mock、Qwen、DeepSeek、OpenAI-compatible 模型配置。
- 缺少 API Key 时自动使用 mock 兜底，便于课程演示。
- 支持普通聊天接口和流式聊天接口。
- 支持 Prompt 角色列表、会话中途切换角色。
- 支持 SQLite LIKE 会话搜索。
- 支持会话统计、模型使用统计、角色使用统计和最近 7 天消息统计。
- 支持 Markdown、TXT、JSON 导出。
- 支持 JSON Lines 结构化日志，输出到控制台、`backend/logs/app.log`、`backend/logs/error.log`。

## 技术栈

- 后端：FastAPI、SQLAlchemy、Pydantic、LangChain、Loguru、Tenacity
- 前端：Streamlit、Requests、Pandas
- 数据库：SQLite
- 配置：`config.yaml`、`.env`

## 目录结构

```text
backend/
  app/
    api/
    core/
    db/
    schemas/
    services/
    llm/
  data/
  logs/
  tests/
  requirements.txt
frontend/
  components/
  pages/
  api_client.py
  streamlit_app.py
config.yaml
.env.example
run.md
```

## 安装

```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r backend\requirements.txt
```

## 配置

复制 `.env.example` 为 `.env`，按需填写 API Key。

```env
DASHSCOPE_API_KEY=your_dashscope_api_key
DEEPSEEK_API_KEY=your_deepseek_api_key
OPENAI_API_KEY=your_openai_api_key
DEFAULT_MODEL=mock
BACKEND_API_URL=http://localhost:8000/api
```

模型、Prompt 角色、数据库路径、超时和重试次数在 `config.yaml` 中维护。

## 初始化数据库

```powershell
cd backend
python -m app.db.init_db
```

## 启动后端

```powershell
cd backend
uvicorn app.main:app --reload --port 8000
```

## 启动前端

```powershell
cd frontend
streamlit run streamlit_app.py
```

浏览器打开：

```text
http://localhost:8501
```

## 测试

```powershell
cd backend
pytest
```

## API 概览

- `POST /api/users`
- `POST /api/conversations`
- `GET /api/conversations?user_id=1`
- `GET /api/conversations/{conversation_id}?user_id=1`
- `PATCH /api/conversations/{conversation_id}/title`
- `PATCH /api/conversations/{conversation_id}/model`
- `PATCH /api/conversations/{conversation_id}/prompt-role`
- `POST /api/chat`
- `POST /api/chat/stream`
- `GET /api/prompts`
- `GET /api/models`
- `GET /api/search?user_id=1&keyword=...`
- `GET /api/stats?user_id=1`
- `GET /api/export/{conversation_id}?user_id=1&format=markdown`

## 后续扩展

- 将 SQLite 搜索升级为 FTS5 或向量检索。
- 增加正式登录、OAuth 或学校统一认证。
- 增加会话摘要、Token 费用统计、Docker 部署和管理员后台。

