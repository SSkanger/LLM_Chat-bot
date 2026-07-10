# AI / Vibe Coding 工作日志

## Step 2：项目骨架实现

- 用户 Prompt：根据老师要求的 Step2 修改项目，并将修改后的项目直接 Git 提交。
- 需求来源：老师《实施步骤计划》v1.2 的 Step 2。
- 实现范围：Pydantic 数据模型、异步存储 ABC、配置管理、统一 UI 协议、Rich + prompt_toolkit TUI 骨架。
- MVP 决策：五项菜单功能本步只返回 stub 提示，不提前实现 Step 3 之后的数据库和业务功能。
- 兼容性决策：保留现有 FastAPI/Streamlit 代码；将其依赖纳入 pyproject，避免 uv 同步后破坏 Web 应用环境。
- 验证命令：`uv run python src/main.py --check`、`uv run pytest`。
- 计划标签：`step-2-skeleton`。

## Step 3：SQLite 后端与数据库初始化

- 用户 Prompt：根据老师要求的 Step3 修改项目，并将修改后的项目直接 Git 提交。
- 需求来源：老师《实施步骤计划》v1.2 的 Step 3。
- 实现范围：aiosqlite 后端、完整异步 CRUD、存储工厂、版本化迁移和初始化脚本。
- MVP 决策：初始化脚本自动创建全部表并幂等写入内置预设；Step4 才接入用户管理菜单。
- 验证命令：`uv run python scripts/init_db.py`、`uv run pytest`、`uv run ruff check src scripts tests`。
- 计划标签：`step-3-sqlite`。

## Step 4：用户管理与 TUI 菜单

- 用户 Prompt：根据老师要求的 Step4 修改项目，并将修改后的项目直接 Git 提交。
- 需求来源：老师《实施步骤计划》v1.2 的 Step 4 和需求 B1-B4。
- 实现范围：UserManager、TUI 用户子菜单、创建/切换/二次确认删除、当前用户上下文。
- 隔离策略：会话、预设、配置均通过当前用户 ID 查询；SQLite 外键负责删除关联数据。
- 验证命令：`uv run pytest`、`uv run python src/main.py --check`、真实 TUI 按键流程。
- 计划标签：`step-4-user-mgmt`。
