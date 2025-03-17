import requests
import datetime
import json
import os
import time


#调用对应的API接口，获取相应月份的数据简报
def call_api(start_date, end_date, page_index=0, hierarchy_id=1):
    """调用API获取数据"""
    api_url = "https://api2.banklaw.com/search/v1/statutes/search?1742208260648"
    
    headers = {
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
    
    body = {
        "pageIndex": page_index,
        "pageSize": 10,
        "sort": 1,
        "exactMatch": True,
        "securityLevel": "",
        "hierarchyAliasId": hierarchy_id,
        "needImportantNews": True,
        "content": "",
        "organizationName": "",
        "referenceNo": "",
        "beginPublishDate": start_date,
        "endPublishDate": end_date,
        "code": 2,
        "nochild": False,
        "statusChangeContainDoubleDate": 0
    }
    
    try:
        response = requests.post(api_url, headers=headers, json=body)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"API调用失败: {e}")
        return None

def save_response(data, month):
    """保存API响应报文"""
    filename = f"api_response_{month}.json"
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"已保存报文: {filename}")

def process_monthly_data(year, month, hierarchy_id, save_dir):
    """处理指定年月的数据"""
    start_date = f"{year}-{month:02d}-01"
    if month == 12:
        end_date = f"{year}-12-31"
    else:
        end_date = f"{year}-{month+1:02d}-01"
    
    all_data = []
    page_index = 0
    
    while True:
        print(f"正在获取 {year}年{month}月 第{page_index + 1}页数据...")
        data = call_api(start_date, end_date, page_index, hierarchy_id)
        
        if not data or not data.get('data', {}).get('rows'):
            print("没有更多数据")
            break
            
        # 仅提取statuteId和title字段
        for item in data['data']['rows']:
            all_data.append({
                'statuteId': item.get('statuteId'),
                'title': item.get('title')
            })
        
        print("暂停5秒后继续获取下一页...")
        time.sleep(5)
        page_index += 1
    
    if all_data:
        filename = os.path.join(save_dir, f"api_response_{month}.json")
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump({
                'year': year,
                'month': month,
                'hierarchy_id': hierarchy_id,
                'total': len(all_data),
                'data': all_data
            }, f, ensure_ascii=False, indent=2)
        print(f"已保存报文: {filename}")

def process_data_by_hierarchy_and_year():
    """按层级和年份处理数据"""
    hierarchies = {
        1: "法律法规",
        2: "规章制度", 
        3: "行业动态"
    }
    
    years = range(2022, 2026)
    
    if not os.path.exists('api_responses'):
        os.makedirs('api_responses')
    
    for hierarchy_id, hierarchy_name in hierarchies.items():
        hierarchy_dir = f'api_responses/hierarchy_{hierarchy_id}_{hierarchy_name}'
        if not os.path.exists(hierarchy_dir):
            os.makedirs(hierarchy_dir)
            
        for year in years:
            year_dir = f'{hierarchy_dir}/{year}'
            if not os.path.exists(year_dir):
                os.makedirs(year_dir)
                
            print(f"\n开始处理 {hierarchy_name} {year}年的数据...")
            
            for month in range(1, 13):
                process_monthly_data(year, month, hierarchy_id, year_dir)

if __name__ == "__main__":
    process_data_by_hierarchy_and_year()
