import os
import random
import redis  # 导入redis库，用于连接Redis数据库
import time  # 导入time库，用于实现延时功能
import threading  # 导入threading库，用于实现多线程操作
import json  # 导入json库，用于处理JSON数据
import requests  # 导入requests库，用于发送HTTP请求
from .wechat_login import WechatLogin  # 从当前包中导入WechatLogin类，用于微信登录
from .crawler import Crawler  # 从当前包中导入Crawler类，用于爬取数据
from .config import (  # 从配置文件导入所需的配置参数
    REDIS_HOST, REDIS_PORT, REDIS_DB, REDIS_PASSWORD,  # Redis连接参数
    MAX_REQUESTS_PER_COOKIE,  # 每个cookie可以发送的最大请求数
    REQUIRED_TOKEN_COUNT,  # 需要的access_token数量
    BANKLAW_API_URL  # API基础URL
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
        # self.cookie_usage = {}  # 初始化cookie使用计数字典
        self.lock = threading.Lock()  # 创建线程锁，用于多线程环境下对共享资源的访问控制
        self.access_token = None  # 初始化access_token为None
        self.wechat_login = None
        self.is_running = True
        
        # 检查是否已有access_token
        self._check_access_token()
        
    def _check_access_token(self):  # 检查是否已有access_token
        """检查Redis中是否已有足够数量的access_token"""
        # 检查单个token（兼容旧代码）
        token = self.redis_conn.get('access_token')  # 从Redis获取access_token
        if token:  # 如果token存在
            self.access_token = token.decode('utf-8')  # 解码并存储
            print(f"从Redis加载access_token: {self.access_token[:10]}...")
        
        # 检查token列表
        token_count = self.redis_conn.llen('access_tokens')
        print(f"Redis中已有 {token_count} 个access_token，需要 {REQUIRED_TOKEN_COUNT} 个")
        
        if token_count >= REQUIRED_TOKEN_COUNT:
            return True
        return False
    
    def check_token_health(self, token):
        """检查token是否健康"""
        print(f"正在检查token健康状态: {token}...")
        try:
            # 使用token调用一个简单的API，例如获取用户信息
            headers = {
                "Accept": "application/json",
                "Accept-Encoding": "gzip, deflate, br, zstd",
                "Accept-Language": "zh-CN,zh;q=0.9",
                "Access-Token": token,
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Content-Type": "application/json; charset=utf-8",
                "Host": "api2.banklaw.com",
                "Origin": "https://www.banklaw.com",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36"
            }
            body = {
                "pageIndex": 2,
                "pageSize": 10,
                "sort": 1,
                "exactMatch": True,
                "securityLevel": "",
                "hierarchyAliasId": 1,
                "needImportantNews": True,
                "content": "",
                "organizationName": "",
                "referenceNo": "",
                "beginPublishDate": "2022-01-01",
                "endPublishDate": "2022-01-30",
                "code": 2,
                "nochild": False,
                "statusChangeContainDoubleDate": 0
            }
            
            # 尝试访问一个简单的API端点
            response = requests.post(
                f"https://api2.banklaw.com/search/v1/statutes/search?1742280914627",
                headers=headers,
                json=body,
                timeout=10
            )
            
            # 检查响应状态码和响应内容
            if response.status_code == 200:
                # 解析响应内容
                try:
                    response_data = response.json()
                    # 检查是否有错误码
                    if 'code' in response_data and response_data['code'] != 0:
                        error_message = response_data.get('message', '未知错误')
                        print(f"Token健康检查失败，错误信息: {error_message}")
                        return False
                    # 检查是否包含"您今日请求数已超过限制"等错误信息
                    if 'message' in response_data and '超过限制' in response_data['message']:
                        print(f"Token健康检查失败，错误信息: {response_data['message']}")
                        return False
                    #对目录的非第一页查询是否会跳入第一页
                    if response_data['data']['pageIndex'] == 0:
                        return False
                    print(f"Token健康检查通过: {token[:10]}...")
                    return True
                except json.JSONDecodeError:
                    print(f"Token健康检查失败，无法解析响应内容")
                    return False
            else:
                print(f"Token健康检查失败，状态码: {response.status_code}")
                return False
        except Exception as e:
            print(f"Token健康检查异常: {e}")
            return False
    
    def get_healthy_token(self):
        """获取一个健康的token"""
        # 获取所有token
        all_tokens = self.redis_conn.lrange('access_tokens', 0, -1)
        if not all_tokens:
            print("Redis中没有存储的token")
            return None
            
        # 随机打乱token顺序，避免总是使用同一个token
        all_tokens_list = list(all_tokens)
        random.shuffle(all_tokens_list)
        
        for token_data in all_tokens_list:
            try:
                # 解析token数据（包含token和用户信息）
                token_info = json.loads(token_data.decode('utf-8'))
                token = token_info['token']
                user_name = token_info.get('user_name', '未知')
                
                # 进行健康检查
                if self.check_token_health(token):
                    print(f"找到健康的token: {token[:10]}... (用户: {user_name})")
                    return token
                else:
                    # 移除不健康的token
                    print(f"移除不健康的token: {token[:10]}... (用户: {user_name})")
                    self.redis_conn.lrem('access_tokens', 0, token_data)
            except Exception as e:
                print(f"检查token健康状态时出错: {e}")
                # 移除格式错误的token
                self.redis_conn.lrem('access_tokens', 0, token_data)
                
        return None
    
    def get_access_token(self):  # 获取access_token的方法
        """获取access_token，如果Redis中存在则使用，否则返回None"""
        with self.lock:  # 使用线程锁，确保对共享资源的安全访问
            # 检查Redis中token数量是否满足要求
            token_count = self.redis_conn.llen('access_tokens')
            
            # 如果token数量不足，尝试获取更多token
            if token_count < REQUIRED_TOKEN_COUNT:
                print(f"Redis中token数量不足，当前有 {token_count} 个，需要 {REQUIRED_TOKEN_COUNT} 个")
                self.ensure_enough_tokens()
            
            # 尝试获取健康的token
            healthy_token = self.get_healthy_token()
            if healthy_token:
                self.access_token = healthy_token
                return healthy_token
                
            # 如果没有健康的token，尝试刷新
            print("没有健康的token可用，尝试刷新...")
            self.ensure_enough_tokens()
            
            # 再次尝试获取健康的token
            healthy_token = self.get_healthy_token()
            if healthy_token:
                self.access_token = healthy_token
                return healthy_token
            
            # 如果仍然没有健康的token，尝试使用旧方法获取单个token
            token = self.redis_conn.get('access_token')
            if token:
                self.access_token = token.decode('utf-8')
                print(f"从Redis单个键获取token: {self.access_token[:10]}...")
                return self.access_token
                
            return None
    
    def ensure_enough_tokens(self):
        """确保Redis中有足够数量的token"""
        token_count = self.redis_conn.llen('access_tokens')
        needed_tokens = REQUIRED_TOKEN_COUNT - token_count
        
        if needed_tokens <= 0:
            print(f"Redis中已有足够的token: {token_count} 个")
            return True
        
        print(f"需要获取 {needed_tokens} 个新token")
        
        # 连续获取多个token
        for i in range(needed_tokens):
            print(f"正在获取第 {i+1}/{needed_tokens} 个token...")
            success = self.refresh_access_token()
            if not success:
                print(f"获取第 {i+1} 个token失败，停止获取")
                return False
            # 每次获取token后等待一段时间，避免频繁请求
            if i < needed_tokens - 1:  # 不是最后一个token
                wait_time = random.uniform(2, 5)
                print(f"等待 {wait_time:.2f} 秒后继续获取下一个token...")
                time.sleep(wait_time)
        
        # 再次检查token数量
        token_count = self.redis_conn.llen('access_tokens')
        print(f"已成功获取所需token，当前Redis中有 {token_count} 个token")
        return token_count >= REQUIRED_TOKEN_COUNT
    
    def show_tokens_status(self):
        """显示所有token的状态"""
        all_tokens = self.redis_conn.lrange('access_tokens', 0, -1)
        if not all_tokens:
            print("Redis中没有存储的token")
            return
            
        print("\n当前Token状态:")
        print("-" * 80)
        print(f"{'用户':20} {'创建时间':20} {'过期时间':20} {'状态':10}")
        print("-" * 80)
        
        for token_data in all_tokens:
            try:
                token_info = json.loads(token_data.decode('utf-8'))
                token = token_info.get('token', '')
                user_name = token_info.get('user_name', '未知')
                created_at = token_info.get('created_at', '未知')
                expires_at = token_info.get('expires_at', '未知')
                
                # 检查token健康状态
                is_healthy = self.check_token_health(token)
                status = "正常" if is_healthy else "失效"
                
                print(f"{user_name:20} {created_at:20} {expires_at:20} {status:10}")
            except Exception as e:
                print(f"无法解析token数据: {e}")
                
        print("-" * 80)
    
 
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
                access_token = self.get_access_token()

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
            access_token = self.get_access_token()

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
                        self.get_access_token()  # 刷新token
                    
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
if __name__ == "__main__":
    scheduler = CrawlerScheduler()
    scheduler.show_tokens_status()
