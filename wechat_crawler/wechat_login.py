from selenium import webdriver
from selenium.webdriver.common.by import By
import time
import os
import redis
from .config import (
    REDIS_HOST, REDIS_PORT, REDIS_DB, REDIS_PASSWORD,
    QR_CODE_PATH, HEADLESS
)

class WechatLogin:
    def __init__(self):
        self.driver = None
        self.redis_conn = redis.Redis(
            host=REDIS_HOST, 
            port=REDIS_PORT, 
            db=REDIS_DB,
            password=REDIS_PASSWORD
        )
        self.qr_code_path = QR_CODE_PATH
        
    def init_browser(self):
        options = webdriver.ChromeOptions()
        if HEADLESS:
            options.add_argument('--headless')
            options.add_argument('--disable-gpu')
        self.driver = webdriver.Chrome(options=options)
        
    def get_qr_code(self):
        self.driver.get('https://wx.qq.com/')
        time.sleep(5)
        qr_element = self.driver.find_element(By.CLASS_NAME, 'qrcode-img')
        qr_element.screenshot(self.qr_code_path)
        return self.qr_code_path
        
    def wait_for_login(self):
        while True:
            try:
                self.driver.find_element(By.CLASS_NAME, 'avatar')
                cookies = self.driver.get_cookies()
                self.save_cookies(cookies)
                break
            except:
                time.sleep(1)
                
    def save_cookies(self, cookies):
        cookie_str = '; '.join([f"{c['name']}={c['value']}" for c in cookies])
        self.redis_conn.rpush('wechat_cookies', cookie_str)
        
    def close(self):
        self.driver.quit()
