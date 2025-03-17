#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
微信登录API启动脚本
"""

import os
import sys
from wechat_crawler.api import run_api
from wechat_crawler.config import API_HOST, API_PORT

if __name__ == "__main__":
    print("=" * 50)
    print("微信登录API服务启动")
    print("=" * 50)
    print("API服务将提供以下功能：")
    print("1. 获取微信登录二维码: GET /api/qrcode")
    print("2. 获取所有可用cookie: GET /api/cookies")
    print("3. 删除指定cookie: DELETE /api/cookies")
    print("4. 获取当前状态: GET /api/status")
    print("=" * 50)
    print(f"API文档: http://{API_HOST if API_HOST != '0.0.0.0' else 'localhost'}:{API_PORT}/docs")
    print("=" * 50)
    
    try:
        # 可通过命令行参数修改端口
        port = API_PORT
        if len(sys.argv) > 1:
            port = int(sys.argv[1])
            
        run_api(host=API_HOST, port=port, reload=False)
    except KeyboardInterrupt:
        print("\nAPI服务被用户中断")
        sys.exit(0)
    except Exception as e:
        print(f"API服务发生错误: {e}")
        sys.exit(1)
