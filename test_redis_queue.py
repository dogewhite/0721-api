#!/usr/bin/env python3
# -*- coding: utf-8 -*-

Redis队列测试脚本
用于检查trigger_queue队列的状态和内容
import redis
import json
from datetime import datetime

# Redis配置
REDIS_HOST = "localhost"  # 测试环境使用localhost
REDIS_PORT = 6379
REDIS_DB = 0
REDIS_QUEUE = "trigger_queue"

def test_redis_connection():
    """测试Redis连接"""
    try:
        client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, decode_responses=True)
        client.ping()
        print("✅ Redis连接成功")
        return client
    except Exception as e:
        print(f"❌ Redis连接失败: {e}")
        return None

def check_queue_status(client):
    """检查队列状态"""
    try:
        # 获取队列长度
        queue_length = client.llen(REDIS_QUEUE)
        print(f"\n📊 队列状态:)
        print(f"   队列名称: {REDIS_QUEUE})
        print(f"   队列长度: {queue_length}")
        
        if queue_length > 0:
            # 获取所有任务（不删除）
            raw_tasks = client.lrange(REDIS_QUEUE, 0, -1)
            print(f"\n📋 队列内容:")
            
            for i, raw_task in enumerate(raw_tasks, 1):
                try:
                    task = json.loads(raw_task)
                    print(f"\n   任务 {i}:")
                    print(f"     主搜索: {task.get('main', '无')}")
                    print(f"     职位: {task.get('position', '无')}")
                    print(f"     公司: {task.get('company', '无')}")
                    print(f"     时间: {task.get('timestamp', '未知')}")
                except json.JSONDecodeError:
                    print(f"   任务 {i}: 无法解析数据 - {raw_task}")
        else:
            print("\n📭 队列为空")
            
    except Exception as e:
        print(f"❌ 检查队列失败: {e}")

def add_test_task(client):
    """添加测试任务"""
    try:
        test_task = {
            "main": "测试关键词1 测试关键词2",
            "position": "测试职位2",
            "company": "测试公司2",
            "timestamp": datetime.now().isoformat()
        }
        
        client.rpush(REDIS_QUEUE, json.dumps(test_task, ensure_ascii=False))
        print(f"\n✅ 测试任务已添加到队列")
        print(f"   任务内容: {test_task}")
        
    except Exception as e:
        print(f"❌ 添加测试任务失败: {e}")

def clear_queue(client):
    """清空队列"""
    try:
        deleted_count = client.delete(REDIS_QUEUE)
        print(f"\n🗑️ 队列已清空，删除了 {deleted_count} 个任务")
    except Exception as e:
        print(f"❌ 清空队列失败: {e}")

def main():
    """主函数"""
    print("🔍 Redis队列测试工具")
    print("=" * 50)
    
    # 测试连接
    client = test_redis_connection()
    if not client:
        return
    
    while True:
        print("\n" + "=" * 50)
        print("请选择操作:)
        print("1. 查看队列状态)
        print("2. 添加测试任务)
        print(3. 清空队列)
        print(4. 退出)
        
        choice = input("\n请输入选项 (1-4): ").strip()
        
        if choice == '1':
            check_queue_status(client)
        elif choice == '2':
            add_test_task(client)
        elif choice == '3':
            confirm = input("确定要清空队列吗？(y/N): ").strip().lower()
            if confirm == 'y':
                clear_queue(client)
            else:
                print("操作已取消")
        elif choice == '4':
            print("👋 再见！")
            break
        else:
            print("❌ 无效选项，请重新选择")

if __name__ == "__main__":
    main() 