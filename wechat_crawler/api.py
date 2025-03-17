#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
微信登录API接口
提供二维码获取和cookie管理的HTTP接口
"""

from fastapi import FastAPI, HTTPException, Response, BackgroundTasks, status
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
import redis
import threading
import time
import os
from typing import List, Optional
from .wechat_login import WechatLogin
from .config import (
    REDIS_HOST, REDIS_PORT, REDIS_DB, REDIS_PASSWORD,
    QR_CODE_PATH
)

app = FastAPI(title="微信登录爬虫API", description="提供二维码获取和cookie管理的HTTP接口")
redis_conn = redis.Redis(
    host=REDIS_HOST, 
    port=REDIS_PORT, 
    db=REDIS_DB,
    password=REDIS_PASSWORD
)

# 全局变量，用于控制登录线程
login_thread = None
login_in_progress = False

# 定义请求和响应模型
class CookieDelete(BaseModel):
    cookie: str

class CookieResponse(BaseModel):
    cookies: List[str]
    count: int

class StatusResponse(BaseModel):
    login_in_progress: bool
    cookie_count: int
    qrcode_available: bool

class SuccessResponse(BaseModel):
    success: bool
    message: str

def login_worker():
    """微信登录工作线程"""
    global login_in_progress
    
    try:
        login = WechatLogin()
        login.init_browser()
        login.get_qr_code()
        print("二维码已生成，等待扫描...")
        login.wait_for_login()
        print("登录成功，已保存cookie")
    except Exception as e:
        print(f"登录过程发生错误: {e}")
    finally:
        login_in_progress = False
        if 'login' in locals():
            login.close()

def start_login_process(background_tasks: BackgroundTasks):
    """启动登录进程"""
    global login_thread, login_in_progress
    
    if not login_in_progress:
        login_in_progress = True
        background_tasks.add_task(login_worker)
        # 等待二维码生成
        time.sleep(2)

@app.get("/api/qrcode", response_class=FileResponse)
async def get_qrcode(background_tasks: BackgroundTasks):
    """获取登录二维码"""
    start_login_process(background_tasks)
    
    if os.path.exists(QR_CODE_PATH):
        return FileResponse(QR_CODE_PATH, media_type="image/png")
    else:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="二维码生成失败")

@app.get("/api/cookies", response_model=CookieResponse)
async def get_cookies():
    """获取所有可用的cookie"""
    cookies = redis_conn.lrange('wechat_cookies', 0, -1)
    cookie_list = [cookie.decode('utf-8') for cookie in cookies]
    return {"cookies": cookie_list, "count": len(cookie_list)}

@app.delete("/api/cookies", response_model=SuccessResponse)
async def delete_cookie(cookie_data: CookieDelete):
    """删除指定的cookie"""
    cookie = cookie_data.cookie
    if not cookie:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="缺少cookie参数")
    
    count = redis_conn.lrem('wechat_cookies', 0, cookie)
    if count > 0:
        return {"success": True, "message": f"成功删除 {count} 个cookie"}
    else:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="未找到指定的cookie")

@app.get("/api/status", response_model=StatusResponse)
async def get_status():
    """获取当前状态"""
    cookie_count = redis_conn.llen('wechat_cookies')
    return {
        "login_in_progress": login_in_progress,
        "cookie_count": cookie_count,
        "qrcode_available": os.path.exists(QR_CODE_PATH)
    }

def run_api(host='0.0.0.0', port=5000, reload=False):
    """运行API服务器"""
    import uvicorn
    uvicorn.run("wechat_crawler.api:app", host=host, port=port, reload=reload)

if __name__ == '__main__':
    run_api()
