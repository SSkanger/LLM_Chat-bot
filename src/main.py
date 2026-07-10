"""langchain-chat 程序总入口。

Step 1 阶段：仅打印启动横幅，验证项目骨架可运行（零第三方依赖）。
运行方式：uv run python src/main.py
"""

import platform
import sys
from datetime import datetime


APP_NAME = "langchain-chat"
APP_VERSION = "0.1.0"
CURRENT_STEP = "Step 1：项目初始化与工程化配置"


def print_banner() -> None:
    """打印启动横幅。"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    banner = f"""
================================================================================
  {APP_NAME}  v{APP_VERSION}
================================================================================
  Python 版本  : {platform.python_version()}   ({sys.version.split()[0]})
  运行平台     : {platform.system()} {platform.machine()}
  启动时间     : {now}
  当前进度     : {CURRENT_STEP}
================================================================================
"""
    print(banner)
    print(f"[完成] {APP_NAME} 项目已启动（{CURRENT_STEP}）")


def main() -> None:
    """程序主函数。"""
    print_banner()


if __name__ == "__main__":
    main()
