-- 修复 position_candidates 表的外键约束
-- 连接到 talentdb 数据库，使用正确的 schema 路径

-- 1. 检查当前外键约束状态
SELECT '=== 当前外键约束状态 ===' as info;
SELECT 
    tc.constraint_name,
    kcu.column_name as source_column,
    ccu.table_schema as target_schema,
    ccu.table_name as target_table,
    ccu.column_name as target_column
FROM information_schema.table_constraints tc
JOIN information_schema.key_column_usage kcu 
    ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage ccu 
    ON ccu.constraint_name = tc.constraint_name
WHERE tc.table_name = 'position_candidates'
AND tc.table_schema = 'project_management'
AND tc.constraint_type = 'FOREIGN KEY'
ORDER BY tc.constraint_name;

-- 2. 检查表结构
SELECT '=== position_candidates表结构 ===' as info;
SELECT 
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns 
WHERE table_name = 'position_candidates' 
AND table_schema = 'project_management'
ORDER BY ordinal_position;

-- 3. 检查目标表是否存在
SELECT '=== 目标表检查 ===' as info;
SELECT 
    schemaname,
    tablename
FROM pg_tables 
WHERE tablename IN ('positions', 'resumes')
AND schemaname IN ('project_management', 'public')
ORDER BY schemaname, tablename;

-- 4. 如果需要，添加缺失的外键约束
DO $$
BEGIN
    -- 检查 position 外键约束是否存在
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE constraint_name = 'fk_position_candidates_position' 
        AND table_name = 'position_candidates'
        AND table_schema = 'project_management'
        AND constraint_type = 'FOREIGN KEY'
    ) THEN
        RAISE NOTICE 'Adding position foreign key constraint...';
        ALTER TABLE project_management.position_candidates 
        ADD CONSTRAINT fk_position_candidates_position 
        FOREIGN KEY (position_id) REFERENCES project_management.positions(id);
    ELSE
        RAISE NOTICE 'Position foreign key constraint already exists.';
    END IF;
    
    -- 检查 resume 外键约束是否存在
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE constraint_name = 'position_candidates_resume_id_fkey' 
        AND table_name = 'position_candidates'
        AND table_schema = 'project_management'
        AND constraint_type = 'FOREIGN KEY'
    ) THEN
        RAISE NOTICE 'Adding resume foreign key constraint...';
        ALTER TABLE project_management.position_candidates 
        ADD CONSTRAINT position_candidates_resume_id_fkey 
        FOREIGN KEY (resume_id) REFERENCES public.resumes(id);
    ELSE
        RAISE NOTICE 'Resume foreign key constraint already exists.';
    END IF;
END $$;

-- 5. 验证修复结果
SELECT '=== 修复后的外键约束 ===' as info;
SELECT 
    tc.constraint_name,
    kcu.column_name as source_column,
    ccu.table_schema as target_schema,
    ccu.table_name as target_table,
    ccu.column_name as target_column
FROM information_schema.table_constraints tc
JOIN information_schema.key_column_usage kcu 
    ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage ccu 
    ON ccu.constraint_name = tc.constraint_name
WHERE tc.table_name = 'position_candidates'
AND tc.table_schema = 'project_management'
AND tc.constraint_type = 'FOREIGN KEY'
ORDER BY tc.constraint_name; 