#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import psycopg2
from config_loader import config_loader

def test_draft_fields():
    """测试draft.draft_resumes表的字段结构"""
    try:
        # 获取数据库连接
        db_url = config_loader.get_talentdb_url()
        print(f"数据库URL: {db_url}")
        
        # 连接数据库
        conn = psycopg2.connect(db_url)
        cursor = conn.cursor()
        
        # 查询draft.draft_resumes表的结构
        cursor.execute("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns 
            WHERE table_schema = 'draft' 
              AND table_name = 'draft_resumes'
            ORDER BY ordinal_position;
        """)
        
        columns = cursor.fetchall()
        print("\n=== draft.draft_resumes 表字段结构 ===")
        for col in columns:
            print(f"{col[0]}: {col[1]} (nullable: {col[2]})")
        
        # 检查highest_education字段是否存在
        has_highest_education = any(col[0] == 'highest_education' for col in columns)
        print(f"\n是否包含highest_education字段: {has_highest_education}")
        
        # 查询resumes表的结构
        cursor.execute("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns 
            WHERE table_name = 'resumes'
            ORDER BY ordinal_position;
        """)
        
        columns = cursor.fetchall()
        print("\n=== resumes 表字段结构 ===")
        for col in columns:
            print(f"{col[0]}: {col[1]} (nullable: {col[2]})")
        
        # 检查highest_education字段是否存在
        has_highest_education = any(col[0] == 'highest_education' for col in columns)
        print(f"\n是否包含highest_education字段: {has_highest_education}")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"测试失败: {e}")

if __name__ == "__main__":
    test_draft_fields() 