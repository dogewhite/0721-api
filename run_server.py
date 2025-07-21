#!/usr/bin/env python3
"""
智能JD分析API服务器启动脚本
"""

import uvicorn
import sys
import os
import socket

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from api import app

# 获取本机IP地址
hostname = socket.gethostname()
local_ip = socket.gethostbyname(hostname)

print("🚀 启动智能JD分析API服务器...")
print(f"📊 本地访问: http://localhost:8000")
print(f"📊 局域网访问: http://{local_ip}:8000")
print("📚 API文档: http:///docs")
print("🔧 配置信息:")
print("   - 数据库: PostgreSQL")
print("   - 文件存储: 阿里云OSS")
print("   - 图表生成: Kroki")
print("   - AI分析: DeepSeek R1")
print("-" * 50)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000) 