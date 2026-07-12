# LangChain Chat / LLM Chat-bot

> 基于 LangChain 的多轮会话系统（教学项目）

本项目按老师的工程化步骤推进，每一步均提供可运行、可验证的 MVP，并使用 Git commit 与 tag 保存回退点。当前仓库同时保留已实现的 FastAPI、Streamlit、SQLite 聊天系统。

## Step 6 验收

环境要求：Python 3.12（要求 3.10 及以上）和 uv。

```powershell
uv sync
uv run python scripts/init_db.py
uv run python scripts/chat_engine_demo.py
uv run python src/main.py --check
uv run python src/main.py
```

数据库初始化命令会创建 SQLite 表并加载系统预设。对话引擎演示脚本会使用真实 OpenAI 兼容配置或本地 mock，完成两轮异步流式对话并输出 Token 用量。Step7 才会把引擎接入 TUI 的“开始对话”。

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
- 工程管理：uv、Git、pytest、ruff

## 目录结构

```text
pyproject.toml
uv.lock
.env.example
config.yaml
config/
  presets.yaml
  logging.yaml
src/
  __init__.py
  main.py
  config_manager.py
  core/
    user_manager.py
    preset_manager.py
    chat_engine.py
  models/
  storage/
    sqlite_backend.py
    factory.py
  interface/
  ui/tui/
scripts/
  init_db.py
docs/
  需求说明文档.md
  实施步骤计划.md
  需求变更与扩展登记.md
  Git命令与操作教学.md
  uv包管理器教学文档.md
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
run.md
```

## 安装

```powershell
uv venv .venv --python 3.12
uv pip install -r backend\requirements.txt
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
- 按 `docs/实施步骤计划.md` 在 Step 15 完成 dev/test/prod 多环境隔离。

## 配置分层

| 层 | 文件 | 内容 | 是否提交 |
|---|---|---|---|
| 敏感配置 | `.env` | API Key、数据库密码 | 否 |
| 业务配置 | `config.yaml` | 模型、存储、超时等 | 是 |
| 日志配置 | `config/logging.yaml` | 日志格式与级别 | 是 |
| 业务数据 | `config/presets.yaml` | 系统内置预设角色 | 是 |

完整实施计划和工程说明位于 `docs/` 目录。
