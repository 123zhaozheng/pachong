# 导入所需模块
from selenium import webdriver  # 用于浏览器自动化
from selenium.webdriver.common.by import By  # 用于定位页面元素
from selenium.webdriver.support.ui import WebDriverWait  # 用于等待页面元素
from selenium.webdriver.support import expected_conditions as EC  # 用于定义等待条件
import time  # 用于时间控制
import os  # 用于文件路径操作
import redis  # 用于与Redis数据库交互
import json  # 用于处理JSON数据
import re  # 用于正则表达式匹配
from .config import (  # 从配置文件导入相关配置
    REDIS_HOST, REDIS_PORT, REDIS_DB, REDIS_PASSWORD,
    QR_CODE_PATH, HEADLESS
)
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# 设置banklaw.com网站的URL
BANKLAW_LOGIN_URL = "https://www.banklaw.com/login?returnUrl=https://www.banklaw.com/"

class WechatLogin:
    """微信登录类，负责处理微信扫码登录相关操作，特别是banklaw.com网站的登录"""
    
    def __init__(self):
        """初始化WechatLogin实例"""
        self.driver = None  # 浏览器驱动实例
        self.redis_conn = redis.Redis(  # 连接Redis数据库
            host=REDIS_HOST, 
            port=REDIS_PORT, 
            db=REDIS_DB,
            password=REDIS_PASSWORD
        )
        self.qr_code_path = QR_CODE_PATH  # 二维码保存路径
        self.access_token = None  # 存储access_token
        self.is_running = True  # 登录过程是否正在运行
        
    def init_browser(self):
        """初始化浏览器实例"""
        options = webdriver.ChromeOptions()
        
        # 添加选项
        if HEADLESS:
            options.add_argument('--headless')
            options.add_argument('--disable-gpu')
            # 在无头模式下设置窗口大小
            options.add_argument('--window-size=1920,1080')
        else:
            # 在有头模式下设置窗口最大化
            options.add_argument('--start-maximized')
        
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--no-sandbox')
        options.add_experimental_option('excludeSwitches', ['enable-automation'])
        options.add_experimental_option('useAutomationExtension', False)
        
        # 指定 ChromeDriver 路径
        chrome_driver_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'chromedriver.exe')
        service = Service(executable_path=chrome_driver_path)
        
        try:
            self.driver = webdriver.Chrome(service=service, options=options)
            
            # 确保窗口最大化
            if not HEADLESS:
                self.driver.maximize_window()
                
            # 隐藏自动化特征
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        except Exception as e:
            print(f"初始化浏览器失败: {e}")
            raise
        
    def get_qr_code(self):
        """获取banklaw.com的登录页面截图并保存到本地"""
        try:
            # 访问banklaw.com登录页面
            self.driver.get(BANKLAW_LOGIN_URL)
            print(f"已打开登录页面: {BANKLAW_LOGIN_URL}")
            
            # 等待页面加载完成
            time.sleep(3)  # 给页面足够的加载时间
            
            # 直接截取整个页面并保存
            self.driver.save_screenshot(self.qr_code_path)
            
            print(f"登录页面截图已保存到: {self.qr_code_path}")
            return self.qr_code_path

        except Exception as e:
            print(f"获取登录页面截图失败: {e}")
            # 试图截图，即使出错
            try:
                self.driver.save_screenshot("debug_full_page.png")
                print("已保存调试截图到 debug_full_page.png")
            except:
                pass
            raise
        
    def wait_for_login(self):
        """等待用户扫码登录banklaw.com"""
        max_wait_time = 300  # 最大等待时间（秒）
        start_time = time.time()
        
        print("等待用户扫描二维码登录...")
        
        while time.time() - start_time < max_wait_time:
            try:
                # 检查是否已登录成功（可能会重定向到首页）
                if "returnUrl" not in self.driver.current_url and "/login" not in self.driver.current_url:
                    print("检测到页面跳转，可能已登录成功")
                    
                    # 尝试从localStorage获取token
                    self.extract_token_from_storage()
                    
                    # 如果从localStorage获取失败，尝试从网络请求中获取
                    if not self.access_token:
                        print("从localStorage获取token失败，尝试从网络请求中获取")
                        self.extract_token_from_requests()
                    
                    if self.access_token:
                        print(f"成功获取access_token: {self.access_token[:10]}...")
                        self.save_access_token(self.access_token)
                        return True
                
                time.sleep(2)  # 每2秒检查一次
            except Exception as e:
                print(f"等待登录时发生错误: {e}")
                time.sleep(2)
        
        print("等待登录超时")
        return False
                
    def extract_token_from_storage(self):
        """从localStorage或sessionStorage中提取access_token"""
        try:
            # 尝试从localStorage获取token
            local_storage = self.driver.execute_script("""
                return Object.keys(localStorage).reduce((obj, key) => {
                    obj[key] = localStorage.getItem(key);
                    return obj;
                }, {});
            """)
            
            # 尝试从sessionStorage获取token
            session_storage = self.driver.execute_script("""
                return Object.keys(sessionStorage).reduce((obj, key) => {
                    obj[key] = sessionStorage.getItem(key);
                    return obj;
                }, {});
            """)
            
            # 合并两个存储对象进行搜索
            all_storage = {**local_storage, **session_storage}
            
            # 查找可能包含token的键
            token_keys = [k for k in all_storage.keys() if 'token' in k.lower() or 'auth' in k.lower()]
            
            for key in token_keys:
                value = all_storage[key]
                if value and len(value) > 20:  # token通常较长
                    print(f"找到可能的token，键: {key}")
                    # 如果值是JSON字符串，尝试解析
                    try:
                        data = json.loads(value)
                        if isinstance(data, dict) and ('token' in data or 'accessToken' in data):
                            self.access_token = data.get('token') or data.get('AccessToken')
                            return
                    except:
                        # 如果不是JSON，检查值本身是否像token
                        if re.match(r'^[A-Za-z0-9+/=]+$', value):
                            self.access_token = value
                            return
        except Exception as e:
            print(f"从存储中提取token时出错: {e}")
    
    def extract_token_from_requests(self):
        """从网络请求中提取access_token"""
        try:
            # 执行一些操作触发API请求
            self.driver.get("https://www.banklaw.com/")
            time.sleep(3)
            
            # 获取所有请求的性能日志
            logs = self.driver.execute_script("""
                return window.performance.getEntries().filter(e => 
                    e.name.includes('api') || e.name.includes('token')
                ).map(e => e.name);
            """)
            
            # 在URL中查找token参数
            for url in logs:
                if 'token=' in url or 'access_token=' in url:
                    token_match = re.search(r'(token|access_token)=([^&]+)', url)
                    if token_match:
                        self.access_token = token_match.group(2)
                        return
            
            # 如果在URL中找不到，尝试执行一个API请求并拦截请求头
            headers = self.driver.execute_script("""
                let headers;
                const originalFetch = window.fetch;
                window.fetch = async function(url, options) {
                    headers = options?.headers;
                    return originalFetch.apply(this, arguments);
                };
                
                // 触发一个API请求
                fetch('/api/user/profile');
                
                // 等待一小段时间让请求发出
                await new Promise(resolve => setTimeout(resolve, 500));
                
                // 恢复原始fetch
                window.fetch = originalFetch;
                
                return headers;
            """)
            
            if headers and ('Authorization' in headers or 'Access-Token' in headers):
                token = headers.get('Authorization') or headers.get('Access-Token')
                if token and token.startswith('Bearer '):
                    token = token[7:]  # 移除"Bearer "前缀
                self.access_token = token
        except Exception as e:
            print(f"从请求中提取token时出错: {e}")
    
    def save_access_token(self, token):
        """将access_token保存到Redis数据库"""
        # 存储token到Redis
        self.redis_conn.set('access_token', token)
        # 设置过期时间，假设token有效期为2小时
        self.redis_conn.expire('access_token', 7200)
        
    def close(self):
        """关闭浏览器"""
        if self.driver:
            self.driver.quit()  # 关闭浏览器实例

    def stop(self):
        """停止登录过程"""
        self.is_running = False
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass

    def wait_for_login(self):
        """等待用户扫码登录"""
        try:
            while self.is_running:
                if not self.check_login_status():
                    time.sleep(1)
                else:
                    return True
        except KeyboardInterrupt:
            print("\n检测到中断信号，正在关闭浏览器...")
            self.stop()
            return False
        return False
