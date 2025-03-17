import redis
import time
import threading
from .wechat_login import WechatLogin
from .crawler import Crawler
from .config import (
    REDIS_HOST, REDIS_PORT, REDIS_DB, REDIS_PASSWORD,
    MAX_REQUESTS_PER_COOKIE
)

class CrawlerScheduler:
    def __init__(self):
        self.redis_conn = redis.Redis(
            host=REDIS_HOST, 
            port=REDIS_PORT, 
            db=REDIS_DB,
            password=REDIS_PASSWORD
        )
        self.max_requests_per_cookie = MAX_REQUESTS_PER_COOKIE
        self.cookie_usage = {}
        self.lock = threading.Lock()
        
    def get_available_cookie(self):
        with self.lock:
            cookies = self.redis_conn.lrange('wechat_cookies', 0, -1)
            for cookie in cookies:
                cookie_str = cookie.decode('utf-8')
                if self.cookie_usage.get(cookie_str, 0) < self.max_requests_per_cookie:
                    self.cookie_usage[cookie_str] = self.cookie_usage.get(cookie_str, 0) + 1
                    return cookie_str
            return None
            
    def refresh_cookies(self):
        wechat_login = WechatLogin()
        wechat_login.init_browser()
        qr_code_path = wechat_login.get_qr_code()
        print(f"请扫描二维码登录: {qr_code_path}")
        wechat_login.wait_for_login()
        wechat_login.close()
        
    def start_crawler(self, url, max_pages=10):
        while True:
            cookie = self.get_available_cookie()
            if cookie:
                try:
                    print(f"使用cookie {cookie[:20]}... 爬取 {url}")
                    crawler = Crawler(cookie)
                    total, failed = crawler.crawl(max_pages)
                    print(f"爬取完成，共下载 {total} 条法规，失败 {failed} 条")
                    
                    # 如果失败率过高，可能是cookie失效
                    if total > 0 and failed / total > 0.5:
                        print("失败率过高，可能cookie已失效")
                        self.redis_conn.lrem('wechat_cookies', 0, cookie)
                    
                except Exception as e:
                    print(f"爬取失败: {e}")
                    self.redis_conn.lrem('wechat_cookies', 0, cookie)
            else:
                print("没有可用的cookie，等待刷新...")
                self.refresh_cookies()
                time.sleep(5)
