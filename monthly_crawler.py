import requests
import datetime
import json
import os
import time


#调用对应的API接口，获取相应月份的数据简报
def call_api(start_date=None, end_date=None, page_index=0, hierarchy_id=1, if_chufa=0):
    """调用API获取数据
    
    Args:
        start_date: 开始日期，处罚数据不需要此参数
        end_date: 结束日期，处罚数据不需要此参数
        page_index: 页码索引
        hierarchy_id: 层级ID
        if_chufa: 是否为处罚数据，0为法规数据，1为处罚数据
        
    Returns:
        API响应的JSON数据
    """
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
    
    if if_chufa == 1:
        # 处罚数据API
        api_url = "https://api2.banklaw.com/search/v1/casus/search?1742266630148"
        body = {
            "pageIndex": page_index,
            "pageSize": 30,
            "sort": 1,
            "exactMatch": True,
            "securityLevel": "",
            "needImportantNews": True,
            "content": "",
            "organizationName": "",
            "referenceNo": "",
            "code": 2,
            "nochild": False,
            "statusChangeContainDoubleDate": 0
        }
    else:
        # 法规数据API
        api_url = "https://api2.banklaw.com/search/v1/statutes/search?1742208260648"
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
def process_data_chufa():
    """处理处罚数据"""
    print("*" * 50 + "开始处理处罚数据" + "*" * 50)
    
    # 创建保存处罚数据的目录
    chufa_dir = 'api_responses/chufa'
    if not os.path.exists(chufa_dir):
        os.makedirs(chufa_dir)
    
    all_data = []
    page_index = 0
    
    while True:
        print(f"正在获取处罚数据第{page_index + 1}页...")
        # 调用API获取处罚数据，if_chufa=1表示获取处罚数据
        data = call_api(if_chufa=1, page_index=page_index)
        print(data)
        
        if not data or not data.get('data', {}).get('rows'):
            print("没有更多处罚数据")
            break
        
        # 提取casusId和title字段
        for item in data['data']['rows']:
            all_data.append({
                'casusId': item.get('casusId'),
                'title': item.get('title')
            })
        
        print("暂停5秒后继续获取下一页...")
        time.sleep(5)
        page_index += 1
    
    if all_data:
        # 保存处罚数据到文件
        filename = os.path.join(chufa_dir, "api_response_chufa.json")
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump({
                'type': 'chufa',
                'total': len(all_data),
                'data': all_data
            }, f, ensure_ascii=False, indent=2)
        print(f"已保存处罚数据: {filename}")
        print(f"共获取到 {len(all_data)} 条处罚数据")
    else:
        print("未获取到任何处罚数据")
    
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

def main():
    """主函数，程序入口点"""
    # 询问用户要处理的数据类型
    print("请选择要处理的数据类型:")
    print("1. 法规数据 (按层级和年份)")
    print("2. 处罚数据")
    print("3. 全部数据")
    
    choice = input("请输入选择 (1/2/3): ").strip()
    
    if choice == '1':
        process_data_by_hierarchy_and_year()
    elif choice == '2':
        process_data_chufa()
    elif choice == '3':
        process_data_by_hierarchy_and_year()
        process_data_chufa()
    else:
        print("无效的选择，请输入 1, 2 或 3")

if __name__ == "__main__":
    main()
