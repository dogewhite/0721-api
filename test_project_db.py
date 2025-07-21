#!/usr/bin/env python3
"""
测试项目管理数据库连接
"""

import sys
import os

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from database import engine
    from models import Company, Project, Position, PositionCandidate
    from sqlalchemy.orm import sessionmaker
    
    print("✅ 模型导入成功")
    
    # 创建会话
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    print("✅ 数据库连接成功")
    
    # 测试查询公司表
    try:
        companies = db.query(Company).all()
        print(f"✅ 公司表查询成功，共有 {len(companies)} 家公司")
        
        for company in companies:
            print(f"   - {company.name}: {company.description}")
            
    except Exception as e:
        print(f"❌ 公司表查询失败: {e}")
    
    # 测试查询项目表
    try:
        projects = db.query(Project).all()
        print(f"✅ 项目表查询成功，共有 {len(projects)} 个项目")
        
    except Exception as e:
        print(f"❌ 项目表查询失败: {e}")
    
    # 测试查询职位表
    try:
        positions = db.query(Position).all()
        print(f"✅ 职位表查询成功，共有 {len(positions)} 个职位")
        
    except Exception as e:
        print(f"❌ 职位表查询失败: {e}")
    
    # 测试查询候选人关联表
    try:
        candidates = db.query(PositionCandidate).all()
        print(f"✅ 候选人关联表查询成功，共有 {len(candidates)} 个关联记录")
        
    except Exception as e:
        print(f"❌ 候选人关联表查询失败: {e}")
    
    db.close()
    print("✅ 数据库连接已关闭")
    
except Exception as e:
    print(f"❌ 测试失败: {e}")
    import traceback
    traceback.print_exc() 