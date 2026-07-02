"""
Copyright (c) 2026 八方网域-无涯
"""

import sys
import os

# 获取当前目录并加入路径
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from promptbreach.ui.gui import run


if __name__ == "__main__":
    run()
