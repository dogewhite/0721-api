#!/usr/bin/env python3
"""
测试草稿简历岗位关联功能
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from draft_models import DraftResume, get_draft_db
from models import Position, Project, Company, PositionCandidate, get_db
from talent_models import Resume, get_talentdb

def test_position_association():
    """测试岗位关联功能"""
    print("=== 测试草稿简历岗位关联功能 ===")
    
    # 1. 检查草稿简历是否有岗位信息
    print("\n1. 检查草稿简历岗位信息...")
    draft_db = next(get_draft_db())
    try:
        draft_resumes = draft_db.query(DraftResume).filter(DraftResume.position_id.isnot(None)).all()
        print(f"找到 {len(draft_resumes)} 个有关联岗位的草稿简历")
        
        for draft in draft_resumes:
            print(f"  草稿ID: {draft.id}, 姓名: {draft.chinese_name}")
            print(f"    岗位ID: {draft.position_id}")
            print(f"    岗位名称: {draft.position_name}")
            print(f"    项目名称: {draft.project_name}")
            print(f"    公司名称: {draft.company_name}")
    finally:
        draft_db.close()
    
    # 2. 检查正式简历
    print("\n2. 检查正式简历...")
    talent_db = next(get_talentdb())
    try:
        resumes = talent_db.query(Resume).all()
        print(f"找到 {len(resumes)} 个正式简历")
        
        for resume in resumes[:5]:  # 只显示前5个
            print(f"  简历ID: {resume.id}, 姓名: {resume.chinese_name}")
    finally:
        talent_db.close()
    
    # 3. 检查岗位候选人关联
    print("\n3. 检查岗位候选人关联...")
    project_db = next(get_db())
    try:
        position_candidates = project_db.query(PositionCandidate).all()
        print(f"找到 {len(position_candidates)} 个岗位候选人关联")
        
        for pc in position_candidates:
            print(f"  关联ID: {pc.id}, 岗位ID: {pc.position_id}, 简历ID: {pc.resume_id}")
            print(f"    状态: {pc.status}, 备注: {pc.notes}")
    finally:
        project_db.close()
    
    # 4. 检查岗位信息
    print("\n4. 检查岗位信息...")
    project_db = next(get_db())
    try:
        positions = project_db.query(Position).all()
        print(f"找到 {len(positions)} 个岗位")
        
        for position in positions:
            project = project_db.query(Project).filter(Project.id == position.project_id).first()
            if project:
                company = project_db.query(Company).filter(Company.id == project.company_id).first()
                print(f"  岗位ID: {position.id}, 名称: {position.name}")
                print(f"    项目: {project.name if project else 'N/A'}")
                print(f"    公司: {company.name if company else 'N/A'}")
    finally:
        project_db.close()

def test_draft_to_resume_flow():
    """测试草稿到正式简历的流程"""
    print("\n=== 测试草稿到正式简历流程 ===")
    
    # 1. 查找一个有关联岗位的草稿简历
    draft_db = next(get_draft_db())
    try:
        draft_resume = draft_db.query(DraftResume).filter(
            DraftResume.position_id.isnot(None),
            DraftResume.draft_status == "pending_review"
        ).first()
        
        if not draft_resume:
            print("没有找到有关联岗位的待审核草稿简历")
            return
        
        print(f"找到草稿简历: ID={draft_resume.id}, 姓名={draft_resume.chinese_name}")
        print(f"关联岗位: {draft_resume.position_name}")
        print(f"关联项目: {draft_resume.project_name}")
        print(f"关联公司: {draft_resume.company_name}")
        
        # 2. 模拟确认流程
        print("\n模拟确认流程...")
        
        # 检查岗位是否存在
        project_db = next(get_db())
        try:
            position = project_db.query(Position).filter(Position.id == draft_resume.position_id).first()
            if position:
                print(f"✅ 岗位存在: {position.name}")
            else:
                print(f"❌ 岗位不存在: ID={draft_resume.position_id}")
                return
        finally:
            project_db.close()
        
        # 检查是否已经有正式简历
        talent_db = next(get_talentdb())
        try:
            existing_resume = talent_db.query(Resume).filter(
                Resume.chinese_name == draft_resume.chinese_name,
                Resume.phone == draft_resume.phone
            ).first()
            
            if existing_resume:
                print(f"✅ 找到对应的正式简历: ID={existing_resume.id}")
                
                # 检查是否已经有岗位关联
                project_db = next(get_db())
                try:
                    existing_association = project_db.query(PositionCandidate).filter(
                        PositionCandidate.position_id == draft_resume.position_id,
                        PositionCandidate.resume_id == existing_resume.id
                    ).first()
                    
                    if existing_association:
                        print(f"✅ 岗位关联已存在: 关联ID={existing_association.id}")
                        print(f"    状态: {existing_association.status}")
                        print(f"    备注: {existing_association.notes}")
                    else:
                        print(f"⚠️ 岗位关联不存在，需要手动创建")
                finally:
                    project_db.close()
            else:
                print(f"⚠️ 没有找到对应的正式简历")
        finally:
            talent_db.close()
            
    finally:
        draft_db.close()

if __name__ == "__main__":
    test_position_association()
    test_draft_to_resume_flow()
    print("\n=== 测试完成 ===") 