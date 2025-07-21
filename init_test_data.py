#!/usr/bin/env python3
"""
初始化测试数据脚本
用于创建基础的公司和项目数据，确保前端能够正常工作
"""

from database import get_db, init_db
from models import Company, Project, Position, PositionCandidate
from datetime import datetime

def init_test_data():
    """初始化测试数据"""
    print("正在初始化数据库表结构...")
    try:
        init_db()
        print("✓ 数据库表结构初始化完成")
    except Exception as e:
        print(f"⚠️ 数据库表结构初始化失败: {e}")
        return False
    
    print("正在创建测试数据...")
    
    # 获取数据库会话
    db = next(get_db())
    
    try:
        # 检查是否已经有数据
        existing_companies = db.query(Company).count()
        if existing_companies > 0:
            print("✓ 测试数据已存在，跳过创建")
            return True
        
        # 创建测试公司
        companies_data = [
            {
                "name": "科技创新有限公司",
                "description": "专注于AI和大数据技术的创新公司"
            },
            {
                "name": "互联网科技公司",
                "description": "主要业务为互联网产品开发"
            },
            {
                "name": "金融科技公司",
                "description": "专业的金融科技解决方案提供商"
            }
        ]
        
        created_companies = []
        for company_data in companies_data:
            company = Company(**company_data)
            db.add(company)
            db.flush()  # 获取ID
            created_companies.append(company)
            print(f"✓ 创建公司: {company.name}")
        
        # 创建测试项目
        projects_data = [
            {
                "company_id": created_companies[0].id,
                "name": "高级前端工程师招聘",
                "description": "招聘3名高级前端工程师，负责React项目开发",
                "status": "active"
            },
            {
                "company_id": created_companies[0].id,
                "name": "后端工程师批量招聘",
                "description": "为新项目招聘5名后端工程师",
                "status": "active"
            },
            {
                "company_id": created_companies[1].id,
                "name": "产品经理招聘项目",
                "description": "招聘2名产品经理，负责产品规划和设计",
                "status": "active"
            },
            {
                "company_id": created_companies[2].id,
                "name": "量化交易工程师",
                "description": "招聘量化交易相关的技术人员",
                "status": "completed"
            }
        ]
        
        created_projects = []
        for project_data in projects_data:
            project = Project(**project_data)
            db.add(project)
            db.flush()  # 获取ID
            created_projects.append(project)
            print(f"✓ 创建项目: {project.name}")
        
        # 创建测试职位
        positions_data = [
            {
                "project_id": created_projects[0].id,
                "name": "高级前端工程师",
                "description": "负责React项目开发和维护",
                "requirements": "3年以上React开发经验，熟悉TypeScript",
                "status": "active"
            },
            {
                "project_id": created_projects[1].id,
                "name": "Java后端工程师",
                "description": "负责后端服务开发和架构设计",
                "requirements": "5年以上Java开发经验，熟悉Spring Boot",
                "status": "active"
            },
            {
                "project_id": created_projects[2].id,
                "name": "高级产品经理",
                "description": "负责产品规划和需求分析",
                "requirements": "3年以上产品经理经验，有B端产品经验",
                "status": "active"
            }
        ]
        
        for position_data in positions_data:
            position = Position(**position_data)
            db.add(position)
            print(f"✓ 创建职位: {position.name}")
        
        # 提交所有更改
        db.commit()
        print("✓ 所有测试数据创建成功")
        return True
        
    except Exception as e:
        print(f"✗ 创建测试数据失败: {e}")
        db.rollback()
        return False
    finally:
        db.close()

def clear_test_data():
    """清除测试数据"""
    print("正在清除测试数据...")
    
    db = next(get_db())
    
    try:
        # 按照外键依赖顺序删除
        db.query(PositionCandidate).delete()
        db.query(Position).delete()
        db.query(Project).delete()
        db.query(Company).delete()
        
        db.commit()
        print("✓ 测试数据清除完成")
        return True
        
    except Exception as e:
        print(f"✗ 清除测试数据失败: {e}")
        db.rollback()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "clear":
        clear_test_data()
    else:
        init_test_data() 