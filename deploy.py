#!/usr/bin/env python3
"""
AI Auto Deploy - 智能一键部署工具
自动识别项目类型，一键部署到云服务器/Cloudflare/Vercel
"""

import sys
import os

# 添加 src 到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.cli import main

if __name__ == "__main__":
    main()
