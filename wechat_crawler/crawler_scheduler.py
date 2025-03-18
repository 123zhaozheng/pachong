import os
import random
import redis  # 导入redis库，用于连接Redis数据库
import time  # 导入time库，用于实现延时功能
import threading  # 导入threading库，用于实现多线程操作
from .wechat_login import WechatLogin  # 从当前包中导入WechatLogin类，用于微信登录
from .crawler import Crawler  # 从当前包中导入Crawler类，用于爬取数据
from .config import (  # 从配置文件导入所需的配置参数
    REDIS_HOST, REDIS_PORT, REDIS_DB, REDIS_PASSWORD,  # Redis连接参数
    MAX_REQUESTS_PER_COOKIE  # 每个cookie可以发送的最大请求数
)
HIERARCHIES = {
    1: "法律法规",
    2: "规章制度",
    3: "行业动态"
}

class CrawlerScheduler:  # 定义爬虫调度器类
    def __init__(self):  # 初始化方法
        self.redis_conn = redis.Redis(  # 创建Redis连接
            host=REDIS_HOST,  # Redis服务器地址
            port=REDIS_PORT,  # Redis服务器端口
            db=REDIS_DB,  # Redis数据库索引
            password=REDIS_PASSWORD  # Redis连接密码
        )
        self.max_requests_per_cookie = MAX_REQUESTS_PER_COOKIE  # 设置每个cookie的最大请求数
        self.cookie_usage = {}  # 初始化cookie使用计数字典
        self.lock = threading.Lock()  # 创建线程锁，用于多线程环境下对共享资源的访问控制
        self.access_token = None  # 初始化access_token为None
        self.wechat_login = None
        self.is_running = True
        
        # 检查是否已有access_token
        self._check_access_token()
        
    def _check_access_token(self):  # 检查是否已有access_token
        """检查Redis中是否已有access_token"""
        token = self.redis_conn.get('access_token')  # 从Redis获取access_token
        if token:  # 如果token存在
            self.access_token = token.decode('utf-8')  # 解码并存储
            print(f"从Redis加载access_token: {self.access_token[:10]}...")
            return True
        return False
    
    def get_access_token(self):  # 获取access_token的方法
        """获取access_token，如果Redis中存在则使用，否则返回None"""
        with self.lock:  # 使用线程锁，确保对共享资源的安全访问
            # 如果实例变量中没有token，尝试从Redis获取
            if not self.access_token:
                token = self.redis_conn.get('access_token')  # 从Redis获取access_token
                if token:  # 如果token存在
                    self.access_token = token.decode('utf-8')  # 更新实例变量
            
            # 如果token即将过期，尝试刷新
            if self.access_token and self.redis_conn.ttl('access_token') < 600:  # 如果剩余时间少于10分钟
                print("Access-Token即将过期，尝试刷新...")
                self.refresh_access_token()
                
            return self.access_token  # 返回实例变量中的token
    
    def set_access_token(self, token, ttl=7200):  # 设置access_token的方法
        """设置access_token并存储到Redis
        
        Args:
            token: access_token字符串
            ttl: 过期时间（秒），默认2小时
        """
        with self.lock:  # 使用线程锁，确保对共享资源的安全访问
            if not token:  # 如果token为空
                print("警告: 尝试设置空token")
                return False
                
            self.access_token = token  # 更新实例变量
            self.redis_conn.set('access_token', token)  # 存储到Redis
            self.redis_conn.expire('access_token', ttl)  # 设置过期时间
            print(f"成功设置access_token: {token[:10]}..., 有效期: {ttl}秒")
            return True
            
    def refresh_access_token(self):  # 刷新access_token的方法
        """刷新access_token"""
        try:
            self.wechat_login = WechatLogin()
            login_success = False
            
            try:
                self.wechat_login.init_browser()
                qr_code_path = self.wechat_login.get_qr_code()
                if qr_code_path:
                    login_success = self.wechat_login.wait_for_login()
            except KeyboardInterrupt:
                print("\n检测到中断信号，正在清理资源...")
                self.stop()
                #这还是暂停不了
                raise
            finally:
                if self.wechat_login:
                    self.wechat_login.stop()

            if not login_success:
                print("登录失败或被中断")
                return False

            return True
        except Exception as e:
            print(f"刷新token失败: {e}")
            return False

    def stop(self):
        """停止所有进程"""
        self.is_running = False
        if self.wechat_login:
            self.wechat_login.stop()
        
    def start_crawler(self, hierarchy_id=1, year=2022,if_chufa = 0):  # 修改方法参数
        """启动爬虫，爬取banklaw.com的法规
        
        Args:
            if_chufa: 是否直接导出处罚案例
            hierarchy_id: 法规层级ID（1:法律法规, 2:规章制度, 3:行业动态）
            max_pages: 最大爬取页数
            keyword: 搜索关键词（保留但不使用）
        """
        #优先判断是否直接导出处罚案例
        if if_chufa == 1:
            #直接处理案例
            print("*"*50+"直接处理处罚案例"+"*"*50)
                
            while True:  # 无限循环，持续爬取
                # 获取access_token，暂时注释
                # access_token = self.get_access_token()
                access_token = "yON3YgFuomVjA6VX9pAiH+QTlTmlRK8SOvkmv+JchVG2CRspG2neoC8U/5cGnxPd"

                if access_token:  # 如果有access_token
                    try:
                        print(f"使用access_token: {access_token[:10]}... 爬取banklaw.com")
                        
                        # 创建爬虫实例，只传入access_token
                        crawler = Crawler(access_token=access_token)
                        
                        # 使用指定的层级ID爬取内容
                        total, failed = crawler.crawl_by_api_responses(hierarchy_id, year,if_chufa)
                        
                        print(f"爬取完成，共下载 {total} 条{hierarchy_name}，失败 {failed} 条")
                        #这里需要根据一定条件跳出循环，这里可以根据failed的数量来判断
                        if failed == 0:
                            break
                        # 如果失败率过高，可能是token失效
                        if total == 0 or (total > 0 and failed / total > 0.5):
                            print("失败率过高，可能access_token已失效")
                            self.refresh_access_token()  # 刷新token
                        
                        # 成功爬取后，休息一段时间再继续
                        sleep_time = random.uniform(30, 60)
                        print(f"休息 {sleep_time:.2f} 秒后继续...")
                        time.sleep(sleep_time)
                        
                    except Exception as e:
                        print(f"爬取失败: {e}")
                        print("可能是access_token已失效，尝试刷新...")
                        self.refresh_access_token()  # 刷新token
                        time.sleep(5)  # 等待5秒后继续
                else:
                    print("没有可用的access_token，尝试获取...")
                    self.refresh_access_token()  # 获取新token
                    time.sleep(5)  # 等待5秒后继续


            return
        # 获取层级名称
        hierarchy_name = {1: "法律法规", 2: "规章制度", 3: "行业动态"}.get(hierarchy_id, "法律法规")
        print(f"开始爬取 {hierarchy_name}，年份: {year}")
        
        while True:  # 无限循环，持续爬取
            # 获取access_token，暂时注释
            # access_token = self.get_access_token()
            access_token = "yON3YgFuomVjA6VX9pAiH+QTlTmlRK8SOvkmv+JchVG2CRspG2neoC8U/5cGnxPd"

            if access_token:  # 如果有access_token
                try:
                    print(f"使用access_token: {access_token[:10]}... 爬取banklaw.com")
                    
                    # 创建爬虫实例，只传入access_token
                    crawler = Crawler(access_token=access_token)
                    
                    # 使用指定的层级ID爬取内容
                    total, failed = crawler.crawl_by_api_responses(hierarchy_id, year,if_chufa)
                    
                    print(f"爬取完成，共下载 {total} 条{hierarchy_name}，失败 {failed} 条")
                    #这里需要根据一定条件跳出循环，这里可以根据failed的数量来判断
                    if failed == 0:
                        break
                    # 如果失败率过高，可能是token失效
                    if total == 0 or (total > 0 and failed / total > 0.5):
                        print("失败率过高，可能access_token已失效")
                        self.refresh_access_token()  # 刷新token
                    
                    # 成功爬取后，休息一段时间再继续
                    sleep_time = random.uniform(30, 60)
                    print(f"休息 {sleep_time:.2f} 秒后继续...")
                    time.sleep(sleep_time)
                    
                except Exception as e:
                    print(f"爬取失败: {e}")
                    print("可能是access_token已失效，尝试刷新...")
                    self.refresh_access_token()  # 刷新token
                    time.sleep(5)  # 等待5秒后继续
            else:
                print("没有可用的access_token，尝试获取...")
                self.refresh_access_token()  # 获取新token
                time.sleep(5)  # 等待5秒后继续

    def check_year_data(self, hierarchy_id, year):
        """检查指定层级和年份的数据是否已爬取"""
        file_lujing = f"downloaded_regulations/hierarchy_{hierarchy_id}_{HIERARCHIES[hierarchy_id]}/{year}"
        if not os.path.exists(file_lujing):
            #判断这个路径中是否有文件
            return False
        return True
