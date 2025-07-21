#!/usr/bin/env python3
"""
重置xuexinyu用户的密码
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from passlib.context import CryptContext
from sqlalchemy.orm import Session
from models import User
from database import get_db, init_db

# 密码加密工具
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    """加密密码"""
    return pwd_context.hash(password)

def reset_xuexinyu_password():
    """重置xuexinyu用户的密码"""
    print("重置xuexinyu用户密码...")
    
    try:
        # 初始化数据库
        init_db()
        
        # 获取数据库会话
        db = next(get_db())
        
        try:
            # 查找xuexinyu用户
            user = db.query(User).filter(User.username == "xuexinyu").first()
            if not user:
                print("用户xuexinyu不存在，创建新用户...")
                user = User(
                    username="xuexinyu",
                    password_hash=hash_password("password123")
                )
                db.add(user)
            else:
                print(f"找到用户xuexinyu，ID: {user.id}")
                print("更新密码...")
                user.password_hash = hash_password("password123")
            
            db.commit()
            print("密码重置成功！")
            print("用户名: xuexinyu")
            print("密码: password123")
            
            # 验证密码
            if pwd_context.verify("password123", user.password_hash):
                print("密码验证测试: 成功")
            else:
                print("密码验证测试: 失败")
                
        finally:
            db.close()
            
    except Exception as e:
        print(f"重置密码失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    reset_xuexinyu_password() 