-- 为草稿简历表添加用户ID字段，实现用户数据隔离
-- 请在 talentdb 数据库中执行

-- 1. 添加用户ID字段到 draft.draft_resumes 表
ALTER TABLE draft.draft_resumes 
ADD COLUMN IF NOT EXISTS user_id UUID;

-- 2. 为现有数据设置默认用户ID（假设现有数据都属于用户xuexinyu）
-- 首先需要获取xuexinyu用户的ID
UPDATE draft.draft_resumes 
SET user_id = (
    SELECT id FROM auth.users WHERE username = 'xuexinyu'
) 
WHERE user_id IS NULL;

-- 3. 设置user_id字段为NOT NULL
ALTER TABLE draft.draft_resumes 
ALTER COLUMN user_id SET NOT NULL;

-- 4. 添加索引以提高查询性能
CREATE INDEX IF NOT EXISTS idx_draft_resumes_user_id ON draft.draft_resumes(user_id);

-- 5. 添加注释
COMMENT ON COLUMN draft.draft_resumes.user_id IS '上传用户ID，用于数据隔离';

-- 6. 验证字段是否添加成功
SELECT 
    column_name, 
    data_type, 
    is_nullable,
    column_default
FROM information_schema.columns 
WHERE table_schema = 'draft' 
    AND table_name = 'draft_resumes' 
    AND column_name = 'user_id'; 