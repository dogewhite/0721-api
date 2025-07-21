#!/usr/bin/env python3
"""
测试导图生成功能
"""

import sys
import os

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from JDMapGenerator import JDMapGenerator

def test_diagram_generation():
    """测试导图生成功能"""
    print("🧪 开始测试导图生成功能...")
    print("=" * 50)
    
    try:
        # 创建JDMapGenerator实例
        jd_map = JDMapGenerator()
        
        # 测试数据
        test_data = {
            "job_title": "前端工程师",
            "skills": ["JavaScript", "React", "Vue"],
            "products": ["Web开发", "移动端"]
        }
        
        print("📊 测试数据:")
        print(f"   - 职位: {test_data['job_title']}")
        print(f"   - 技能: {test_data['skills']}")
        print(f"   - 产品: {test_data['products']}")
        print()
        
        # 生成导图
        print("🔄 正在生成导图...")
        result = jd_map.generate_jd_map(test_data)
        
        print("📋 生成结果:")
        print(f"   - 成功状态: {result['success']}")
        print(f"   - 是否有Mermaid代码: {bool(result.get('mermaid_code'))}")
        print(f"   - 是否有PNG数据: {bool(result.get('png_data'))}")
        print(f"   - 是否有diagram_url: {bool(result.get('diagram_url'))}")
        
        if result.get('mermaid_code'):
            print("\n📝 Mermaid代码:")
            print(result['mermaid_code'])
        
        if result.get('error'):
            print(f"\n❌ 错误信息: {result['error']}")
        
        print("\n🎉 测试完成！")
        return result['success']
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_diagram_generation()
    sys.exit(0 if success else 1) 