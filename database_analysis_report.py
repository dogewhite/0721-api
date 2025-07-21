#!/usr/bin/env python3
"""
数据库结构分析报告生成器
"""

import psycopg2
import json
from datetime import datetime
from config_loader import config_loader

def analyze_database_structure():
    """分析数据库结构并生成报告"""
    
    # 使用配置文件中的数据库连接信息
    db_url = config_loader.get_db_url()
    print(f"连接数据库: {db_url}")
    
    # 连接数据库
    conn = psycopg2.connect(db_url)
    cur = conn.cursor()
    
    try:
        print("=== 数据库结构分析报告 ===")
        print(f"生成时间: {datetime.now()}")
        print("=" * 50)
        
        # 1. 获取所有schema和表
        print("\n1. 数据库Schema和表结构:")
        print("-" * 30)
        cur.execute("""
            SELECT schemaname, tablename, tableowner
            FROM pg_tables 
            WHERE schemaname NOT IN ('information_schema', 'pg_catalog', 'pg_toast')
            ORDER BY schemaname, tablename
        """)
        
        tables = cur.fetchall()
        schemas = {}
        for schema, table, owner in tables:
            if schema not in schemas:
                schemas[schema] = []
            schemas[schema].append(table)
        
        for schema, table_list in schemas.items():
            print(f"\nSchema: {schema}")
            for table in table_list:
                print(f"  - {table}")
        
        # 2. 获取外键关联关系
        print("\n\n2. 表关联关系:")
        print("-" * 30)
        cur.execute("""
            SELECT 
                tc.table_schema as source_schema,
                tc.table_name as source_table,
                kcu.column_name as source_column,
                ccu.table_schema as target_schema,
                ccu.table_name as target_table,
                ccu.column_name as target_column,
                tc.constraint_name
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu 
                ON tc.constraint_name = kcu.constraint_name
                AND tc.table_schema = kcu.table_schema
            JOIN information_schema.constraint_column_usage ccu 
                ON ccu.constraint_name = tc.constraint_name
                AND ccu.table_schema = tc.table_schema
            WHERE tc.constraint_type = 'FOREIGN KEY'
            AND tc.table_schema NOT IN ('information_schema', 'pg_catalog')
            ORDER BY tc.table_schema, tc.table_name, kcu.column_name
        """)
        
        foreign_keys = cur.fetchall()
        if foreign_keys:
            for fk in foreign_keys:
                source_schema, source_table, source_col, target_schema, target_table, target_col, constraint = fk
                print(f"  {source_schema}.{source_table}.{source_col} -> {target_schema}.{target_table}.{target_col} ({constraint})")
        else:
            print("  未发现外键关联")
        
        # 3. 特别分析position_candidates表
        print("\n\n3. position_candidates表详细分析:")
        print("-" * 30)
        
        # 检查表是否存在
        cur.execute("""
            SELECT schemaname, tablename 
            FROM pg_tables 
            WHERE tablename = 'position_candidates'
        """)
        
        position_candidates_tables = cur.fetchall()
        if position_candidates_tables:
            for schema, table in position_candidates_tables:
                print(f"\n  表位置: {schema}.{table}")
                
                # 获取表结构
                cur.execute(f"""
                    SELECT column_name, data_type, is_nullable, column_default
                    FROM information_schema.columns 
                    WHERE table_name = 'position_candidates'
                    AND table_schema = '{schema}'
                    ORDER BY ordinal_position
                """)
                
                columns = cur.fetchall()
                print("  表结构:")
                for col_name, data_type, nullable, default in columns:
                    print(f"    - {col_name}: {data_type} {'NULL' if nullable == 'YES' else 'NOT NULL'} {f'DEFAULT {default}' if default else ''}")
                
                # 获取外键约束
                cur.execute(f"""
                    SELECT 
                        tc.constraint_name,
                        kcu.column_name as source_column,
                        ccu.table_schema as target_schema,
                        ccu.table_name as target_table,
                        ccu.column_name as target_column
                    FROM information_schema.table_constraints tc
                    JOIN information_schema.key_column_usage kcu 
                        ON tc.constraint_name = kcu.constraint_name
                    JOIN information_schema.constraint_column_usage ccu 
                        ON ccu.constraint_name = tc.constraint_name
                    WHERE tc.table_name = 'position_candidates'
                    AND tc.table_schema = '{schema}'
                    AND tc.constraint_type = 'FOREIGN KEY'
                """)
                
                fk_constraints = cur.fetchall()
                if fk_constraints:
                    print("  外键约束:")
                    for constraint_name, source_col, target_schema, target_table, target_col in fk_constraints:
                        print(f"    - {constraint_name}: {source_col} -> {target_schema}.{target_table}.{target_col}")
                else:
                    print("  外键约束: 无")
        else:
            print("  position_candidates表不存在")
        
        # 4. 分析跨schema关联
        print("\n\n4. 跨Schema关联分析:")
        print("-" * 30)
        cur.execute("""
            SELECT 
                tc.table_schema as source_schema,
                tc.table_name as source_table,
                kcu.column_name as source_column,
                ccu.table_schema as target_schema,
                ccu.table_name as target_table,
                ccu.column_name as target_column,
                tc.constraint_name
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu 
                ON tc.constraint_name = kcu.constraint_name
            JOIN information_schema.constraint_column_usage ccu 
                ON ccu.constraint_name = tc.constraint_name
            WHERE tc.constraint_type = 'FOREIGN KEY'
            AND tc.table_schema != ccu.table_schema
            ORDER BY tc.table_schema, tc.table_name
        """)
        
        cross_schema_fks = cur.fetchall()
        if cross_schema_fks:
            for fk in cross_schema_fks:
                source_schema, source_table, source_col, target_schema, target_table, target_col, constraint = fk
                print(f"  {source_schema}.{source_table}.{source_col} -> {target_schema}.{target_table}.{target_col}")
        else:
            print("  无跨Schema关联")
        
        # 5. 数据统计
        print("\n\n5. 数据统计:")
        print("-" * 30)
        for schema, table_list in schemas.items():
            for table in table_list:
                try:
                    cur.execute(f"SELECT COUNT(*) FROM {schema}.{table}")
                    count = cur.fetchone()[0]
                    print(f"  {schema}.{table}: {count} 行")
                except Exception as e:
                    print(f"  {schema}.{table}: 无法统计 ({e})")
        
        print("\n" + "=" * 50)
        print("分析完成")
        
    except Exception as e:
        print(f"分析过程中出现错误: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    analyze_database_structure() 