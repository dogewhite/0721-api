-- ================================================
-- 项目管理系统 - 手动建表脚本
-- 数据库：PostgreSQL
-- 请在数据库管理工具中执行此脚本
-- ================================================

-- 1. 公司表
CREATE TABLE IF NOT EXISTS companies (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 2. 招聘项目表
CREATE TABLE IF NOT EXISTS projects (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    status VARCHAR(50) DEFAULT 'active' CHECK (status IN ('active', 'closed', 'archived')),
    company_id INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_projects_company FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE
);

-- 3. 职位表
CREATE TABLE IF NOT EXISTS positions (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    requirements TEXT,
    status VARCHAR(50) DEFAULT 'active' CHECK (status IN ('active', 'closed', 'archived')),
    project_id INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_positions_project FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
);

-- 4. 职位-候选人关联表
CREATE TABLE IF NOT EXISTS position_candidates (
    id SERIAL PRIMARY KEY,
    position_id INTEGER NOT NULL,
    resume_id INTEGER NOT NULL,
    status VARCHAR(50) DEFAULT 'pending' CHECK (status IN ('pending', 'interviewing', 'offered', 'rejected', 'archived')),
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_position_candidates_position FOREIGN KEY (position_id) REFERENCES positions(id) ON DELETE CASCADE,
    CONSTRAINT uk_position_resume UNIQUE (position_id, resume_id)
);

-- 5. 创建索引以优化查询性能
CREATE INDEX IF NOT EXISTS idx_companies_name ON companies(name);
CREATE INDEX IF NOT EXISTS idx_projects_company_id ON projects(company_id);
CREATE INDEX IF NOT EXISTS idx_projects_status ON projects(status);
CREATE INDEX IF NOT EXISTS idx_positions_project_id ON positions(project_id);
CREATE INDEX IF NOT EXISTS idx_positions_status ON positions(status);
CREATE INDEX IF NOT EXISTS idx_position_candidates_position_id ON position_candidates(position_id);
CREATE INDEX IF NOT EXISTS idx_position_candidates_resume_id ON position_candidates(resume_id);
CREATE INDEX IF NOT EXISTS idx_position_candidates_status ON position_candidates(status);

-- 6. 创建更新时间戳的触发器函数
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 7. 为每个表创建更新时间戳的触发器
CREATE TRIGGER update_companies_updated_at BEFORE UPDATE ON companies FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_projects_updated_at BEFORE UPDATE ON projects FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_positions_updated_at BEFORE UPDATE ON positions FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_position_candidates_updated_at BEFORE UPDATE ON position_candidates FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- 8. 插入一些测试数据（可选）
INSERT INTO companies (name, description) VALUES 
('智讯扬科技', '技术驱动的人才管理平台'),
('示例公司A', '互联网科技公司'),
('示例公司B', '金融服务公司')
ON CONFLICT DO NOTHING;

-- 验证表创建是否成功
SELECT 
    schemaname,
    tablename,
    tableowner
FROM pg_tables 
WHERE tablename IN ('companies', 'projects', 'positions', 'position_candidates')
ORDER BY tablename; 