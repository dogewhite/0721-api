-- 临时修正版本 - 假设resume表在talentdb schema下
-- 执行前请备份数据库

-- 1. 删除现有的外键约束（使用实际的外键约束名）
ALTER TABLE public.work_experiences DROP CONSTRAINT IF EXISTS work_experiences_resume_id_fkey;
ALTER TABLE public.education_experiences DROP CONSTRAINT IF EXISTS education_experiences_resume_id_fkey;
ALTER TABLE public.project_experiences DROP CONSTRAINT IF EXISTS project_experiences_resume_id_fkey;

-- 2. 重新创建外键约束，添加 ON DELETE CASCADE
-- 注意：这里假设resume表在talentdb schema下
ALTER TABLE public.work_experiences 
ADD CONSTRAINT work_experiences_resume_id_fkey 
FOREIGN KEY (resume_id) 
REFERENCES talentdb.resume(id) 
ON DELETE CASCADE;

ALTER TABLE public.education_experiences 
ADD CONSTRAINT education_experiences_resume_id_fkey 
FOREIGN KEY (resume_id) 
REFERENCES talentdb.resume(id) 
ON DELETE CASCADE;

ALTER TABLE public.project_experiences 
ADD CONSTRAINT project_experiences_resume_id_fkey 
FOREIGN KEY (resume_id) 
REFERENCES talentdb.resume(id) 
ON DELETE CASCADE; 