#!/usr/bin/env python3
"""
LLM管理器测试脚本
"""

import sys
import os
import asyncio
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from llm_manager import llm_manager

def test_llm_manager():
    """测试LLM管理器"""
    try:
        print("🚀 开始测试LLM管理器...")
        
        # 1. 测试获取可用模型列表
        print("\n1. 获取可用模型列表:")
        models = llm_manager.get_available_models()
        for model in models:
            print(f"   - {model['name']} ({model['id']}) - {model['description']}")
        
        if not models:
            print("   ⚠️  没有可用的模型，请检查API密钥配置")
            return
        
        # 2. 测试同步聊天
        print("\n2. 测试同步聊天:")
        for model in models[:2]:  # 只测试前2个模型
            try:
                print(f"   正在测试 {model['name']}...")
                response = llm_manager.simple_chat(
                    "请用一句话介绍自己",
                    "你是一个专业的AI助手。",
                    model['id']
                )
                print(f"   {model['name']} 回复: {response[:100]}...")
            except Exception as e:
                print(f"   ❌ {model['name']} 测试失败: {e}")
        
        print("\n✅ 同步聊天测试完成")
        
    except Exception as e:
        print(f"❌ LLM管理器测试失败: {e}")
        import traceback
        traceback.print_exc()

async def test_llm_manager_async():
    """测试LLM管理器异步功能"""
    try:
        print("\n3. 测试异步聊天:")
        
        models = llm_manager.get_available_models()
        if not models:
            print("   ⚠️  没有可用的模型")
            return
        
        # 测试异步聊天
        for model in models[:2]:  # 只测试前2个模型
            try:
                print(f"   正在异步测试 {model['name']}...")
                response = await llm_manager.asimple_chat(
                    "请分析一下招聘行业的发展趋势",
                    "你是一个专业的招聘和人力资源助手。",
                    model['id']
                )
                print(f"   {model['name']} 异步回复: {response[:150]}...")
            except Exception as e:
                print(f"   ❌ {model['name']} 异步测试失败: {e}")
        
        print("\n✅ 异步聊天测试完成")
        
    except Exception as e:
        print(f"❌ 异步LLM管理器测试失败: {e}")
        import traceback
        traceback.print_exc()

def test_conversation():
    """测试多轮对话"""
    try:
        print("\n4. 测试多轮对话:")
        
        models = llm_manager.get_available_models()
        if not models:
            print("   ⚠️  没有可用的模型")
            return
        
        # 选择第一个可用模型进行多轮对话测试
        model = models[0]
        print(f"   使用模型: {model['name']}")
        
        # 第一轮对话
        messages = [
            {"role": "system", "content": "你是一个专业的招聘顾问。"},
            {"role": "user", "content": "我是一个3年经验的前端工程师，想要跳槽，有什么建议吗？"}
        ]
        
        response1 = llm_manager.chat(messages, model['id'])
        print(f"   第一轮回复: {response1[:200]}...")
        
        # 第二轮对话
        messages.append({"role": "assistant", "content": response1})
        messages.append({"role": "user", "content": "我主要做React开发，想要提升技能，你建议学习什么？"})
        
        response2 = llm_manager.chat(messages, model['id'])
        print(f"   第二轮回复: {response2[:200]}...")
        
        print("\n✅ 多轮对话测试完成")
        
    except Exception as e:
        print(f"❌ 多轮对话测试失败: {e}")
        import traceback
        traceback.print_exc()

async def main():
    """主测试函数"""
    print("🧪 LLM管理器功能测试")
    print("=" * 50)
    
    # 同步测试
    test_llm_manager()
    
    # 异步测试
    await test_llm_manager_async()
    
    # 多轮对话测试
    test_conversation()
    
    print("\n" + "=" * 50)
    print("🎉 所有测试完成！")

if __name__ == "__main__":
    asyncio.run(main()) 