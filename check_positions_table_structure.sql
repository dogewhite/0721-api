-- 检查 positions 表的实际结构
-- 连接到 talentdb 数据库

-- 1. 检查 positions 表的字段结构
SELECT '=== project_management.positions 表结构 ===' as info;
SELECT 
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns 
WHERE table_name = 'positions' 
AND table_schema = 'project_management'
ORDER BY ordinal_position;

-- 2. 查看 positions 表的数据
SELECT '=== positions 表数据 ===' as info;
SELECT * FROM project_management.positions LIMIT 5;

-- 3. 检查其他相关表的结构
SELECT '=== project_management.companies 表结构 ===' as info;
SELECT 
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns 
WHERE table_name = 'companies' 
AND table_schema = 'project_management'
ORDER BY ordinal_position;

SELECT '=== project_management.projects 表结构 ===' as info;
SELECT 
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns 
WHERE table_name = 'projects' 
AND table_schema = 'project_management'
ORDER BY ordinal_position;

-- 4. 查看完整的数据关系
SELECT '=== 完整数据关系 ===' as info;
SELECT 
    c.name as company_name,
    p.name as project_name,
    pos.name as position_name,
    pos.id as position_id
FROM project_management.companies c
JOIN project_management.projects p ON c.id = p.company_id
JOIN project_management.positions pos ON p.id = pos.project_id
ORDER BY c.name, p.name, pos.name; 