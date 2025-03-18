# 从当前包导入爬虫调度器类，负责管理和协调爬虫任务
import time
from .crawler_scheduler import CrawlerScheduler
# 导入线程模块，用于实现多线程爬虫
import threading
# 导入json模块，用于处理JSON数据
import json
# 导入sys模块，用于获取命令行参数
import sys
# 导入random模块，用于生成随机数
import random
# 从配置文件导入必要的常量参数
from .config import MAX_PAGES_PER_THREAD,START_YEAR, END_YEAR, IF_CHUFA,THREAD_ID,IF_ON

# banklaw.com网站的URL
BANKLAW_URL = "https://www.banklaw.com"

# 分类定义
HIERARCHIES = {
    1: "法律法规",
    2: "规章制度",
    3: "行业动态"
}

def parse_args():
    """解析命令行参数"""
    args = {
        'thread_id': 1 , # 默认为线程1（法律法规）
        'if_chufa': 0
    }
    
    # 遍历所有命令行参数
    for arg in sys.argv[1:]:
        if arg == '--help' or arg == '-h':
            print_help()
            sys.exit(0)
        elif arg.isdigit() and 1 <= int(arg) <= 3:
            args['thread_id'] = int(arg)
        else:
            print(f"无效的参数: {arg}")
            print_help()
            sys.exit(1)
            
    return args

def print_help():
    """打印帮助信息"""
    print(f"""
爬取banklaw.com法规的爬虫程序

用法: python run.py [线程ID]

线程ID:
  1       爬取法律法规 (默认)
  2       爬取规章制度
  3       爬取行业动态
  
  --help, -h         显示此帮助信息

示例:
  python run.py 1    # 爬取法律法规
  python run.py 2    # 爬取规章制度
  python run.py 3    # 爬取行业动态
    """)

def main():
    #判断是否启用配置文件
    if IF_ON == 0:
        print("配置文件中未启用")
    # 解析命令行参数
        args = parse_args()
        thread_id = args['thread_id']
        if_chufa = args['if_chufa']
    else:
        thread_id = THREAD_ID
        if_chufa = IF_CHUFA
        
    
    # 创建爬虫调度器实例
    scheduler = CrawlerScheduler()
    
    # 显示所有token的状态
    scheduler.show_tokens_status()
    
    # 检查是否有足够的健康token
    if not scheduler.get_access_token():
        print("没有可用的健康access_token，将尝试通过微信扫码登录获取")
        # 确保有足够的token
        scheduler.ensure_enough_tokens()
    
    # 获取线程对应的层级ID和名称
    hierarchy_id = thread_id
    hierarchy_name = HIERARCHIES[hierarchy_id]
    #判断是否直接导出案例
    if if_chufa == 1:
        #直接处理案例
        scheduler.start_crawler(if_chufa = 1)
    print(f"启动爬虫线程 {thread_id}，处理内容：{hierarchy_name}")
    for year in range(START_YEAR,END_YEAR+1):
        print(year,"-"*50)
        #进行简单的判断，看是否这个年份的数据已经爬取过了(已经有方法可以对每个文件进行判断是否爬取，此步骤废弃)
        # if scheduler.check_year_data(hierarchy_id,year):
        #     print(f"{year}年的数据已经爬取过了，跳过")
        #     continue
        #应该在这获取年份了
        print(f"开始爬取 {hierarchy_name}，年份: {year}")
        time.sleep(5)
        # 启动爬虫
        try:
            # 根据线程ID传递对应的层级ID
            scheduler.start_crawler(hierarchy_id=hierarchy_id, year=year, if_chufa=if_chufa)
        except KeyboardInterrupt:
            # 捕获键盘中断（Ctrl+C），实现优雅退出
            print("接收到终止信号，程序退出")

# 确保脚本直接执行时才运行main函数，而非被导入时
if __name__ == "__main__":
    main()  # 执行主函数
