#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import sys
import os

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from kimi_client import KimiClient

def test_json_fix():
    """测试JSON修复功能"""
    client = KimiClient()
    
    # 测试数据：模拟有问题的JSON
    problematic_json = '''
    {
      "work_experiences": [
        {
          "company_name": "某科技公司",
          "position": "高级前端工程师",
          "start_date": "2020-03-01",
          "end_date": null,
          "current_status": "在职",
          "job_description": "负责公司核心产品的前端架构设计和开发，包括：
1. 设计并实现响应式前端架构
2. 优化前端性能，提升用户体验
3. 指导初级开发人员
4. 参与技术选型和架构决策",
          "achievements": [
            "主导完成公司核心产品重构，性能提升50%",
            "获得年度优秀员工称号"
          ]
        }
      ]
    }
    '''
    
    print("原始JSON:")
    print(problematic_json)
    print("\n" + "="*50 + "\n")
    
    try:
        # 测试修复功能
        fixed_json = client._fix_work_experience_json(problematic_json)
        print("修复后的JSON:")
        print(fixed_json)
        print("\n" + "="*50 + "\n")
        
        # 测试解析
        parsed_data = json.loads(fixed_json)
        print("解析成功！")
        print(f"工作经历数量: {len(parsed_data.get('work_experiences', []))}")
        
        # 打印第一个工作经历
        if parsed_data.get('work_experiences'):
            work = parsed_data['work_experiences'][0]
            print(f"公司: {work.get('company_name')}")
            print(f"职位: {work.get('position')}")
            print(f"工作描述长度: {len(work.get('job_description', ''))}")
            
    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()

def test_string_fix():
    """测试字符串修复功能"""
    client = KimiClient()
    
    # 测试未闭合的字符串
    test_content = '{"name": "test", "description": "这是一个测试"'
    print(f"原始内容: {test_content}")
    
    fixed = client._fix_unclosed_strings(test_content)
    print(f"修复后: {fixed}")
    
    # 测试缺少逗号
    test_content2 = '{"key1": "value1" "key2": "value2"}'
    print(f"\n原始内容2: {test_content2}")
    
    fixed2 = client._fix_missing_commas(test_content2)
    print(f"修复后2: {fixed2}")

if __name__ == "__main__":
    print("测试JSON修复功能...")
    test_string_fix()
    print("\n" + "="*50 + "\n")
    test_json_fix() 