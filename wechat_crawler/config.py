#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
banklaw.com爬虫配置文件
"""

# Redis配置
REDIS_HOST = 'localhost'
REDIS_PORT = 6379
REDIS_DB = 0
REDIS_PASSWORD = None  # 如果有密码，请填写

# 爬虫配置
MAX_REQUESTS_PER_COOKIE = 100  # 每个cookie最大请求次数
NUM_THREADS = 3  # 爬虫线程数
MAX_PAGES_PER_THREAD = 5  # 每个线程爬取的最大页数

# banklaw.com网站配置
TARGET_URL = "https://www.banklaw.com/login?returnUrl=https://www.banklaw.com/"  # 登录页面URL
BANKLAW_API_URL = "https://api2.banklaw.com"  # API基础URL
ACCESS_TOKEN_TTL = 7200  # access_token有效期（秒）

# 下载配置
SAVE_DIR = "downloaded_regulations"  # 法规保存目录
DOWNLOAD_DELAY_MIN = 1.5  # 下载延迟最小值（秒）
DOWNLOAD_DELAY_MAX = 3.5  # 下载延迟最大值（秒）
PAGE_DELAY_MIN = 3  # 页面间延迟最小值（秒）
PAGE_DELAY_MAX = 6  # 页面间延迟最大值（秒）

# 浏览器配置
HEADLESS = False  # 是否使用无头浏览器，设为False可以看到浏览器操作过程，方便调试
QR_CODE_PATH = 'qrcode.png'  # 二维码保存路径
BROWSER_TIMEOUT = 30  # 浏览器操作超时时间（秒）

# API配置
API_HOST = '0.0.0.0'  # API监听地址，0.0.0.0表示监听所有网卡
API_PORT = 5000  # API监听端口

# 搜索配置
DEFAULT_SEARCH_KEYWORDS = [
    "银行法",
    "金融法规",
    "支付结算",
    "存款保险"
]  # 默认搜索关键词，可在命令行参数中覆盖
