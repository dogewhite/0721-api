-- ================================================
-- 项目管理系统 - Schema版建表脚本
-- 在现有数据库中创建独立的 schema
-- ================================================

-- 1. 创建项目管理专用的 schema
CREATE SCHEMA IF NOT EXISTS project_management;

-- 2. 设置搜索路径（可选，方便后续操作）
SET search_path TO project_management, public;

-- 3. 公司表
CREATE TABLE IF NOT EXISTS project_management.companies (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 4. 招聘项目表
CREATE TABLE IF NOT EXISTS project_management.projects (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    status VARCHAR(50) DEFAULT 'active',
    company_id INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_projects_company FOREIGN KEY (company_id) 
        REFERENCES project_management.companies(id) ON DELETE CASCADE
);

-- 5. 职位表
CREATE TABLE IF NOT EXISTS project_management.positions (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    requirements TEXT,
    status VARCHAR(50) DEFAULT 'active',
    project_id INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_positions_project FOREIGN KEY (project_id) 
        REFERENCES project_management.projects(id) ON DELETE CASCADE
);

-- 6. 职位-候选人关联表
-- 注意：resume_id 引用 public schema 中的简历表
CREATE TABLE IF NOT EXISTS project_management.position_candidates (
    id SERIAL PRIMARY KEY,
    position_id INTEGER NOT NULL,
    resume_id INTEGER NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_position_candidates_position FOREIGN KEY (position_id) 
        REFERENCES project_management.positions(id) ON DELETE CASCADE,
    CONSTRAINT uk_position_resume UNIQUE (position_id, resume_id)
);

-- 7. 创建索引
CREATE INDEX IF NOT EXISTS idx_pm_companies_name ON project_management.companies(name);
CREATE INDEX IF NOT EXISTS idx_pm_projects_company_id ON project_management.projects(company_id);
CREATE INDEX IF NOT EXISTS idx_pm_projects_status ON project_management.projects(status);
CREATE INDEX IF NOT EXISTS idx_pm_positions_project_id ON project_management.positions(project_id);
CREATE INDEX IF NOT EXISTS idx_pm_positions_status ON project_management.positions(status);
CREATE INDEX IF NOT EXISTS idx_pm_position_candidates_position_id ON project_management.position_candidates(position_id);
CREATE INDEX IF NOT EXISTS idx_pm_position_candidates_resume_id ON project_management.position_candidates(resume_id);
CREATE INDEX IF NOT EXISTS idx_pm_position_candidates_status ON project_management.position_candidates(status);

-- 8. 插入测试数据
INSERT INTO project_management.companies (name, description) VALUES 
('智讯扬科技', '技术驱动的人才管理平台'),
('示例公司A', '互联网科技公司'),
('示例公司B', '金融服务公司')
ON CONFLICT DO NOTHING;

-- 9. 验证表创建
SELECT 
    schemaname,
    tablename,
    tableowner
FROM pg_tables 
WHERE schemaname = 'project_management'
ORDER BY tablename; 