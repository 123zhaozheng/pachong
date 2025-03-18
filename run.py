#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
banklaw.com法规爬虫启动脚本
"""

import os
import sys
import time
import json
from wechat_crawler.main import main, print_help
from wechat_crawler.monthly_crawler import process_data_by_hierarchy_and_year
from wechat_crawler.config import IF_CHERK

def check_monthly_data():
    """检查monthly_crawler的数据是否已生成"""
    hierarchies = {1: "法律法规", 2: "规章制度", 3: "行业动态"}
    current_year = time.localtime().tm_year
    
    for hierarchy_id, hierarchy_name in hierarchies.items():
        dir_path = f'api_responses/hierarchy_{hierarchy_id}_{hierarchy_name}/{current_year}'
        if not os.path.exists(dir_path):
            return False
            
        # 检查当前月份之前的文件是否存在
        current_month = time.localtime().tm_mon
        for month in range(1, current_month + 1):
            file_path = f'{dir_path}/api_response_{month}.json'
            if not os.path.exists(file_path):
                return False
                
            # 验证文件内容
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                if not data.get('data'):
                    return False
            except:
                return False
                
    return True

def generate_monthly_data():
    """生成monthly_crawler的数据"""
    print("=" * 60)
    print("正在生成月度数据源...")
    print("=" * 60)
    process_data_by_hierarchy_and_year()
    print("月度数据源生成完成")
    print("=" * 60)

if __name__ == "__main__":
    print("=" * 60)
    print("banklaw.com法规爬虫启动")
    print("=" * 60)
    #根据config.py中的IF_CHERK来判断是否要生成爬虫源
    if IF_CHERK :
        if not check_monthly_data():
            print("月度数据源不完整，需要重新生成")
            generate_monthly_data()
        else:
            print("月度数据源检查完成")
               
    print("该爬虫将通过微信扫码登录banklaw.com获取access-token")
    print("然后使用爬虫爬取法规网站内容，并保存到本地")
    print("当access-token失效时，系统会自动提示扫码刷新")
    print("=" * 60)
    print("爬虫线程说明：")
    print("1 - 爬取法律法规")
    print("2 - 爬取规章制度")
    print("3 - 爬取行业动态")
    print("使用方法：python run.py [方向ID]")
    print("=" * 60)
    
    try:
        main()
    except KeyboardInterrupt:
        print("\n正在安全退出程序...")
        # 给线程一些时间来清理资源
        time.sleep(1)
        print("程序已退出")
        sys.exit(0)
    except Exception as e:
        print(f"程序发生错误: {e}")
        time.sleep(2)
        sys.exit(1)
