import requests
from bs4 import BeautifulSoup
import os
import time
import random
from .config import (
    TARGET_URL, SAVE_DIR, 
    DOWNLOAD_DELAY_MIN, DOWNLOAD_DELAY_MAX,
    PAGE_DELAY_MIN, PAGE_DELAY_MAX
)

class Crawler:
    def __init__(self, cookie):
        self.cookie = cookie
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Cookie': self.cookie
        }
        self.base_url = TARGET_URL
        self.save_dir = SAVE_DIR
        
        # 创建保存目录
        if not os.path.exists(self.save_dir):
            os.makedirs(self.save_dir)
    
    def get_regulation_list(self, page=1):
        """获取法规列表页"""
        url = f"{self.base_url}/list?page={page}"
        response = requests.get(url, headers=self.headers)
        
        if response.status_code != 200:
            raise Exception(f"获取法规列表失败: {response.status_code}")
            
        soup = BeautifulSoup(response.text, 'html.parser')
        regulation_links = []
        
        # 假设法规链接在<a>标签中，class为'regulation-item'
        for link in soup.select('a.regulation-item'):
            regulation_links.append({
                'title': link.text.strip(),
                'url': link['href'] if link['href'].startswith('http') else self.base_url + link['href']
            })
            
        return regulation_links
    
    def download_regulation(self, regulation):
        """下载单个法规文本"""
        try:
            response = requests.get(regulation['url'], headers=self.headers)
            
            if response.status_code != 200:
                raise Exception(f"下载法规失败: {response.status_code}")
                
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 假设法规内容在<div>标签中，id为'regulation-content'
            content_div = soup.select_one('div#regulation-content')
            
            if not content_div:
                raise Exception("未找到法规内容")
                
            content = content_div.text.strip()
            
            # 保存法规文本
            filename = f"{self.save_dir}/{regulation['title']}.txt"
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(content)
                
            print(f"成功下载法规: {regulation['title']}")
            
            # 随机延迟，避免请求过于频繁
            time.sleep(random.uniform(DOWNLOAD_DELAY_MIN, DOWNLOAD_DELAY_MAX))
            
            return True
        except Exception as e:
            print(f"下载法规 {regulation['title']} 失败: {e}")
            return False
    
    def crawl(self, max_pages=10):
        """爬取多页法规"""
        total_count = 0
        failed_count = 0
        
        for page in range(1, max_pages + 1):
            try:
                regulations = self.get_regulation_list(page)
                print(f"第 {page} 页找到 {len(regulations)} 条法规")
                
                for regulation in regulations:
                    success = self.download_regulation(regulation)
                    if success:
                        total_count += 1
                    else:
                        failed_count += 1
                        
                # 页面间随机延迟
                time.sleep(random.uniform(PAGE_DELAY_MIN, PAGE_DELAY_MAX))
                
            except Exception as e:
                print(f"爬取第 {page} 页失败: {e}")
                
        print(f"爬取完成，共下载 {total_count} 条法规，失败 {failed_count} 条")
        return total_count, failed_count
