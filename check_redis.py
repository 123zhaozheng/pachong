#!/usr/bin/env python
# -*- coding: utf-8 -*-

import redis
import json
from wechat_crawler.config import (
    REDIS_HOST,
    REDIS_PORT,
    REDIS_DB,
    REDIS_PASSWORD
)

def check_redis_content():
    """连接Redis并查看其内容"""
    try:
        # 连接到Redis
        redis_conn = redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            db=REDIS_DB,
            password=REDIS_PASSWORD,
            decode_responses=True  # 自动将字节解码为字符串
        )
        
        # 测试连接
        print("Redis连接状态:", "成功" if redis_conn.ping() else "失败")
        print("\n" + "="*50)
        
        # 获取所有keys
        all_keys = redis_conn.keys("*")
        print(f"Redis中共有 {len(all_keys)} 个key:")
        
        # 遍历并显示每个key的内容
        for key in all_keys:
            print("\n" + "-"*30)
            print(f"Key: {key}")
            
            # 获取key的类型
            key_type = redis_conn.type(key)
            print(f"类型: {key_type}")
            
            # 根据类型获取值
            if key_type == "string":
                value = redis_conn.get(key)
                try:
                    # 尝试解析JSON
                    parsed_value = json.loads(value)
                    print("值 (JSON):", json.dumps(parsed_value, indent=2, ensure_ascii=False))
                except:
                    print("值:", value)
                    
            elif key_type == "list":
                values = redis_conn.lrange(key, 0, -1)
                print(f"列表长度: {len(values)}")
                for i, value in enumerate(values, 1):
                    try:
                        # 尝试解析JSON
                        parsed_value = json.loads(value)
                        print(f"\n列表项 {i}:")
                        print(json.dumps(parsed_value, indent=2, ensure_ascii=False))
                    except:
                        print(f"\n列表项 {i}: {value}")
                        
            elif key_type == "hash":
                values = redis_conn.hgetall(key)
                print("哈希表内容:")
                for field, value in values.items():
                    print(f"  {field}: {value}")
                    
            elif key_type == "set":
                values = redis_conn.smembers(key)
                print("集合内容:", list(values))
                
            elif key_type == "zset":
                values = redis_conn.zrange(key, 0, -1, withscores=True)
                print("有序集合内容:")
                for value, score in values:
                    print(f"  {value}: {score}")
        
    except redis.ConnectionError as e:
        print(f"连接Redis失败: {e}")
    except Exception as e:
        print(f"发生错误: {e}")

if __name__ == "__main__":
    check_redis_content()
