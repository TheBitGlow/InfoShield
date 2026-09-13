"""Gearify - 脱敏工具 启动入口
"""

import sys
import os

# 确保当前目录位于 sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from gearify.ui.main_window import run_app

if __name__ == "__main__":
    run_app()
