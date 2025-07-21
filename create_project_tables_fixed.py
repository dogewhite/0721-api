#!/usr/bin/env python3
"""
创建项目管理模块的数据库表
"""

import psycopg2
from config_loader import config_loader

def create_project_management_tables():
    """创建项目管理相关表"""
    
    # 从配置文件获取数据库连接信息
    connection = psycopg2.connect(
        host=config_loader.config.get('DB_HOST'),
        port=config_loader.config.get('DB_PORT'),
        database=config_loader.config.get('DB_NAME'),
        user=config_loader.config.get('DB_USER'),
        password=config_loader.config.get('DB_PASSWORD')
    )
    
    cursor = connection.cursor()
    
    try:
        # 创建schema
        cursor.execute("CREATE SCHEMA IF NOT EXISTS project_management;")
        
        # 创建公司表 (与用户数据库表结构保持一致)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS project_management.companies (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                description TEXT,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        # 创建项目表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS project_management.projects (
                id SERIAL PRIMARY KEY,
                company_id INTEGER REFERENCES project_management.companies(id) ON DELETE CASCADE,
                title VARCHAR(255) NOT NULL,
                description TEXT,
                status VARCHAR(50) DEFAULT 'active',
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        # 创建职位表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS project_management.positions (
                id SERIAL PRIMARY KEY,
                project_id INTEGER REFERENCES project_management.projects(id) ON DELETE CASCADE,
                title VARCHAR(255) NOT NULL,
                description TEXT,
                requirements TEXT,
                salary_range VARCHAR(100),
                count INTEGER DEFAULT 0,
                hired INTEGER DEFAULT 0,
                status VARCHAR(50) DEFAULT 'active',
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        # 创建职位候选人关联表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS project_management.position_candidates (
                id SERIAL PRIMARY KEY,
                project_id INTEGER REFERENCES project_management.projects(id) ON DELETE CASCADE,
                candidate_id INTEGER REFERENCES public.resumes(id) ON DELETE CASCADE,
                stage VARCHAR(50) DEFAULT '初筛',
                score INTEGER,
                assigned_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                notes TEXT,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        # 创建更新时间触发器函数
        cursor.execute("""
            CREATE OR REPLACE FUNCTION update_updated_at_column()
            RETURNS TRIGGER AS $$
            BEGIN
                NEW.updated_at = CURRENT_TIMESTAMP;
                RETURN NEW;
            END;
            $$ language 'plpgsql';
        """)
        
        # 为各表添加更新时间触发器
        tables = ['companies', 'projects', 'positions', 'position_candidates']
        for table in tables:
            cursor.execute(f"""
                DROP TRIGGER IF EXISTS update_{table}_updated_at ON project_management.{table};
                CREATE TRIGGER update_{table}_updated_at
                    BEFORE UPDATE ON project_management.{table}
                    FOR EACH ROW
                    EXECUTE FUNCTION update_updated_at_column();
            """)
        
        # 提交事务
        connection.commit()
        print("✅ 项目管理表创建成功！")
        
        # 验证表是否创建成功
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'project_management'
            ORDER BY table_name;
        """)
        
        tables = cursor.fetchall()
        print(f"📋 已创建的表: {[table[0] for table in tables]}")
        
    except Exception as e:
        connection.rollback()
        print(f"❌ 创建表失败: {e}")
        raise
        
    finally:
        cursor.close()
        connection.close()

if __name__ == "__main__":
    create_project_management_tables() 