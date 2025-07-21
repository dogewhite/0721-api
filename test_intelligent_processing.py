#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import sys
import os

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from kimi_client import KimiClient

def test_work_section_identification():
    """测试工作经历部分识别功能"""
    client = KimiClient()
    
    # 模拟简历内容
    test_resume = """
    张三
    电话：138****1234
    邮箱：zhangsan@email.com
    
    工作经历：
    2020.03-至今 某科技公司 高级前端工程师
    负责公司核心产品的前端架构设计和开发，包括：
    1. 设计并实现响应式前端架构
    2. 优化前端性能，提升用户体验
    3. 指导初级开发人员
    4. 参与技术选型和架构决策
    
    2018.06-2020.02 某互联网公司 前端工程师
    负责公司多个项目的前端开发工作，包括：
    1. 参与电商平台的前端开发
    2. 负责移动端H5页面开发
    3. 与后端团队协作完成接口对接
    
    教育经历：
    2014.09-2018.06 某大学 计算机科学与技术 本科
    
    技能：
    JavaScript, React, Vue, Node.js
    """
    
    print("测试工作经历部分识别...")
    sections = client._identify_work_sections(test_resume)
    
    print(f"识别到 {len(sections)} 个工作经历部分:")
    for i, section in enumerate(sections):
        print(f"\n--- 第{i+1}个部分 ---")
        print(section[:200] + "..." if len(section) > 200 else section)

def test_chunk_processing():
    """测试分块处理功能"""
    client = KimiClient()
    
    # 模拟工作经历块
    work_chunk = """
    2020.03-至今 某科技公司 高级前端工程师
    负责公司核心产品的前端架构设计和开发，包括：
    1. 设计并实现响应式前端架构
    2. 优化前端性能，提升用户体验
    3. 指导初级开发人员
    4. 参与技术选型和架构决策
    5. 负责团队代码审查和技术培训
    6. 与产品经理协作完成需求分析
    7. 参与系统架构设计和技术选型
    8. 负责前端自动化测试和部署流程
    9. 优化构建流程，提升开发效率
    10. 参与开源项目贡献和技术分享
    """
    
    print("\n测试分块处理...")
    result = client._process_work_chunk(work_chunk, 1)
    
    print(f"处理结果: {json.dumps(result, ensure_ascii=False, indent=2)}")

def test_json_fix_methods():
    """测试JSON修复方法"""
    client = KimiClient()
    
    # 测试未闭合的字符串
    test_cases = [
        '{"name": "test", "description": "这是一个测试"',
        '{"key1": "value1" "key2": "value2"}',
        '{"array": ["item1" "item2" "item3"]}'
    ]
    
    print("\n测试JSON修复方法...")
    for i, test_case in enumerate(test_cases):
        print(f"\n测试用例 {i+1}: {test_case}")
        
        # 测试字符串修复
        fixed_strings = client._fix_unclosed_strings(test_case)
        print(f"字符串修复后: {fixed_strings}")
        
        # 测试逗号修复
        fixed_commas = client._fix_missing_commas(fixed_strings)
        print(f"逗号修复后: {fixed_commas}")

def test_intelligent_processing_flow():
    """测试智能处理流程"""
    client = KimiClient()
    
    # 模拟超长工作经历
    long_work_content = """
    工作经历：
    
    2020.03-至今 某科技公司 高级前端工程师
    负责公司核心产品的前端架构设计和开发，包括：
    1. 设计并实现响应式前端架构，支持多端适配
    2. 优化前端性能，通过代码分割、懒加载等技术提升用户体验
    3. 指导初级开发人员，组织技术分享和代码审查
    4. 参与技术选型和架构决策，推动技术栈升级
    5. 负责团队代码审查和技术培训，提升团队整体技术水平
    6. 与产品经理协作完成需求分析，提供技术可行性建议
    7. 参与系统架构设计和技术选型，制定前端开发规范
    8. 负责前端自动化测试和部署流程，提升开发效率
    9. 优化构建流程，引入Webpack5和Vite等现代构建工具
    10. 参与开源项目贡献和技术分享，提升团队技术影响力
    
    2018.06-2020.02 某互联网公司 前端工程师
    负责公司多个项目的前端开发工作，包括：
    1. 参与电商平台的前端开发，负责商品详情页和购物车功能
    2. 负责移动端H5页面开发，确保在不同设备上的兼容性
    3. 与后端团队协作完成接口对接，参与API设计讨论
    4. 使用Vue.js框架开发单页应用，实现组件化开发
    5. 负责前端性能优化，通过图片懒加载、CDN加速等方式提升加载速度
    6. 参与前端自动化测试，编写单元测试和集成测试
    7. 负责前端代码部署和运维，使用Docker容器化部署
    8. 参与技术选型讨论，评估新技术的可行性
    9. 负责前端文档编写，维护技术文档和开发指南
    10. 参与团队代码审查，提供代码质量改进建议
    
    2016.07-2018.05 某软件公司 初级前端工程师
    参与公司多个Web项目的开发，包括：
    1. 使用HTML、CSS、JavaScript开发静态页面
    2. 参与jQuery插件的开发和维护
    3. 负责页面兼容性测试和bug修复
    4. 参与前端框架的学习和应用
    5. 协助高级工程师完成复杂功能开发
    6. 负责前端代码的版本控制和代码合并
    7. 参与项目需求分析和功能设计讨论
    8. 负责前端开发环境的搭建和维护
    9. 参与前端技术分享和学习交流
    10. 协助测试团队完成功能测试和回归测试
    """
    
    print("\n测试智能处理流程...")
    print("模拟超长工作经历内容...")
    
    # 测试工作经历部分识别
    sections = client._identify_work_sections(long_work_content)
    print(f"识别到 {len(sections)} 个工作经历部分")
    
    # 测试分块处理
    all_experiences = []
    for i, section in enumerate(sections):
        print(f"\n处理第{i+1}个工作经历块...")
        chunk_result = client._process_work_chunk(section, i+1)
        if chunk_result:
            all_experiences.extend(chunk_result)
            print(f"第{i+1}块处理成功，提取到 {len(chunk_result)} 个工作经历")
        else:
            print(f"第{i+1}块处理失败")
    
    print(f"\n总共提取到 {len(all_experiences)} 个工作经历")
    for i, exp in enumerate(all_experiences):
        print(f"工作经历 {i+1}: {exp.get('company_name', 'N/A')} - {exp.get('position', 'N/A')}")

if __name__ == "__main__":
    print("测试智能处理机制...")
    
    # 测试各个功能模块
    test_work_section_identification()
    test_chunk_processing()
    test_json_fix_methods()
    test_intelligent_processing_flow()
    
    print("\n测试完成！") 