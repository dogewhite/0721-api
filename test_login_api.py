#!/usr/bin/env python3
"""
测试登录API
"""

import requests
import json

def test_login_api():
    """测试登录API"""
    url = "http://localhost:8000/api/login"
    
    # 测试数据
    data = {
        "username": "xuexinyu",
        "password": "password123"
    }
    
    print(f"测试登录API: {url}")
    print(f"请求数据: {data}")
    
    try:
        # 发送POST请求
        response = requests.post(url, data=data)
        
        print(f"响应状态码: {response.status_code}")
        print(f"响应头: {dict(response.headers)}")
        print(f"响应内容: {response.text}")
        
        if response.status_code == 200:
            try:
                result = response.json()
                print(f"JSON响应: {json.dumps(result, indent=2, ensure_ascii=False)}")
                return True
            except json.JSONDecodeError as e:
                print(f"JSON解析失败: {e}")
                return False
        else:
            print(f"登录失败，状态码: {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"请求失败: {e}")
        return False

if __name__ == "__main__":
    test_login_api() 