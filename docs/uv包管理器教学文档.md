# uv 包管理器教学文档

## 常用命令

```powershell
uv --version
uv sync
uv run python --version
uv run python src/main.py
uv lock
```

- `pyproject.toml` 声明项目需要的 Python 版本和依赖。
- `uv.lock` 记录精确解析结果，必须提交到 Git。
- `.venv` 是本机虚拟环境，不得提交。
- `uv run` 会自动使用项目虚拟环境，一般不需要手动激活。

Step 1 的依赖列表为空，启动入口只使用 Python 标准库；第三方依赖从后续步骤开始引入。
