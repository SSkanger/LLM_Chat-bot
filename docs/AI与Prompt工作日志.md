# AI / Vibe Coding 工作日志

## Step 2：项目骨架实现

- 用户 Prompt：根据老师要求的 Step2 修改项目，并将修改后的项目直接 Git 提交。
- 需求来源：老师《实施步骤计划》v1.2 的 Step 2。
- 实现范围：Pydantic 数据模型、异步存储 ABC、配置管理、统一 UI 协议、Rich + prompt_toolkit TUI 骨架。
- MVP 决策：五项菜单功能本步只返回 stub 提示，不提前实现 Step 3 之后的数据库和业务功能。
- 兼容性决策：保留现有 FastAPI/Streamlit 代码；将其依赖纳入 pyproject，避免 uv 同步后破坏 Web 应用环境。
- 验证命令：`uv run python src/main.py --check`、`uv run pytest`。
- 计划标签：`step-2-skeleton`。
