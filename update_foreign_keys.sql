-- 更新外键约束，添加 ON DELETE CASCADE
-- 执行前请备份数据库

-- 1. 删除现有的外键约束（使用实际的外键约束名）
ALTER TABLE public.work_experiences DROP CONSTRAINT IF EXISTS work_experiences_resume_id_fkey;
ALTER TABLE public.education_experiences DROP CONSTRAINT IF EXISTS education_experiences_resume_id_fkey;
ALTER TABLE public.project_experiences DROP CONSTRAINT IF EXISTS project_experiences_resume_id_fkey;

-- 2. 重新创建外键约束，添加 ON DELETE CASCADE
ALTER TABLE public.work_experiences 
ADD CONSTRAINT work_experiences_resume_id_fkey 
FOREIGN KEY (resume_id) 
REFERENCES public.resumes(id) 
ON DELETE CASCADE;

ALTER TABLE public.education_experiences 
ADD CONSTRAINT education_experiences_resume_id_fkey 
FOREIGN KEY (resume_id) 
REFERENCES public.resumes(id) 
ON DELETE CASCADE;

ALTER TABLE public.project_experiences 
ADD CONSTRAINT project_experiences_resume_id_fkey 
FOREIGN KEY (resume_id) 
REFERENCES public.resumes(id) 
ON DELETE CASCADE;

-- 3. 验证约束是否创建成功
SELECT 
    tc.table_name, 
    tc.constraint_name, 
    tc.constraint_type,
    kcu.column_name,
    ccu.table_name AS foreign_table_name,
    ccu.column_name AS foreign_column_name,
    rc.delete_rule
FROM information_schema.table_constraints AS tc 
JOIN information_schema.key_column_usage AS kcu
    ON tc.constraint_name = kcu.constraint_name
    AND tc.table_schema = kcu.table_schema
JOIN information_schema.constraint_column_usage AS ccu
    ON ccu.constraint_name = tc.constraint_name
    AND ccu.table_schema = tc.table_schema
JOIN information_schema.referential_constraints AS rc
    ON tc.constraint_name = rc.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY' 
    AND tc.table_schema = 'public'
    AND tc.table_name IN ('work_experiences', 'education_experiences', 'project_experiences')
ORDER BY tc.table_name; 