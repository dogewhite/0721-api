-- 分析数据库结构和表关联关系
-- 连接到 project_management 数据库

-- 1. 显示所有schema和表
SELECT '=== 所有Schema和表 ===' as section;
SELECT 
    schemaname,
    tablename,
    tableowner
FROM pg_tables 
WHERE schemaname NOT IN ('information_schema', 'pg_catalog', 'pg_toast')
ORDER BY schemaname, tablename;

-- 2. 显示所有外键关联关系
SELECT '=== 外键关联关系 ===' as section;
SELECT 
    tc.table_schema as source_schema,
    tc.table_name as source_table,
    kcu.column_name as source_column,
    ccu.table_schema as target_schema,
    ccu.table_name as target_table,
    ccu.column_name as target_column,
    tc.constraint_name
FROM information_schema.table_constraints tc
JOIN information_schema.key_column_usage kcu 
    ON tc.constraint_name = kcu.constraint_name
    AND tc.table_schema = kcu.table_schema
JOIN information_schema.constraint_column_usage ccu 
    ON ccu.constraint_name = tc.constraint_name
    AND ccu.table_schema = tc.table_schema
WHERE tc.constraint_type = 'FOREIGN KEY'
AND tc.table_schema NOT IN ('information_schema', 'pg_catalog')
ORDER BY tc.table_schema, tc.table_name, kcu.column_name;

-- 3. 显示每个表的详细结构
SELECT '=== 表结构详情 ===' as section;
SELECT 
    t.table_schema,
    t.table_name,
    c.column_name,
    c.data_type,
    c.is_nullable,
    c.column_default,
    c.ordinal_position
FROM information_schema.tables t
JOIN information_schema.columns c 
    ON t.table_name = c.table_name 
    AND t.table_schema = c.table_schema
WHERE t.table_schema NOT IN ('information_schema', 'pg_catalog')
AND t.table_type = 'BASE TABLE'
ORDER BY t.table_schema, t.table_name, c.ordinal_position;

-- 4. 显示主键信息
SELECT '=== 主键信息 ===' as section;
SELECT 
    tc.table_schema,
    tc.table_name,
    kcu.column_name,
    tc.constraint_name
FROM information_schema.table_constraints tc
JOIN information_schema.key_column_usage kcu 
    ON tc.constraint_name = kcu.constraint_name
WHERE tc.constraint_type = 'PRIMARY KEY'
AND tc.table_schema NOT IN ('information_schema', 'pg_catalog')
ORDER BY tc.table_schema, tc.table_name;

-- 5. 显示唯一约束
SELECT '=== 唯一约束 ===' as section;
SELECT 
    tc.table_schema,
    tc.table_name,
    kcu.column_name,
    tc.constraint_name
FROM information_schema.table_constraints tc
JOIN information_schema.key_column_usage kcu 
    ON tc.constraint_name = kcu.constraint_name
WHERE tc.constraint_type = 'UNIQUE'
AND tc.table_schema NOT IN ('information_schema', 'pg_catalog')
ORDER BY tc.table_schema, tc.table_name;

-- 6. 显示索引信息
SELECT '=== 索引信息 ===' as section;
SELECT 
    schemaname,
    tablename,
    indexname,
    indexdef
FROM pg_indexes 
WHERE schemaname NOT IN ('information_schema', 'pg_catalog')
ORDER BY schemaname, tablename, indexname;

-- 7. 显示表大小和行数统计
SELECT '=== 表统计信息 ===' as section;
SELECT 
    schemaname,
    tablename,
    n_tup_ins as inserts,
    n_tup_upd as updates,
    n_tup_del as deletes,
    n_live_tup as live_rows,
    n_dead_tup as dead_rows
FROM pg_stat_user_tables
ORDER BY schemaname, tablename;

-- 8. 特别关注position_candidates表
SELECT '=== position_candidates表详情 ===' as section;
SELECT 
    tc.table_schema,
    tc.table_name,
    c.column_name,
    c.data_type,
    c.is_nullable,
    c.column_default
FROM information_schema.columns c
JOIN information_schema.tables tc 
    ON c.table_name = tc.table_name 
    AND c.table_schema = tc.table_schema
WHERE tc.table_name = 'position_candidates'
ORDER BY c.ordinal_position;

-- 9. position_candidates表的外键约束
SELECT '=== position_candidates外键约束 ===' as section;
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
AND tc.constraint_type = 'FOREIGN KEY';

-- 10. 检查跨schema的关联
SELECT '=== 跨Schema关联 ===' as section;
SELECT 
    tc.table_schema as source_schema,
    tc.table_name as source_table,
    kcu.column_name as source_column,
    ccu.table_schema as target_schema,
    ccu.table_name as target_table,
    ccu.column_name as target_column,
    tc.constraint_name
FROM information_schema.table_constraints tc
JOIN information_schema.key_column_usage kcu 
    ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage ccu 
    ON ccu.constraint_name = tc.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY'
AND tc.table_schema != ccu.table_schema
ORDER BY tc.table_schema, tc.table_name; 