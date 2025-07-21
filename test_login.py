#!/usr/bin/env python3
"""
测试用户登录功能
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

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def test_user_login(username: str, password: str):
    """测试用户登录"""
    print(f"测试用户登录: {username}")
    
    try:
        # 初始化数据库
        init_db()
        
        # 获取数据库会话
        db = next(get_db())
        
        try:
            # 查找用户
            user = db.query(User).filter(User.username == username).first()
            if not user:
                print(f"用户 {username} 不存在")
                return False
            
            print(f"找到用户: {user.username}, ID: {user.id}")
            
            # 验证密码
            if verify_password(password, user.password_hash):
                print(f"密码验证成功")
                return True
            else:
                print(f"密码验证失败")
                return False
                
        finally:
            db.close()
            
    except Exception as e:
        print(f"测试失败: {e}")
        return False

def list_all_users():
    """列出所有用户"""
    print("列出所有用户:")
    
    try:
        # 初始化数据库
        init_db()
        
        # 获取数据库会话
        db = next(get_db())
        
        try:
            users = db.query(User).all()
            for user in users:
                print(f"  - {user.username} (ID: {user.id})")
                
        finally:
            db.close()
            
    except Exception as e:
        print(f"获取用户列表失败: {e}")

def main():
    """主函数"""
    print("开始测试用户登录功能...")
    
    # 列出所有用户
    list_all_users()
    print()
    
    # 测试用户登录
    test_users = [
        ("xuexinyu", "password123"),
        ("zhangsan", "password123"),
        ("lisi", "password123"),
        ("wangwu", "password123"),
        ("zhaoliu", "password123"),
        ("qianqi", "password123"),
    ]
    
    for username, password in test_users:
        success = test_user_login(username, password)
        print(f"用户 {username} 登录测试: {'成功' if success else '失败'}")
        print()

if __name__ == "__main__":
    main() 