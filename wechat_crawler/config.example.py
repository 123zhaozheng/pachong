#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
爬虫配置文件示例
请复制此文件为config.py并根据实际情况修改
"""

# Redis配置
REDIS_HOST = 'localhost'  # Redis服务器地址，多机部署时修改为中心服务器IP
REDIS_PORT = 6379         # Redis端口
REDIS_DB = 0              # Redis数据库索引
REDIS_PASSWORD = None     # Redis密码，如果有设置则填写，否则为None

# 爬虫配置
MAX_REQUESTS_PER_COOKIE = 100  # 每个cookie最大请求次数，根据目标网站反爬策略调整
NUM_THREADS = 4                # 爬虫线程数，根据机器性能调整
MAX_PAGES_PER_THREAD = 5       # 每个线程爬取的最大页数
TARGET_URL = "https://example.com/regulations"  # 目标网站URL，请替换为实际的法规网站URL

# 下载配置
SAVE_DIR = "downloaded_regulations"  # 法规保存目录
DOWNLOAD_DELAY_MIN = 1  # 下载延迟最小值（秒）
DOWNLOAD_DELAY_MAX = 3  # 下载延迟最大值（秒）
PAGE_DELAY_MIN = 3      # 页面间延迟最小值（秒）
PAGE_DELAY_MAX = 5      # 页面间延迟最大值（秒）

# 浏览器配置
HEADLESS = True         # 是否使用无头浏览器，设为False可以看到浏览器界面
QR_CODE_PATH = 'qrcode.png'  # 二维码保存路径

# API配置
API_HOST = '0.0.0.0'    # API监听地址，0.0.0.0表示监听所有网卡
API_PORT = 5000         # API监听端口
