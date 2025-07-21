-- ================================================
-- 简化版项目管理系统建表脚本
-- 请在 talentdb 数据库中执行！！！
-- ================================================

-- 步骤1: 创建schema
CREATE SCHEMA IF NOT EXISTS project_management;

-- 步骤2: 创建公司表
CREATE TABLE project_management.companies (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 步骤3: 创建项目表
CREATE TABLE project_management.projects (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    status VARCHAR(50) DEFAULT 'active',
    company_id INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 步骤4: 创建职位表
CREATE TABLE project_management.positions (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    requirements TEXT,
    status VARCHAR(50) DEFAULT 'active',
    project_id INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 步骤5: 创建候选人关联表
CREATE TABLE project_management.position_candidates (
    id SERIAL PRIMARY KEY,
    position_id INTEGER NOT NULL,
    resume_id INTEGER NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 步骤6: 添加测试数据
INSERT INTO project_management.companies (name, description) VALUES 
('智讯扬科技', '技术驱动的人才管理平台'),
('示例公司A', '互联网科技公司'),
('示例公司B', '金融服务公司');

-- 步骤7: 验证创建结果
SELECT 'schema创建验证' as step, count(*) as schema_count FROM information_schema.schemata WHERE schema_name = 'project_management';
SELECT 'companies表验证' as step, count(*) as table_count FROM information_schema.tables WHERE table_schema = 'project_management' AND table_name = 'companies';
SELECT 'projects表验证' as step, count(*) as table_count FROM information_schema.tables WHERE table_schema = 'project_management' AND table_name = 'projects';
SELECT 'positions表验证' as step, count(*) as table_count FROM information_schema.tables WHERE table_schema = 'project_management' AND table_name = 'positions';
SELECT 'position_candidates表验证' as step, count(*) as table_count FROM information_schema.tables WHERE table_schema = 'project_management' AND table_name = 'position_candidates';
SELECT '数据验证' as step, count(*) as data_count FROM project_management.companies; 