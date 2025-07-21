#!/usr/bin/env python3
"""
简单的密码重置脚本
"""

import psycopg2
from passlib.context import CryptContext
import uuid

# 密码加密工具
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    """加密密码"""
    return pwd_context.hash(password)

def reset_password():
    """重置xuexinyu用户密码"""
    # 数据库连接信息
    db_config = {
        'host': '106.15.193.241',
        'port': 5432,
        'database': 'talentdb',
        'user': 'huntermind',
        'password': 'huntermind11_'
    }
    
    try:
        # 连接数据库
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor()
        
        # 生成新的密码哈希
        password_hash = hash_password("password123")
        
        # 检查用户是否存在
        cursor.execute("SELECT id FROM auth.users WHERE username = %s", ("xuexinyu",))
        user = cursor.fetchone()
        
        if user:
            # 更新现有用户密码
            cursor.execute(
                "UPDATE auth.users SET password_hash = %s WHERE username = %s",
                (password_hash, "xuexinyu")
            )
            print(f"更新用户xuexinyu密码成功")
        else:
            # 创建新用户
            user_id = str(uuid.uuid4())
            cursor.execute(
                "INSERT INTO auth.users (id, username, password_hash) VALUES (%s, %s, %s)",
                (user_id, "xuexinyu", password_hash)
            )
            print(f"创建用户xuexinyu成功，ID: {user_id}")
        
        conn.commit()
        print("密码重置完成！")
        print("用户名: xuexinyu")
        print("密码: password123")
        
        # 验证密码
        if pwd_context.verify("password123", password_hash):
            print("密码验证测试: 成功")
        else:
            print("密码验证测试: 失败")
            
    except Exception as e:
        print(f"重置密码失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    reset_password() 