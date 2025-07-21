-- 为草稿简历表添加岗位关联字段
-- 请在 talentdb 数据库中执行

-- 1. 添加岗位关联字段到 draft.draft_resumes 表
ALTER TABLE draft.draft_resumes 
ADD COLUMN IF NOT EXISTS position_id INTEGER,
ADD COLUMN IF NOT EXISTS position_name TEXT,
ADD COLUMN IF NOT EXISTS project_id INTEGER,
ADD COLUMN IF NOT EXISTS project_name TEXT,
ADD COLUMN IF NOT EXISTS company_id INTEGER,
ADD COLUMN IF NOT EXISTS company_name TEXT;

-- 2. 添加注释
COMMENT ON COLUMN draft.draft_resumes.position_id IS '关联的岗位ID';
COMMENT ON COLUMN draft.draft_resumes.position_name IS '岗位名称';
COMMENT ON COLUMN draft.draft_resumes.project_id IS '关联的项目ID';
COMMENT ON COLUMN draft.draft_resumes.project_name IS '项目名称';
COMMENT ON COLUMN draft.draft_resumes.company_id IS '关联的公司ID';
COMMENT ON COLUMN draft.draft_resumes.company_name IS '公司名称';

-- 3. 验证字段是否添加成功
SELECT 
    column_name, 
    data_type, 
    is_nullable,
    column_default
FROM information_schema.columns 
WHERE table_schema = 'draft' 
    AND table_name = 'draft_resumes' 
    AND column_name IN ('position_id', 'position_name', 'project_id', 'project_name', 'company_id', 'company_name')
ORDER BY column_name; 