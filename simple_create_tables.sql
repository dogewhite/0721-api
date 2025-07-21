-- ================================================
-- 项目管理系统 - 简化版建表脚本
-- 如果完整版有权限问题，请使用此简化版
-- ================================================

-- 1. 公司表
CREATE TABLE companies (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. 招聘项目表
CREATE TABLE projects (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    status VARCHAR(50) DEFAULT 'active',
    company_id INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. 职位表
CREATE TABLE positions (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    requirements TEXT,
    status VARCHAR(50) DEFAULT 'active',
    project_id INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 4. 职位-候选人关联表
CREATE TABLE position_candidates (
    id SERIAL PRIMARY KEY,
    position_id INTEGER NOT NULL,
    resume_id INTEGER NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 5. 基本索引
CREATE INDEX idx_projects_company_id ON projects(company_id);
CREATE INDEX idx_positions_project_id ON positions(project_id);
CREATE INDEX idx_position_candidates_position_id ON position_candidates(position_id);
CREATE INDEX idx_position_candidates_resume_id ON position_candidates(resume_id);

-- 6. 插入测试数据
INSERT INTO companies (name, description) VALUES 
('智讯扬科技', '技术驱动的人才管理平台'),
('示例公司A', '互联网科技公司');

-- 验证
SELECT * FROM companies; 