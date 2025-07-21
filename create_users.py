#!/usr/bin/env python3
"""
用户创建脚本
为系统添加新用户，实现草稿简历的用户数据隔离
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from passlib.context import CryptContext
from sqlalchemy.orm import Session
from models import User
from database import get_db, init_db
import uuid

# 密码加密工具
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    """加密密码"""
    return pwd_context.hash(password)

def create_user(username: str, password: str, db: Session) -> User:
    """创建用户"""
    # 检查用户是否已存在
    existing_user = db.query(User).filter(User.username == username).first()
    if existing_user:
        print(f"用户 {username} 已存在，跳过创建")
        return existing_user
    
    # 创建新用户
    user = User(
        id=uuid.uuid4(),
        username=username,
        password_hash=hash_password(password)
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    print(f"用户 {username} 创建成功，ID: {user.id}")
    return user

def main():
    """主函数"""
    print("开始创建用户...")
    
    # 初始化数据库
    try:
        init_db()
        print("数据库初始化完成")
    except Exception as e:
        print(f"数据库初始化失败: {e}")
        return
    
    # 获取数据库会话
    db = next(get_db())
    
    try:
        # 用户列表：现有用户 + 5个新用户
        users = [
            ("xuexinyu", "password123"),  # 现有用户
            ("zhangsan", "password123"),  # 新用户1
            ("lisi", "password123"),      # 新用户2
            ("wangwu", "password123"),    # 新用户3
            ("zhaoliu", "password123"),   # 新用户4
            ("qianqi", "password123"),    # 新用户5
        ]
        
        created_users = []
        
        for username, password in users:
            user = create_user(username, password, db)
            created_users.append(user)
        
        print(f"\n用户创建完成！共创建了 {len(created_users)} 个用户:")
        for user in created_users:
            print(f"  - {user.username} (ID: {user.id})")
        
        print("\n所有用户的默认密码都是: password123")
        print("请提醒用户及时修改密码！")
        
    except Exception as e:
        print(f"创建用户时发生错误: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    main() 