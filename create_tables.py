#!/usr/bin/env python3
"""
手动创建项目管理相关表结构
"""
import psycopg2
from config_loader import config_loader

def create_tables():
    try:
        # 读取 SQL 文件
        with open('create_project_tables.sql', 'r', encoding='utf-8') as f:
            sql_content = f.read()
        
        # 连接数据库
        config = config_loader.config
        conn = psycopg2.connect(
            host=config.get('DB_HOST'),
            port=config.get('DB_PORT'),
            database=config.get('DB_NAME'),
            user=config.get('DB_USER'),
            password=config.get('DB_PASSWORD')
        )
        
        cursor = conn.cursor()
        
        # 执行 SQL
        cursor.execute(sql_content)
        conn.commit()
        
        print("✅ 项目管理表创建成功！")
        
        # 验证表是否创建成功
        cursor.execute("""
            SELECT table_name FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name IN ('companies', 'projects', 'positions', 'position_candidates')
            ORDER BY table_name;
        """)
        
        tables = cursor.fetchall()
        print(f"📋 已创建的表: {[table[0] for table in tables]}")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ 创建表失败: {e}")
        raise e

if __name__ == "__main__":
    create_tables() 