# 微信登录法规爬虫

这是一个通过微信扫码登录获取cookie，然后使用多线程爬取法规网站内容的爬虫程序。

## 功能特点

- 微信扫码登录获取cookie
- 多线程并发爬取，提高效率
- cookie使用次数控制，避免被检测
- cookie失效自动刷新
- 支持多个cookie循环调用
- 自动保存法规文本到本地
- 提供FastAPI接口，方便多机调用

## 环境要求

- Python 3.8+
- Redis 服务器
- Chrome浏览器
- ChromeDriver (与Chrome版本匹配)

## 安装步骤

1. 克隆代码库
```
git clone https://github.com/yourusername/wechat-crawler.git
cd wechat-crawler
```

2. 安装依赖包
```
pip install -r requirements.txt
```

3. 配置Redis
确保Redis服务器已启动，默认配置为localhost:6379。如需修改，请编辑`wechat_crawler/config.py`文件。

4. 修改配置
编辑`wechat_crawler/config.py`文件，设置目标网站URL和其他参数：
```python
TARGET_URL = "https://example.com/regulations"  # 替换为实际的法规网站URL
```

## 使用方法

### 爬虫模式

1. 运行爬虫
```
python run.py
```

2. 扫描二维码
程序启动后会生成二维码图片，使用微信扫描登录。

3. 爬取过程
登录成功后，程序会自动开始爬取法规内容，并保存到`downloaded_regulations`目录。

4. 结束程序
按`Ctrl+C`可以终止程序运行。

### API模式

1. 启动API服务
```
python run_api.py [端口号]
```
默认端口为5000

2. API文档
访问 `http://localhost:5000/docs` 查看API文档和测试接口

3. 可用API接口
   - `GET /api/qrcode` - 获取微信登录二维码
   - `GET /api/cookies` - 获取所有可用cookie
   - `DELETE /api/cookies` - 删除指定cookie
   - `GET /api/status` - 获取当前状态

## 文件结构

- `run.py`: 主程序启动脚本
- `run_api.py`: API服务启动脚本
- `requirements.txt`: 依赖包列表
- `wechat_crawler/`: 爬虫包
  - `__init__.py`: 包初始化文件
  - `config.py`: 配置文件
  - `wechat_login.py`: 微信登录模块
  - `crawler.py`: 爬虫模块
  - `crawler_scheduler.py`: 爬虫调度模块
  - `main.py`: 主程序逻辑
  - `api.py`: FastAPI接口模块

## 多机部署

本项目支持多机部署，提高爬取效率：

1. 在中心服务器上部署Redis和API服务
```
python run_api.py
```

2. 在多个客户端机器上运行爬虫，连接到中心Redis服务器
   - 修改各客户端的`config.py`中的Redis连接信息
   - 运行爬虫程序
```
python run.py
```

3. 当cookie不足或失效时，通过API获取新的二维码，扫码登录补充cookie

## 注意事项

- 请合理设置爬取频率，避免对目标网站造成过大压力
- 确保使用合法途径获取数据，遵守相关法律法规
- 本程序仅供学习研究使用，请勿用于商业用途

## 许可证

MIT
