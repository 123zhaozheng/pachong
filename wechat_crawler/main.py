from .crawler_scheduler import CrawlerScheduler
import threading
from .config import (
    NUM_THREADS, TARGET_URL, MAX_PAGES_PER_THREAD
)

def main():
    scheduler = CrawlerScheduler()
    
    # 启动多个爬虫线程
    num_threads = NUM_THREADS
    target_url = TARGET_URL
    max_pages_per_thread = MAX_PAGES_PER_THREAD
    
    threads = []
    for i in range(num_threads):
        t = threading.Thread(
            target=scheduler.start_crawler, 
            args=(target_url, max_pages_per_thread),
            name=f"crawler-{i+1}"
        )
        t.daemon = True
        t.start()
        print(f"启动爬虫线程 {i+1}")
        threads.append(t)
    
    try:
        # 主线程保持运行
        for t in threads:
            t.join()
    except KeyboardInterrupt:
        print("接收到终止信号，程序退出")

if __name__ == "__main__":
    main()
