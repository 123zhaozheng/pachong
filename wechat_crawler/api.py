#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
微信登录API接口
提供二维码获取和cookie管理的HTTP接口
"""

# 导入所需模块
from fastapi import FastAPI, HTTPException, Response, BackgroundTasks, status  # FastAPI相关
from fastapi.responses import FileResponse, JSONResponse  # 响应类型
from pydantic import BaseModel  # 数据验证
import redis  # Redis数据库操作
import threading  # 多线程支持
import time  # 时间控制
import os  # 文件路径操作
from typing import List, Optional  # 类型提示
from .wechat_login import WechatLogin  # 微信登录模块
from .config import (  # 配置文件
    REDIS_HOST, REDIS_PORT, REDIS_DB, REDIS_PASSWORD,
    QR_CODE_PATH
)

# 创建FastAPI应用实例
app = FastAPI(title="微信登录爬虫API", description="提供二维码获取和cookie管理的HTTP接口")

# 初始化Redis连接
redis_conn = redis.Redis(
    host=REDIS_HOST,  # Redis主机地址
    port=REDIS_PORT,  # Redis端口
    db=REDIS_DB,  # Redis数据库编号
    password=REDIS_PASSWORD  # Redis密码
)

# 全局变量，用于控制登录线程
login_thread = None  # 登录线程实例
login_in_progress = False  # 登录是否在进行中

# 定义请求和响应模型
class CookieDelete(BaseModel):
    """删除cookie请求模型"""
    cookie: str  # 要删除的cookie字符串

class CookieResponse(BaseModel):
    """获取cookies响应模型"""
    cookies: List[str]  # cookie列表
    count: int  # cookie数量

class StatusResponse(BaseModel):
    """系统状态响应模型"""
    login_in_progress: bool  # 是否正在登录
    cookie_count: int  # 当前cookie数量
    qrcode_available: bool  # 二维码是否可用
    access_token_available: bool  # 是否有可用的access_token

class SuccessResponse(BaseModel):
    """操作成功响应模型"""
    success: bool  # 是否成功
    message: str  # 返回消息

class TokenRequest(BaseModel):
    """设置token请求模型"""
    token: str  # 要设置的access_token

def login_worker():
    """微信登录工作线程"""
    global login_in_progress
    
    try:
        login = WechatLogin()  # 创建WechatLogin实例
        login.init_browser()  # 初始化浏览器
        login.get_qr_code()  # 获取二维码
        print("二维码已生成，等待扫描...")
        login.wait_for_login()  # 等待用户扫码登录
        print("登录成功，已保存cookie")
    except Exception as e:
        print(f"登录过程发生错误: {e}")
    finally:
        login_in_progress = False  # 登录结束
        if 'login' in locals():
            login.close()  # 关闭浏览器

def start_login_process(background_tasks: BackgroundTasks):
    """启动登录进程"""
    global login_thread, login_in_progress
    
    if not login_in_progress:  # 如果当前没有登录进程
        login_in_progress = True  # 标记登录进行中
        background_tasks.add_task(login_worker)  # 添加登录任务到后台任务
        time.sleep(2)  # 等待二维码生成

@app.get("/api/qrcode", response_class=FileResponse)
async def get_qrcode(background_tasks: BackgroundTasks):
    """获取登录二维码"""
    start_login_process(background_tasks)  # 启动登录进程
    
    if os.path.exists(QR_CODE_PATH):  # 如果二维码文件存在
        return FileResponse(QR_CODE_PATH, media_type="image/png")  # 返回二维码图片
    else:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="二维码生成失败")

@app.get("/api/cookies", response_model=CookieResponse)
async def get_cookies():
    """获取所有可用的cookie"""
    cookies = redis_conn.lrange('wechat_cookies', 0, -1)  # 从Redis获取所有cookies
    cookie_list = [cookie.decode('utf-8') for cookie in cookies]  # 将bytes转换为字符串
    return {"cookies": cookie_list, "count": len(cookie_list)}  # 返回cookies列表和数量

@app.delete("/api/cookies", response_model=SuccessResponse)
async def delete_cookie(cookie_data: CookieDelete):
    """删除指定的cookie"""
    cookie = cookie_data.cookie  # 获取要删除的cookie
    if not cookie:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="缺少cookie参数")
    
    count = redis_conn.lrem('wechat_cookies', 0, cookie)  # 从Redis删除指定cookie
    if count > 0:
        return {"success": True, "message": f"成功删除 {count} 个cookie"}
    else:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="未找到指定的cookie")

@app.get("/api/status", response_model=StatusResponse)
async def get_status():
    """获取当前状态"""
    cookie_count = redis_conn.llen('wechat_cookies')  # 获取当前cookie数量
    access_token = redis_conn.get('access_token')  # 获取access_token
    return {
        "login_in_progress": login_in_progress,  # 登录状态
        "cookie_count": cookie_count,  # cookie数量
        "qrcode_available": os.path.exists(QR_CODE_PATH),  # 二维码可用性
        "access_token_available": access_token is not None  # access_token可用性
    }

@app.post("/api/token", response_model=SuccessResponse)
async def set_token(token_data: TokenRequest):
    """设置access_token"""
    token = token_data.token
    if not token:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="缺少token参数")
    
    # 存储token到Redis
    redis_conn.set('access_token', token)
    # 设置过期时间，假设token有效期为2小时
    redis_conn.expire('access_token', 7200)
    
    return {"success": True, "message": "成功设置access_token"}

@app.get("/api/token", response_model=SuccessResponse)
async def get_token():
    """获取当前的access_token"""
    token = redis_conn.get('access_token')
    if not token:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="未找到access_token")
    
    return {"success": True, "message": f"当前access_token: {token.decode('utf-8')[:10]}..."}

@app.delete("/api/token", response_model=SuccessResponse)
async def delete_token():
    """删除当前的access_token"""
    if not redis_conn.exists('access_token'):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="未找到access_token")
    
    redis_conn.delete('access_token')
    return {"success": True, "message": "成功删除access_token"}

def run_api(host='0.0.0.0', port=5000, reload=False):
    """运行API服务器"""
    import uvicorn
    uvicorn.run("wechat_crawler.api:app", host=host, port=port, reload=reload)

if __name__ == '__main__':
    run_api()
