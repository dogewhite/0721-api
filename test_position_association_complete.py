#!/usr/bin/env python3
"""
完整测试职位关联流程
"""

import psycopg2
import json
from datetime import datetime
from config_loader import config_loader

def test_position_association_flow():
    """测试完整的职位关联流程"""
    
    # 使用配置文件中的数据库连接信息
    db_url = config_loader.get_db_url()
    print(f"连接数据库: {db_url}")
    
    # 连接数据库
    conn = psycopg2.connect(db_url)
    cur = conn.cursor()
    
    try:
        print("=== 职位关联流程测试 ===")
        print(f"测试时间: {datetime.now()}")
        print("=" * 50)
        
        # 1. 检查基础数据
        print("\n1. 检查基础数据:")
        print("-" * 30)
        
        # 检查职位数据 - 使用正确的字段名 'name'
        cur.execute("SELECT id, name FROM project_management.positions LIMIT 5")
        positions = cur.fetchall()
        print(f"  职位数量: {len(positions)}")
        for pos in positions:
            print(f"    - ID: {pos[0]}, 名称: {pos[1]}")
        
        # 检查简历数据 - 使用正确的字段名 'chinese_name'
        cur.execute("SELECT id, chinese_name FROM public.resumes LIMIT 5")
        resumes = cur.fetchall()
        print(f"  简历数量: {len(resumes)}")
        for resume in resumes:
            print(f"    - ID: {resume[0]}, 姓名: {resume[1]}")
        
        # 检查草稿简历数据 - 使用正确的字段名 'chinese_name'
        cur.execute("SELECT id, chinese_name FROM draft.draft_resumes LIMIT 5")
        draft_resumes = cur.fetchall()
        print(f"  草稿简历数量: {len(draft_resumes)}")
        for draft in draft_resumes:
            print(f"    - ID: {draft[0]}, 姓名: {draft[1]}")
        
        # 2. 检查position_candidates表状态
        print("\n2. position_candidates表状态:")
        print("-" * 30)
        
        cur.execute("""
            SELECT COUNT(*) FROM project_management.position_candidates
        """)
        count = cur.fetchone()[0]
        print(f"  现有关联记录: {count} 条")
        
        if count > 0:
            cur.execute("""
                SELECT pc.id, pc.position_id, pc.resume_id, pc.status, pc.created_at,
                       p.name as position_name, r.chinese_name as resume_name
                FROM project_management.position_candidates pc
                LEFT JOIN project_management.positions p ON pc.position_id = p.id
                LEFT JOIN public.resumes r ON pc.resume_id = r.id
                ORDER BY pc.created_at DESC
                LIMIT 5
            """)
            
            associations = cur.fetchall()
            print("  最近的关联记录:")
            for assoc in associations:
                print(f"    - 关联ID: {assoc[0]}, 职位: {assoc[5] or 'N/A'}, 候选人: {assoc[6] or 'N/A'}, 状态: {assoc[3]}, 时间: {assoc[4]}")
        
        # 3. 测试创建新的职位关联
        print("\n3. 测试创建新的职位关联:")
        print("-" * 30)
        
        if positions and resumes:
            position_id = positions[0][0]
            resume_id = resumes[0][0]
            
            # 检查是否已存在关联
            cur.execute("""
                SELECT id FROM project_management.position_candidates 
                WHERE position_id = %s AND resume_id = %s
            """, (position_id, resume_id))
            
            existing = cur.fetchone()
            if existing:
                print(f"  关联已存在，跳过创建")
            else:
                # 创建新关联
                cur.execute("""
                    INSERT INTO project_management.position_candidates 
                    (position_id, resume_id, status, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING id
                """, (position_id, resume_id, 'pending', datetime.now(), datetime.now()))
                
                new_id = cur.fetchone()[0]
                print(f"  创建新关联成功，ID: {new_id}")
                
                # 验证关联
                cur.execute("""
                    SELECT pc.id, p.name, r.chinese_name, pc.status, pc.created_at
                    FROM project_management.position_candidates pc
                    JOIN project_management.positions p ON pc.position_id = p.id
                    JOIN public.resumes r ON pc.resume_id = r.id
                    WHERE pc.id = %s
                """, (new_id,))
                
                result = cur.fetchone()
                if result:
                    print(f"  验证成功: 关联ID {result[0]}, 职位: {result[1]}, 候选人: {result[2]}, 状态: {result[3]}, 时间: {result[4]}")
        
        # 4. 测试从草稿简历创建关联
        print("\n4. 测试从草稿简历创建关联:")
        print("-" * 30)
        
        if positions and draft_resumes:
            position_id = positions[0][0]
            draft_resume_id = draft_resumes[0][0]
            
            # 检查草稿简历是否有对应的正式简历
            cur.execute("""
                SELECT id, chinese_name FROM public.resumes 
                WHERE chinese_name = (SELECT chinese_name FROM draft.draft_resumes WHERE id = %s)
                LIMIT 1
            """, (draft_resume_id,))
            
            corresponding_resume = cur.fetchone()
            if corresponding_resume:
                resume_id = corresponding_resume[0]
                print(f"  找到对应的正式简历: ID {resume_id}, 姓名: {corresponding_resume[1]}")
                
                # 检查是否已存在关联
                cur.execute("""
                    SELECT id FROM project_management.position_candidates 
                    WHERE position_id = %s AND resume_id = %s
                """, (position_id, resume_id))
                
                existing = cur.fetchone()
                if existing:
                    print(f"  关联已存在，跳过创建")
                else:
                    # 创建新关联
                    cur.execute("""
                        INSERT INTO project_management.position_candidates 
                        (position_id, resume_id, status, created_at, updated_at)
                        VALUES (%s, %s, %s, %s, %s)
                        RETURNING id
                    """, (position_id, resume_id, 'pending', datetime.now(), datetime.now()))
                    
                    new_id = cur.fetchone()[0]
                    print(f"  从草稿创建关联成功，ID: {new_id}")
            else:
                print(f"  未找到草稿简历对应的正式简历")
        
        # 5. 测试查询关联数据
        print("\n5. 测试查询关联数据:")
        print("-" * 30)
        
        cur.execute("""
            SELECT 
                pc.id,
                p.name as position_name,
                r.chinese_name as candidate_name,
                pc.status,
                pc.created_at
            FROM project_management.position_candidates pc
            JOIN project_management.positions p ON pc.position_id = p.id
            JOIN public.resumes r ON pc.resume_id = r.id
            ORDER BY pc.created_at DESC
            LIMIT 10
        """)
        
        results = cur.fetchall()
        print(f"  查询到 {len(results)} 条关联记录:")
        for row in results:
            print(f"    - 关联ID: {row[0]}, 职位: {row[1]}, 候选人: {row[2]}, 状态: {row[3]}, 时间: {row[4]}")
        
        # 6. 测试外键约束
        print("\n6. 测试外键约束:")
        print("-" * 30)
        
        # 尝试插入无效的position_id
        try:
            cur.execute("""
                INSERT INTO project_management.position_candidates 
                (position_id, resume_id, status, created_at, updated_at)
                VALUES (99999, 1, 'pending', %s, %s)
            """, (datetime.now(), datetime.now()))
            print("  ❌ 外键约束测试失败：应该阻止插入无效的position_id")
        except Exception as e:
            print(f"  ✅ 外键约束测试通过：正确阻止了无效的position_id插入 ({e})")
        
        # 尝试插入无效的resume_id
        try:
            cur.execute("""
                INSERT INTO project_management.position_candidates 
                (position_id, resume_id, status, created_at, updated_at)
                VALUES (1, 99999, 'pending', %s, %s)
            """, (datetime.now(), datetime.now()))
            print("  ❌ 外键约束测试失败：应该阻止插入无效的resume_id")
        except Exception as e:
            print(f"  ✅ 外键约束测试通过：正确阻止了无效的resume_id插入 ({e})")
        
        print("\n" + "=" * 50)
        print("测试完成")
        
    except Exception as e:
        print(f"测试过程中出现错误: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    test_position_association_flow() 