#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
微信扫描登录测试脚本
用于验证微信扫描登录并获取access-token
"""

import os
import time
import webbrowser
from wechat_crawler.wechat_login import WechatLogin

def test_wechat_login():
    """
    测试微信扫描登录流程
    """
    print("=" * 50)
    print("微信扫描登录测试开始")
    print("=" * 50)
    
    try:
        # 创建WechatLogin实例
        login = WechatLogin()
        
        # 初始化浏览器
        print("正在初始化浏览器...")
        login.init_browser()
        
        # 获取二维码
        print("正在获取微信登录二维码...")
        qr_code_path = login.get_qr_code()
        print(f"二维码已生成，请使用微信扫描: {qr_code_path}")
        
        # 如果二维码文件存在，打印更明显的提示并尝试自动打开图片
        if os.path.exists(qr_code_path):
            print("\n" + "!" * 50)
            print(f"请使用微信扫描二维码登录")
            print("!" * 50 + "\n")
            
            # 获取二维码图片的绝对路径
            abs_path = os.path.abspath(qr_code_path)
            print(f"二维码图片位置: {abs_path}")
            
            # 尝试打开图片
            try:
                print("尝试自动打开二维码图片...")
                webbrowser.open(f"file:///{abs_path}")
            except Exception as e:
                print(f"自动打开图片失败: {e}")
                print("请手动打开二维码图片文件")
        
        # 等待用户扫码登录
        print("等待微信扫码登录...")
        login_success = login.wait_for_login()
        
        # 检查登录结果
        if login_success and login.access_token:
            print("\n" + "=" * 50)
            print("登录成功!")
            print(f"获取到的access_token: {login.access_token[:20]}...")
            print("=" * 50)
            return login.access_token
        else:
            print("\n" + "=" * 50)
            print("登录失败或未能获取access_token")
            print("=" * 50)
            return None
            
    except Exception as e:
        print(f"\n错误: {e}")
        return None
    finally:
        # 确保关闭浏览器
        if 'login' in locals() and login:
            print("正在关闭浏览器...")
            login.close()

def save_token_to_file(token, filename="access_token.txt"):
    """
    将token保存到文件中，方便后续使用
    """
    if token:
        with open(filename, "w", encoding="utf-8") as f:
            f.write(token)
        print(f"token已保存到文件: {filename}")

if __name__ == "__main__":
    # 测试微信扫码登录
    token = test_wechat_login()
    
    # 保存token到文件
    if token:
        save_token_to_file(token)
        print("\n您可以使用以下命令来使用此token进行爬取:")
        print(f"python run.py --token={token[:10]}...")
    else:
        print("\n登录失败，无法获取token")
    
    # 等待几秒再结束程序，让用户看到结果
    time.sleep(5)
