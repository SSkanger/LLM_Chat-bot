# 运行说明

## Step 3：初始化异步 SQLite 数据库

```powershell
uv sync
uv run python scripts/init_db.py
```

默认数据库位于 `data/sqlite/app.db`。脚本会自动创建目录、执行迁移、创建全部业务表并写入内置 Prompt 预设；重复执行不会重复创建表或预设。

## Step 4：使用 TUI 用户管理

```powershell
uv run python src/main.py
```

进入主菜单后选择 `1 用户管理`，可以创建、切换和删除用户。删除操作需要二次确认，并会删除该用户的会话、消息、个人预设和配置。

## Step 5：使用预设 Prompt 管理

先创建或切换用户，再在主菜单选择 `3 预设管理`。系统内置预设对所有用户可见且不可修改；个人预设支持新增、编辑、删除、选择，也可以选择“不使用预设”。

## 1. 安装依赖

```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r backend\requirements.txt
```

## 2. 初始化数据库

```powershell
cd backend
python -m app.db.init_db
```

## 3. 启动后端

```powershell
cd backend
uvicorn app.main:app --reload --port 8000
```

健康检查：

```text
http://localhost:8000/health
```

## 4. 启动前端

另开一个终端：

```powershell
cd frontend
streamlit run streamlit_app.py
```

访问：

```text
http://localhost:8501
```

## 5. 无 API Key 演示

默认模型为 `mock`，无需 API Key 即可完成用户创建、会话创建、流式回复、搜索、统计和导出。

## 6. 接入真实模型

在 `.env` 中填写对应 Key，并在前端侧边栏选择模型：

```env
DASHSCOPE_API_KEY=...
DEEPSEEK_API_KEY=...
OPENAI_API_KEY=...
```
