#!/usr/bin/env python3
"""
DeepSeek客户端测试脚本
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from deepseek_client import DeepSeekClient
from config_loader import config_loader

def test_deepseek_client():
    """测试DeepSeek客户端"""
    try:
        # 获取API密钥
        api_key = config_loader.get_deepseek_api_key()
        print(f"API密钥: {api_key[:20]}...")
        
        if api_key == "sk-your-deepseek-api-key-here":
            print("⚠️  请先在 config_loader.py 中配置实际的 DeepSeek API 密钥")
            return
        
        # 创建客户端
        client = DeepSeekClient(api_key)
        print("DeepSeek客户端创建成功")
        
        # 测试简单对话
        prompt = "请简单介绍一下你自己"
        system_prompt = "你是一个有用的AI助手"
        
        print(f"\n发送请求: {prompt}")
        response = client.simple_chat(prompt, system_prompt)
        print(f"收到响应: {response}")
        
        # 测试DeepSeek-R1推理模型
        print(f"\n测试DeepSeek-R1推理模型...")
        reasoning_prompt = "请分析一下：为什么很多公司要求前端工程师既懂React又懂Vue？"
        r1_response = client.simple_chat(reasoning_prompt, system_prompt, model="deepseek-reasoner")
        print(f"DeepSeek-R1响应: {r1_response}")
        
        # 测试JD分析
        jd_prompt = """
请分析以下招聘JD，提取关键信息并生成搜索关键词：

JD内容：
招聘Python后端开发工程师，要求熟悉Django、Flask框架，有数据库优化经验，3年以上开发经验。

补充说明：
希望候选人有微服务架构经验。

请按照以下JSON格式返回结果：

{
    "job_title": "职位名称",
    "skills": ["技能1", "技能2", "技能3"],
    "products": ["产品/技术1", "产品/技术2"],
    "companies": ["相关企业1", "相关企业2"],
    "keywords": {
        "position": ["精准关键词1", "精准关键词2"],
        "industry": ["行业关键词1", "行业关键词2"],
        "company": ["公司关键词1", "公司关键词2"],
        "product": ["产品关键词1", "产品关键词2"],
        "skill": ["技能关键词1", "技能关键词2"]
    },
    "tagging_dict": {
        "companies": ["企业关键词1", "企业关键词2"],
        "skills": ["技能关键词1", "技能关键词2"],
        "products": ["产品关键词1", "产品关键词2"],
        "industry": ["行业关键词1", "行业关键词2"]
    }
}
"""
        
        print(f"\n发送JD分析请求...")
        jd_response = client.simple_chat(jd_prompt, "你是一个专业的招聘JD分析专家，擅长提取关键信息和生成搜索关键词。请严格按照JSON格式返回结果。")
        print(f"JD分析响应: {jd_response}")
        
        print("\n✅ DeepSeek客户端测试成功！")
        
    except Exception as e:
        print(f"❌ DeepSeek客户端测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_deepseek_client() 