#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
微信登录法规爬虫启动脚本
"""

import os
import sys
import time
from wechat_crawler.main import main

if __name__ == "__main__":
    print("=" * 50)
    print("微信登录法规爬虫启动")
    print("=" * 50)
    print("该爬虫将通过微信扫码登录获取cookie，然后使用多线程爬取法规网站内容")
    print("当cookie失效时，系统会自动提示扫码刷新")
    print("=" * 50)
    
    try:
        main()
    except KeyboardInterrupt:
        print("\n程序被用户中断")
        sys.exit(0)
    except Exception as e:
        print(f"程序发生错误: {e}")
        time.sleep(5)
        sys.exit(1)
