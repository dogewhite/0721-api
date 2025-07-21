-- 简单方法：先检查约束名称，然后手动删除和重建

-- 1. 查看现有的外键约束
SELECT 
    tc.constraint_name,
    kcu.column_name,
    ccu.table_name AS foreign_table_name,
    rc.delete_rule
FROM information_schema.table_constraints tc
JOIN information_schema.key_column_usage kcu 
    ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage ccu
    ON tc.constraint_name = ccu.constraint_name
JOIN information_schema.referential_constraints rc
    ON tc.constraint_name = rc.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY' 
    AND tc.table_schema = 'public'
    AND tc.table_name = 'education_experiences'
    AND kcu.column_name = 'resume_id';

-- 2. 如果上面查询有结果，请手动执行以下命令（替换实际的约束名称）：
-- ALTER TABLE public.education_experiences DROP CONSTRAINT [约束名称];

-- 3. 添加新的外键约束
ALTER TABLE public.education_experiences 
ADD CONSTRAINT education_experiences_resume_id_fkey 
FOREIGN KEY (resume_id) REFERENCES public.resumes(id) ON DELETE CASCADE; 