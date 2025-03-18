import json
import re
import os

def extract_article_from_json(json_data):
    """
    从JSON数据中提取文章内容，并进行格式化处理
    
    参数:
        json_data: JSON字符串或已解析的JSON对象
        
    返回:
        格式化后的文章内容字符串
    """
    # 解析JSON
    data = json.loads(json_data) if isinstance(json_data, str) else json_data
    
    # 获取标题和发布时间
    title = data['data']['title']
    publish_date = data['data']['publishDate']
    
    # 初始化文章内容
    article = f"# {title}\n\n发布时间: {publish_date}\n\n"
    
    # 提取段落内容
    paragraphs = data['data']['paragraphs']
    
    # 按照groupId排序段落
    paragraphs.sort(key=lambda x: x['groupId'])
    
    # 遍历段落并添加到文章中
    for paragraph in paragraphs:
        # 清理HTML标签
        content = re.sub(r'<[^>]+>', '', paragraph['content'])
        # 跳过空段落
        if not content.strip():
            continue
        article += content + "\n\n"
    
    return article

def main():
    # 读取原始JSON文件
    file_path = r"D:\pachong\downloaded_regulations\hierarchy_1_法律法规\2022\downloaded_regulations\hierarchy_1_法律法规\2022\关于建立劳动人事争议“总对总”在线诉调对接机制的通知.txt"
    
    # 检查文件是否存在
    if not os.path.exists(file_path):
        print(f"文件不存在: {file_path}")
        return
    
    # 读取文件内容
    with open(file_path, 'r', encoding='utf-8') as f:
        json_data = f.read()
    
    # 处理JSON数据
    formatted_article = extract_article_from_json(json_data)
    
    # 输出处理后的文章内容
    output_file = "处理后的文章.txt"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(formatted_article)
    
    print(f"文章处理完成，已保存到: {output_file}")
    
    # 打印处理前后的对比信息
    original_data = json.loads(json_data)
    paragraphs_count = len(original_data['data']['paragraphs'])
    
    print("\n处理前后对比:")
    print(f"原始JSON文件大小: {len(json_data)} 字节")
    print(f"原始JSON包含段落数: {paragraphs_count}")
    print(f"处理后文章大小: {len(formatted_article)} 字节")
    
    # 显示处理后文章的前300个字符作为预览
    preview_length = 300
    preview = formatted_article[:preview_length] + "..." if len(formatted_article) > preview_length else formatted_article
    print(f"\n处理后文章预览:\n{preview}")

if __name__ == "__main__":
    main()
