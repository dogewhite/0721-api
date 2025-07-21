#!/usr/bin/env python3
"""
配置读取测试脚本
"""

import sys
import os

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config_loader import config_loader

def test_config_loading():
    """测试配置加载功能"""
    print("🧪 开始测试配置加载功能...")
    print("=" * 50)
    
    try:
        # 测试OSS配置
        print("📦 测试OSS配置加载...")
        oss_config = config_loader.load_oss_config()
        print(f"✅ OSS配置加载成功:")
        print(f"   - Endpoint: {oss_config.get('OSS_ENDPOINT', 'N/A')}")
        print(f"   - Bucket: {oss_config.get('OSS_BUCKET', 'N/A')}")
        print(f"   - Access Key ID: {oss_config.get('OSS_ACCESS_KEY_ID', 'N/A')[:10]}...")
        print()
        
        # 测试SQL配置
        print("🗄️ 测试PostgreSQL配置加载...")
        sql_config = config_loader.load_sql_config()
        print(f"✅ SQL配置加载成功:")
        print(f"   - Account: {sql_config.get('account', 'N/A')}")
        print(f"   - Address: {sql_config.get('address', 'N/A')}")
        print(f"   - Port: {sql_config.get('port', 'N/A')}")
        print()
        
        # 测试数据库URL生成
        print("🔗 测试数据库URL生成...")
        db_url = config_loader.get_database_url()
        print(f"✅ 数据库URL生成成功:")
        print(f"   - URL: {db_url}")
        print()
        
        # 测试OSS配置字典
        print("📋 测试OSS配置字典...")
        oss_dict = config_loader.get_oss_config_dict()
        print(f"✅ OSS配置字典生成成功:")
        for key, value in oss_dict.items():
            if 'secret' in key.lower():
                print(f"   - {key}: {str(value)[:10]}...")
            else:
                print(f"   - {key}: {value}")
        print()
        
        print("🎉 所有配置测试通过！")
        return True
        
    except Exception as e:
        print(f"❌ 配置测试失败: {e}")
        return False

def test_oss_connection():
    """测试OSS连接"""
    print("🔗 测试OSS连接...")
    try:
        from oss_utils import oss_manager
        
        # 测试OSS管理器初始化
        print("✅ OSS管理器初始化成功")
        
        # 测试文件存在性检查（使用一个不存在的文件）
        exists = oss_manager.file_exists("test_file.txt")
        print(f"✅ OSS连接测试成功，文件存在性检查: {exists}")
        
        return True
        
    except Exception as e:
        print(f"❌ OSS连接测试失败: {e}")
        return False

def test_database_connection():
    """测试数据库连接"""
    print("🗄️ 测试数据库连接...")
    try:
        from models import engine
        
        # 测试数据库连接
        with engine.connect() as conn:
            result = conn.execute("SELECT 1")
            print("✅ 数据库连接测试成功")
        
        return True
        
    except Exception as e:
        print(f"❌ 数据库连接测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🚀 智能JD分析模块 - 配置测试")
    print("=" * 50)
    
    # 测试配置加载
    config_ok = test_config_loading()
    
    if config_ok:
        # 测试OSS连接
        oss_ok = test_oss_connection()
        
        # 测试数据库连接
        db_ok = test_database_connection()
        
        print("\n" + "=" * 50)
        print("📊 测试结果汇总:")
        print(f"   - 配置加载: {'✅ 通过' if config_ok else '❌ 失败'}")
        print(f"   - OSS连接: {'✅ 通过' if oss_ok else '❌ 失败'}")
        print(f"   - 数据库连接: {'✅ 通过' if db_ok else '❌ 失败'}")
        
        if all([config_ok, oss_ok, db_ok]):
            print("\n🎉 所有测试通过！系统配置正确。")
        else:
            print("\n⚠️ 部分测试失败，请检查配置。")
    else:
        print("\n❌ 配置加载失败，无法进行后续测试。")

if __name__ == "__main__":
    main() 