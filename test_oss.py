#!/usr/bin/env python3
"""
测试OSS连接和功能
"""

import sys
import os

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config_loader import config_loader
from oss_utils import oss_manager

def test_oss_connection():
    """测试OSS连接"""
    print("🔍 测试OSS连接...")
    
    try:
        # 获取OSS配置
        oss_config = config_loader.get_oss_config_dict()
        print(f"📋 OSS配置信息:")
        print(f"   - Endpoint: {oss_config['endpoint']}")
        print(f"   - Bucket: {oss_config['bucket']}")
        print(f"   - Access Key ID: {oss_config['access_key_id'][:8]}...")
        print(f"   - Access Key Secret: {oss_config['access_key_secret'][:8]}...")
        
        # 测试连接
        print("\n🔗 测试OSS连接...")
        bucket_info = oss_manager.bucket.get_bucket_info()
        print(f"✅ OSS连接成功!")
        print(f"   - Bucket名称: {bucket_info.name}")
        print(f"   - 创建时间: {bucket_info.creation_date}")
        print(f"   - 存储类型: {bucket_info.storage_class}")
        
        # 测试列出文件 (深度扫描)
        print("\n📁 [深度扫描] 测试列出仓库中所有的对象...")
        # 列出所有文件, 不使用 delimiter, 进行递归扫描
        result = oss_manager.bucket.list_objects()
        
        count = 0
        object_list = list(getattr(result, 'object_list', []))
        
        if not object_list:
            print("    -> 扫描结果为空，SDK未能从OSS列出任何对象。")
        else:
            print("  ✅ 成功列出所有对象:")
            for obj in object_list:
                print(f"    - {obj.key} ({obj.size} bytes)")
                count += 1
            print(f"\n  总计: {count} 个对象。")
        
        # 测试上传文件
        print("\n📤 测试上传文件...")
        test_content = "这是一个测试文件，用于验证OSS连接。".encode('utf-8')
        test_object_name = "test_connection.txt"
        
        try:
            oss_url = oss_manager.upload_bytes(test_content, test_object_name)
            print(f"✅ 文件上传成功!")
            print(f"   - 对象名: {test_object_name}")
            print(f"   - URL: {oss_url}")
            
            # 测试删除文件
            print("\n🗑️ 测试删除文件...")
            oss_manager.delete_file(test_object_name)
            print(f"✅ 文件删除成功!")
            
        except Exception as e:
            print(f"❌ 文件操作失败: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ OSS连接失败: {e}")
        return False

def test_oss_functions():
    """测试OSS功能"""
    print("\n🧪 测试OSS功能...")
    
    try:
        # 测试创建文件夹
        print("📁 测试创建文件夹...")
        folder_name = "test_folder/"
        oss_manager.bucket.put_object(folder_name, "")
        print(f"✅ 文件夹创建成功: {folder_name}")
        
        # 测试上传文件到文件夹
        print("📤 测试上传文件到文件夹...")
        file_content = "这是文件夹中的测试文件。".encode('utf-8')
        file_name = "test_folder/test_file.txt"
        oss_url = oss_manager.upload_bytes(file_content, file_name)
        print(f"✅ 文件上传成功: {file_name}")
        
        # 测试列出文件夹内容
        print("📋 测试列出文件夹内容...")
        result = oss_manager.bucket.list_objects(prefix="test_folder/", delimiter='/')
        print(f"✅ 文件夹内容:")
        for obj in getattr(result, 'object_list', []):
            if obj.key.endswith('/'): continue # Skip the folder marker itself
            print(f"   - {obj.key}")
        
        # 清理测试文件
        print("🧹 清理测试文件...")
        oss_manager.delete_file(file_name)
        oss_manager.delete_file(folder_name)
        print("✅ 测试文件清理完成")
        
        return True
        
    except Exception as e:
        print(f"❌ OSS功能测试失败: {e}")
        return False

if __name__ == "__main__":
    print("🚀 开始OSS连接测试...")
    print("=" * 50)
    
    # 测试连接
    if test_oss_connection():
        # 测试功能
        test_oss_functions()
        print("\n🎉 所有测试完成!")
    else:
        print("\n💥 测试失败，请检查OSS配置!")
    
    print("=" * 50) 