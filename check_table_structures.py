#!/usr/bin/env python3
"""
检查数据库表结构的脚本
"""

import psycopg2
from config_loader import config_loader

def check_table_structures():
    """检查各个表的实际结构"""
    
    # 使用配置文件中的数据库连接信息
    db_url = config_loader.get_db_url()
    print(f"连接数据库: {db_url}")
    
    # 连接数据库
    conn = psycopg2.connect(db_url)
    cur = conn.cursor()
    
    try:
        print("=== 数据库表结构检查 ===")
        print("=" * 50)
        
        # 1. 检查 positions 表结构
        print("\n1. project_management.positions 表结构:")
        print("-" * 40)
        cur.execute("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = 'positions' 
            AND table_schema = 'project_management'
            ORDER BY ordinal_position
        """)
        
        columns = cur.fetchall()
        for col in columns:
            print(f"  - {col[0]}: {col[1]} {'NULL' if col[2] == 'YES' else 'NOT NULL'} {f'DEFAULT {col[3]}' if col[3] else ''}")
        
        # 2. 查看 positions 表数据
        print("\n2. project_management.positions 表数据:")
        print("-" * 40)
        cur.execute("SELECT * FROM project_management.positions LIMIT 5")
        positions = cur.fetchall()
        
        # 获取列名
        cur.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'positions' 
            AND table_schema = 'project_management'
            ORDER BY ordinal_position
        """)
        column_names = [col[0] for col in cur.fetchall()]
        
        print(f"  列名: {column_names}")
        for pos in positions:
            print(f"  数据: {pos}")
        
        # 3. 检查 companies 表结构
        print("\n3. project_management.companies 表结构:")
        print("-" * 40)
        cur.execute("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = 'companies' 
            AND table_schema = 'project_management'
            ORDER BY ordinal_position
        """)
        
        columns = cur.fetchall()
        for col in columns:
            print(f"  - {col[0]}: {col[1]} {'NULL' if col[2] == 'YES' else 'NOT NULL'} {f'DEFAULT {col[3]}' if col[3] else ''}")
        
        # 4. 检查 projects 表结构
        print("\n4. project_management.projects 表结构:")
        print("-" * 40)
        cur.execute("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = 'projects' 
            AND table_schema = 'project_management'
            ORDER BY ordinal_position
        """)
        
        columns = cur.fetchall()
        for col in columns:
            print(f"  - {col[0]}: {col[1]} {'NULL' if col[2] == 'YES' else 'NOT NULL'} {f'DEFAULT {col[3]}' if col[3] else ''}")
        
        # 5. 查看完整的数据关系
        print("\n5. 完整数据关系:")
        print("-" * 40)
        try:
            cur.execute("""
                SELECT 
                    c.name as company_name,
                    p.name as project_name,
                    pos.name as position_name,
                    pos.id as position_id
                FROM project_management.companies c
                JOIN project_management.projects p ON c.id = p.company_id
                JOIN project_management.positions pos ON p.id = pos.project_id
                ORDER BY c.name, p.name, pos.name
            """)
            
            relationships = cur.fetchall()
            for rel in relationships:
                print(f"  公司: {rel[0]}, 项目: {rel[1]}, 职位: {rel[2]} (ID: {rel[3]})")
        except Exception as e:
            print(f"  查询关系数据时出错: {e}")
        
        # 6. 检查 resumes 表结构
        print("\n6. public.resumes 表结构:")
        print("-" * 40)
        cur.execute("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = 'resumes' 
            AND table_schema = 'public'
            ORDER BY ordinal_position
        """)
        
        columns = cur.fetchall()
        for col in columns:
            print(f"  - {col[0]}: {col[1]} {'NULL' if col[2] == 'YES' else 'NOT NULL'} {f'DEFAULT {col[3]}' if col[3] else ''}")
        
        print("\n" + "=" * 50)
        print("表结构检查完成")
        
    except Exception as e:
        print(f"检查过程中出现错误: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    check_table_structures() 