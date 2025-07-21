#!/usr/bin/env python3
"""
测试修复后的草稿确认API
"""

import requests
import json
from datetime import datetime

def test_draft_confirmation_api():
    """测试草稿确认API"""
    
    base_url = "https://api.zxyang.xin"
    
    print("=== 测试草稿确认API ===")
    print(f"测试时间: {datetime.now()}")
    print("=" * 50)
    
    try:
        # 1. 获取草稿列表
        print("\n1. 获取草稿列表:")
        print("-" * 30)
        
        response = requests.get(f"{base_url}/api/resume/draft/list?page=1&page_size=10")
        if response.status_code == 200:
            data = response.json()
            drafts = data.get('data', [])
            print(f"  草稿数量: {len(drafts)}")
            
            if drafts:
                for draft in drafts[:3]:  # 只显示前3个
                    print(f"    - ID: {draft.get('id')}, 姓名: {draft.get('chinese_name')}, 状态: {draft.get('draft_status')}")
                
                # 选择一个草稿进行测试
                test_draft = drafts[0]
                test_draft_id = test_draft.get('id')
                print(f"\n  选择测试草稿: ID={test_draft_id}, 姓名={test_draft.get('chinese_name')}")
            else:
                print("  没有找到草稿简历")
                return
        else:
            print(f"  获取草稿列表失败: {response.status_code}")
            return
        
        # 2. 获取草稿详情
        print(f"\n2. 获取草稿详情 (ID: {test_draft_id}):")
        print("-" * 30)
        
        response = requests.get(f"{base_url}/api/resume/draft/{test_draft_id}")
        if response.status_code == 200:
            data = response.json()
            draft_detail = data.get('data', {})
            print(f"  草稿详情获取成功")
            print(f"  姓名: {draft_detail.get('chinese_name')}")
            print(f"  岗位ID: {draft_detail.get('position_id')}")
            print(f"  岗位名称: {draft_detail.get('position_name')}")
            print(f"  项目名称: {draft_detail.get('project_name')}")
            print(f"  公司名称: {draft_detail.get('company_name')}")
        else:
            print(f"  获取草稿详情失败: {response.status_code}")
            return
        
        # 3. 测试草稿确认
        print(f"\n3. 测试草稿确认 (ID: {test_draft_id}):")
        print("-" * 30)
        
        response = requests.post(f"{base_url}/api/resume/draft/{test_draft_id}/confirm")
        if response.status_code == 200:
            data = response.json()
            print(f"  ✅ 草稿确认成功!")
            print(f"  响应: {json.dumps(data, ensure_ascii=False, indent=2)}")
            
            # 检查返回的信息
            if data.get('success'):
                resume_id = data.get('resume_id')
                position_linked = data.get('position_linked')
                position_info = data.get('position_info')
                
                print(f"\n  确认结果:")
                print(f"    - 正式简历ID: {resume_id}")
                print(f"    - 职位关联: {'是' if position_linked else '否'}")
                
                if position_info:
                    print(f"    - 职位信息:")
                    print(f"      * 职位ID: {position_info.get('position_id')}")
                    print(f"      * 职位名称: {position_info.get('position_name')}")
                    print(f"      * 项目名称: {position_info.get('project_name')}")
                    print(f"      * 公司名称: {position_info.get('company_name')}")
            else:
                print(f"  ❌ 草稿确认失败: {data.get('message')}")
        else:
            print(f"  ❌ 草稿确认请求失败: {response.status_code}")
            print(f"  错误信息: {response.text}")
        
        # 4. 验证职位关联是否创建成功
        print(f"\n4. 验证职位关联:")
        print("-" * 30)
        
        if data.get('success') and data.get('position_linked'):
            position_id = data.get('position_info', {}).get('position_id')
            resume_id = data.get('resume_id')
            
            if position_id and resume_id:
                # 查询职位候选人列表
                response = requests.get(f"{base_url}/api/positions/{position_id}/candidates")
                if response.status_code == 200:
                    candidates_data = response.json()
                    candidates = candidates_data.get('data', [])
                    
                    print(f"  职位 {position_id} 的候选人数量: {len(candidates)}")
                    
                    # 查找刚创建的关联
                    found_association = False
                    for candidate in candidates:
                        if candidate.get('resume_id') == resume_id:
                            print(f"  ✅ 找到新创建的职位关联:")
                            print(f"    - 关联ID: {candidate.get('id')}")
                            print(f"    - 简历ID: {candidate.get('resume_id')}")
                            print(f"    - 候选人姓名: {candidate.get('candidate_name')}")
                            print(f"    - 状态: {candidate.get('status')}")
                            print(f"    - 创建时间: {candidate.get('created_at')}")
                            found_association = True
                            break
                    
                    if not found_association:
                        print(f"  ❌ 未找到新创建的职位关联")
                else:
                    print(f"  查询职位候选人失败: {response.status_code}")
            else:
                print(f"  缺少职位ID或简历ID，无法验证关联")
        else:
            print(f"  草稿没有关联职位，跳过验证")
        
        print("\n" + "=" * 50)
        print("测试完成")
        
    except Exception as e:
        print(f"测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_draft_confirmation_api() 