#!/usr/bin/env python3
"""
检查数据库中的表位置
"""

import sys
import os

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from talent_models import talentdb_engine
    from sqlalchemy import text
    
    print("检查talentdb数据库中的表...")
    
    with talentdb_engine.connect() as conn:
        # 查找所有简历相关的表
        result = conn.execute(text("""
            SELECT table_schema, table_name 
            FROM information_schema.tables 
            WHERE table_name IN ('resumes', 'work_experiences', 'education_experiences', 'project_experiences')
            ORDER BY table_schema, table_name;
        """))
        
        tables = result.fetchall()
        
        if tables:
            print("找到以下表：")
            for schema, table in tables:
                print(f"  - {schema}.{table}")
                
                # 检查每个表的记录数
                try:
                    count_result = conn.execute(text(f"SELECT COUNT(*) FROM {schema}.{table}"))
                    count = count_result.scalar()
                    print(f"    记录数: {count}")
                    
                    if table == 'resumes' and count > 0:
                        # 检查最新的一条简历记录
                        latest = conn.execute(text(f"""
                            SELECT id, chinese_name, created_at 
                            FROM {schema}.{table} 
                            ORDER BY created_at DESC 
                            LIMIT 1
                        """))
                        latest_record = latest.fetchone()
                        if latest_record:
                            print(f"    最新记录: ID={latest_record[0]}, 姓名={latest_record[1]}, 时间={latest_record[2]}")
                            
                            # 检查这条简历的关联数据
                            for related_table in ['work_experiences', 'education_experiences', 'project_experiences']:
                                related_count = conn.execute(text(f"""
                                    SELECT COUNT(*) 
                                    FROM {schema}.{related_table} 
                                    WHERE resume_id = {latest_record[0]}
                                """))
                                related_count = related_count.scalar()
                                print(f"    - 关联的{related_table}: {related_count}条记录")
                except Exception as e:
                    print(f"    查询失败: {e}")
        else:
            print("❌ 没有找到简历相关的表")
            
        # 检查所有schema
        result = conn.execute(text("""
            SELECT schema_name 
            FROM information_schema.schemata 
            WHERE schema_name NOT IN ('information_schema', 'pg_catalog', 'pg_toast', 'pg_temp_1', 'pg_toast_temp_1')
            ORDER BY schema_name;
        """))
        
        schemas = result.fetchall()
        print(f"\n数据库中的schema: {[s[0] for s in schemas]}")
            
except Exception as e:
    print(f"❌ 检查失败: {e}")
    import traceback
    traceback.print_exc() 