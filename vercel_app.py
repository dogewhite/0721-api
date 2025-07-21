#!/usr/bin/env python3
"""
Vercel部署专用的FastAPI应用入口
"""

import os
import sys
from pathlib import Path

# 添加当前目录到Python路径
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# 设置环境变量
os.environ.setdefault("VERCEL_ENV", "production")

# 导入主应用
from api import app

# 为了兼容Vercel，我们需要确保应用可以正确处理请求
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000))) 