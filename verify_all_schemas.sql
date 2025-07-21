-- 验证所有schema下指向 resumes 表的外键约束
-- 包括 public 和 project_management schema

-- 1. 检查所有指向 resumes 表的外键约束（不限制schema）
SELECT 
    tc.table_schema,
    tc.table_name, 
    tc.constraint_name, 
    kcu.column_name,
    ccu.table_schema AS foreign_table_schema,
    ccu.table_name AS foreign_table_name,
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
    AND ccu.table_name = 'resumes'
    AND ccu.table_schema = 'public'
ORDER BY tc.table_schema, tc.table_name;

-- 2. 专门检查 project_management schema 下的 position_candidates 表
SELECT 
    tc.table_schema,
    tc.table_name, 
    tc.constraint_name, 
    kcu.column_name,
    ccu.table_schema AS foreign_table_schema,
    ccu.table_name AS foreign_table_name,
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
    AND tc.table_schema = 'project_management'
    AND tc.table_name = 'position_candidates'
    AND kcu.column_name = 'resume_id'
ORDER BY kcu.column_name;

-- 3. 统计所有级联约束
SELECT 
    COUNT(*) as total_cascade_constraints,
    '指向 public.resumes 表的级联删除约束总数' as description
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
    AND ccu.table_name = 'resumes'
    AND ccu.table_schema = 'public'
    AND rc.delete_rule = 'CASCADE'; 