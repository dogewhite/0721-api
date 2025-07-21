#!/usr/bin/env python3
"""
生产环境配置文件
"""

import os

# 生产环境配置
PRODUCTION_CONFIG = {
    # API域名
    'API_BASE_URL': 'https://api.zxyang.xin',
    
    # 数据库配置
    'DB_HOST': os.environ.get('DB_HOST', 'localhost'),
    'DB_PORT': os.environ.get('DB_PORT', '5432'),
    'DB_USER': os.environ.get('DB_USER', ''),
    'DB_PASSWORD': os.environ.get('DB_PASSWORD', ''),
    'DB_NAME': os.environ.get('DB_NAME', ''),
    
    # OSS配置
    'OSS_ENDPOINT': os.environ.get('OSS_ENDPOINT', ''),
    'OSS_ACCESS_KEY_ID': os.environ.get('OSS_ACCESS_KEY_ID', ''),
    'OSS_ACCESS_KEY_SECRET': os.environ.get('OSS_ACCESS_KEY_SECRET', ''),
    'OSS_BUCKET': os.environ.get('OSS_BUCKET', ''),
    
    # API密钥
    'DEEPSEEK_API_KEY': os.environ.get('DEEPSEEK_API_KEY', ''),
    'KIMI_API_KEY': os.environ.get('KIMI_API_KEY', ''),
    
    # JWT配置
    'JWT_SECRET_KEY': os.environ.get('JWT_SECRET_KEY', 'your-secret-key'),
    
    # Redis配置
    'REDIS_HOST': os.environ.get('REDIS_HOST', 'localhost'),
    'REDIS_PORT': int(os.environ.get('REDIS_PORT', 6379)),
    'REDIS_DB': int(os.environ.get('REDIS_DB', 0)),
    
    # 环境标识
    'ENVIRONMENT': 'production'
}

def get_production_config():
    """获取生产环境配置"""
    return PRODUCTION_CONFIG

def is_production():
    """判断是否为生产环境"""
    return os.environ.get('ENVIRONMENT', 'development') == 'production' 