import requests
from bs4 import BeautifulSoup
import os
import time
import random
import json
from datetime import datetime
from .config import (
    TARGET_URL, SAVE_DIR, 
    DOWNLOAD_DELAY_MIN, DOWNLOAD_DELAY_MAX,
    PAGE_DELAY_MIN, PAGE_DELAY_MAX
)

# API相关常量
BANKLAW_API_URL = "https://api2.banklaw.com"
STATUTE_API_URL = "https://api2.banklaw.com/v1/statutes/{statute_id}"

# 分类定义
HIERARCHIES = {
    1: "法律法规",
    2: "规章制度",
    3: "行业动态"
}

def process_legal_regulation(data):
    """处理法律法规类型的数据"""
    content = []
    try:
        if not isinstance(data, dict):
            return ""
            
        detail = data.get('data', {})
        if not detail:
            return ""
            
        # 添加基本信息
        content.append(f"标题: {detail.get('title', '')}")
        content.append(f"发文字号: {detail.get('documentNo', '')}")
        content.append(f"发布日期: {detail.get('publishDate', '')}")
        content.append(f"生效日期: {detail.get('effectiveDate', '')}")
        content.append(f"发布机构: {detail.get('publishingDepartment', '')}")
        content.append("\n" + "="*50 + "\n")
        
        # 添加正文内容
        if 'content' in detail:
            content.append(detail['content'])
            
        return "\n".join(content)
    except Exception as e:
        print(f"处理法律法规数据失败: {e}")
        return ""

def process_regulatory_rule(data):
    """处理规章制度类型的数据"""
    content = []
    try:
        if not isinstance(data, dict):
            return ""
            
        detail = data.get('data', {})
        if not detail:
            return ""
            
        # 添加基本信息
        content.append(f"标题: {detail.get('title', '')}")
        content.append(f"文号: {detail.get('documentNo', '')}")
        content.append(f"发布时间: {detail.get('publishDate', '')}")
        content.append(f"实施时间: {detail.get('effectiveDate', '')}")
        content.append(f"发布部门: {detail.get('department', '')}")
        content.append("\n" + "="*50 + "\n")
        
        # 添加正文内容
        if 'content' in detail:
            content.append(detail['content'])
            
        return "\n".join(content)
    except Exception as e:
        print(f"处理规章制度数据失败: {e}")
        return ""

def process_industry_news(data):
    """处理行业动态类型的数据"""
    content = []
    try:
        if not isinstance(data, dict):
            return ""
            
        detail = data.get('data', {})
        if not detail:
            return ""
            
        # 添加基本信息
        content.append(f"标题: {detail.get('title', '')}")
        content.append(f"发布时间: {detail.get('publishTime', '')}")
        content.append(f"来源: {detail.get('source', '')}")
        content.append(f"作者: {detail.get('author', '')}")
        content.append("\n" + "="*50 + "\n")
        
        # 添加正文内容
        if 'content' in detail:
            content.append(detail['content'])
            
        return "\n".join(content)
    except Exception as e:
        print(f"处理行业动态数据失败: {e}")
        return ""

# 每个分类的数据处理函数
HIERARCHY_PROCESSORS = {
    1: process_legal_regulation,
    2: process_regulatory_rule,
    3: process_industry_news
}

class Crawler:
    def __init__(self, cookie=None, access_token=None):
        """初始化爬虫实例"""
        self.access_token = access_token
        self.cookie = cookie
        
        # self.headers = {
        #     'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36',
        #     'Accept': 'application/json',
        #     'Accept-Language': 'zh-CN,zh;q=0.9',
        #     'Cache-Control': 'no-cache',
        #     'Connection': 'keep-alive',
        #     'Content-Type': 'application/json; charset=utf-8',
        #     'Pragma': 'no-cache',
        #     'Sec-Fetch-Dest': 'empty',
        #     'Sec-Fetch-Mode': 'cors',
        #     'Sec-Fetch-Site': 'same-site',
        #     'sec-ch-ua': '"Chromium";v="134", "Not:A-Brand";v="24", "Google Chrome";v="134"',
        #     'sec-ch-ua-mobile': '?0',
        #     'sec-ch-ua-platform': 'Windows',
        #     'sourceType': '1'
        # }
        self.headers = {
                "Accept": "application/json",
                "Accept-Encoding": "gzip, deflate, br, zstd",
                "Accept-Language": "zh-CN,zh;q=0.9",
                "Access-Token": "yON3YgFuomVjA6VX9pAiH+QTlTmlRK8SOvkmv+JchVG2CRspG2neoC8U/5cGnxPd",
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Content-Type": "application/json; charset=utf-8",
                "Host": "api2.banklaw.com",
                "Origin": "https://www.banklaw.com",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36"
        }
        
        if self.access_token:
            self.headers['Access-Token'] = self.access_token
        
        if self.cookie:
            self.headers['Cookie'] = self.cookie
            
        self.base_url = BANKLAW_API_URL
        self.save_dir = SAVE_DIR
        
        if not os.path.exists(self.save_dir):
            os.makedirs(self.save_dir)
            
        print(f"爬虫初始化完成，使用API: 未知后续需要修改")
        if self.access_token:
            print(f"使用Access-Token: {self.access_token[:10]}...")

    def download_regulation(self, regulation, hierarchy_id=None, year=None):

        """下载单个法规文本"""
        try:
            #构建爬取路径
            statute_id = regulation.get('statuteId') or regulation.get('id')
            api_url = f'https://api2.banklaw.com/v1/statutes/{statute_id}?focusBatchId=&needSentence=true&tagProjectId=51&needParagraph=true&1742199313084'
            self.base_url = api_url
            title = regulation.get('title')
            
            if not statute_id:
                raise Exception("未找到法规ID")
            
            print(f"下载法规: {title} (ID: {statute_id})")
            
            # api_url = STATUTE_API_URL.format(statute_id=statute_id)
            # params = {
            #     'focusBatchId': '',
            #     'needSentence': 'true',
            #     'tagProjectId': '51',
            #     'needParagraph': 'true'
            # }
            # headers = {
            #     "Accept": "application/json",
            #     "Accept-Encoding": "gzip, deflate, br, zstd",
            #     "Accept-Language": "zh-CN,zh;q=0.9",
            #     "Access-Token": "yON3YgFuomVjA6VX9pAiH+QTlTmlRK8SOvkmv+JchVG2CRspG2neoC8U/5cGnxPd",
            #     "Cache-Control": "no-cache",
            #     "Connection": "keep-alive",
            #     "Content-Type": "application/json; charset=utf-8",
            #     "Host": "api2.banklaw.com",
            #     "Origin": "https://www.banklaw.com",
            #     "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36"
            # }
            response = requests.get(api_url, headers=self.headers)
            
            if response.status_code != 200:
                print(f"请求失败: HTTP {response.status_code}")
                print(f"响应内容: {response.text[:200]}")
                raise Exception(f"下载法规失败: {response.status_code}")
            
            data = response.json()
            print(data)
            print("+++++++++++++++++++++++++++++")

            #简单写法，通过传过来的hierarchy_id来判断是哪种类型的法规，然后调用对应的处理函数
            content = HIERARCHY_PROCESSORS[hierarchy_id](data)
            #下面是要写对应的处理函数是啥把，这里先简单写了一个，后面再改
            
            #直接保存试试

            
            # # 根据不同分类处理数据
            # if hierarchy_id and hierarchy_id in HIERARCHY_PROCESSORS:
            #     content = HIERARCHY_PROCESSORS[hierarchy_id](data)
            # else:
            #     content = self._extract_regulation_content(data)
            
            # if not content:
            #     raise Exception("未找到法规内容")
            
            # 构造保存目录
            save_dir = self.save_dir
            if hierarchy_id:
                hierarchy_name = HIERARCHIES.get(hierarchy_id, "其他")
                save_dir = os.path.join(save_dir, f"hierarchy_{hierarchy_id}_{hierarchy_name}")
                if not os.path.exists(save_dir):
                    os.makedirs(save_dir)
            
            # 构造保存文件名，将上面的save_dir\year和title拼接起来
            temp_dir = f'{save_dir}\{str(year)}'
            if not os.path.exists(temp_dir):
                os.makedirs(temp_dir)
            safe_title = os.path.join(temp_dir, title+'.txt')
            #hierarchy_dir = f'api_responses/hierarchy_{hierarchy_id}_{hierarchy_name}'

            # filename = os.path.join(save_dir, f"{statute_id}_{safe_title}.txt")
            
            # 保存文件
            with open(safe_title, 'w', encoding='utf-8') as f:
                formatted_data = json.dumps(data, ensure_ascii=False, indent=2)
                f.write(formatted_data)
            
            print(f"成功下载法规: {title}")
            print(f"保存到: {safe_title}")
            
            time.sleep(random.uniform(DOWNLOAD_DELAY_MIN, DOWNLOAD_DELAY_MAX))
            return True
            
        except Exception as e:
            print(f"下载法规失败: {e}")
            return False

    def _extract_regulation_content(self, data):
        """从响应数据中提取法规内容"""
        content = []
        try:
            if not isinstance(data, dict):
                return ""
                
            detail = data.get('data', {})
            if not detail:
                return ""
            
            # 添加基本信息
            content.append(f"标题: {detail.get('title', '')}")
            content.append(f"文号: {detail.get('documentNo', '')}")
            content.append(f"发布日期: {detail.get('publishDate', '')}")
            content.append(f"生效日期: {detail.get('effectiveDate', '')}")
            content.append(f"发布机构: {detail.get('publishingDepartment', '')}")
            content.append("\n" + "="*50 + "\n")
            
            # 添加正文内容
            if 'content' in detail:
                content.append(detail['content'])
                
            return "\n".join(content)
        except Exception as e:
            print(f"提取法规内容失败: {e}")
            return ""

    def crawl_by_api_responses(self, hierarchy_id, year=2022):
        """根据层级以及年份爬取对应类型的法规
        
        Args:
            hierarchy_id: 法规层级ID（1:法律法规, 2:规章制度, 3:行业动态）
            year: 年份
            
        Returns:
            tuple: (成功爬取数量, 失败数量)
        """
        hierarchy_name = HIERARCHIES.get(hierarchy_id, "法律法规")
        #读取api_responses文件夹下的json文件
        dir_path = f'api_responses/hierarchy_{hierarchy_id}_{hierarchy_name}/{year}'
        if not os.path.exists(dir_path):
            return 0, 0
        #循环读取此路径下的json文件，每读一个，爬虫一个
        total_success = 0
        total_failed = 0
        for month in range(1, 13):
            file_path = f'{dir_path}/api_response_{month}.json'
            if not os.path.exists(file_path):
                continue
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    print(data)
                if not data.get('data'):
                    raise Exception("无效的数据")
                
                for item in data['data']:
                    # 下载法规详情
                    success = self.download_regulation(item, hierarchy_id, year)
                    if success:
                        total_success += 1
                    else:
                        total_failed += 1
            except Exception as e:
                print(f"处理文件 {file_path} 时发生错误: {e}")
                total_failed += 1
        # print(f"开始爬取 {hierarchy_name}，层级ID: {hierarchy_id}")
        
        # # 确保保存目录存在
        # save_dir = os.path.join(self.save_dir, f"hierarchy_{hierarchy_id}_{hierarchy_name}")
        # if not os.path.exists(save_dir):
        #     os.makedirs(save_dir)
        
        # total_success = 0
        # total_failed = 0
        
        # # 构造API请求参数
        # api_url = f"{self.base_url}/v1/statutes/search"
        
        # for page in range(max_pages):
        #     try:
        #         print(f"正在爬取 {hierarchy_name} 第 {page + 1}/{max_pages} 页...")
                
        #         # 构造请求数据
        #         payload = {
        #             "pageIndex": page,
        #             "pageSize": 10,
        #             "sort": 1,
        #             "exactMatch": True,
        #             "securityLevel": "",
        #             "hierarchyAliasId": hierarchy_id,
        #             "needImportantNews": True,
        #             "content": "",
        #             "organizationName": "",
        #             "referenceNo": "",
        #             "beginPublishDate": "",
        #             "endPublishDate": "",
        #             "code": 2,
        #             "nochild": False,
        #             "statusChangeContainDoubleDate": 0
        #         }
                
        #         # 发送请求
        #         response = requests.post(api_url, headers=self.headers, json=payload)
                
        #         # 确保请求成功
        #         if response.status_code != 200:
        #             print(f"请求失败，状态码: {response.status_code}")
        #             total_failed += 1
        #             continue
                
        #         # 解析响应数据
        #         data = response.json()
        #         if 'data' not in data or 'rows' not in data['data']:
        #             print("响应数据格式错误")
        #             total_failed += 1
        #             continue
                
        #         # 遍历结果列表
        #         for item in data['data']['rows']:
        #             if 'statuteId' in item:
        #                 # 下载法规详情
        #                 success = self.download_regulation(item, hierarchy_id)
        #                 if success:
        #                     total_success += 1
        #                 else:
        #                     total_failed += 1
                
        #         # 页面间延迟
        #         delay = random.uniform(PAGE_DELAY_MIN, PAGE_DELAY_MAX)
        #         print(f"等待 {delay:.2f} 秒后继续...")
        #         time.sleep(delay)
                
        #     except Exception as e:
        #         print(f"爬取第 {page + 1} 页时发生错误: {e}")
        #         total_failed += 1
                
        #         # 出错时适当延迟
        #         time.sleep(random.uniform(5, 10))
        
        # print(f"{hierarchy_name} 爬取完成，成功: {total_success}, 失败: {total_failed}")
        return total_success, total_failed
