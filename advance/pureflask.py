from flask import Flask
from flask_restx import Api, Resource
import requests
import concurrent.futures
import time
import logging


logger = logging.getLogger()

app = Flask(__name__)
api = Api(app, title='Hello World API', description='A simple API example')

@api.route('/sleep')
class Sleep(Resource):
    def get(self) -> dict[str, any]:
        start = time.time()
        time.sleep(3)
        return {
            "costTime": time.time() - start
        }

@api.route('/remote')
class Remote(Resource):
    def get(self) -> dict[str, str]:
        response = requests.get('http://localhost:8765/', params={'sleepSeconds': '3'})
        return {
            "responseBody": response.text
        }
    
@api.route('/memTidy')
class MemTidy(Resource):
    def get(self) -> dict[str, str]:
        url = "http://localhost:8765/"
        # 并行执行前两次请求
        with concurrent.futures.ThreadPoolExecutor() as executor:
            # 提交两个并行任务
            future1 = executor.submit(make_request, url, {"retContent": "first", 
                                                          "sleepSeconds": "2"})
            future2 = executor.submit(make_request, url, {"retContent": "second", 
                                                          "sleepSeconds": "3"})
            # 等待两个并行任务完成
            concurrent.futures.wait([future1, future2])
            # 获取结果
            result1 = future1.result()
            result2 = future2.result()
            
            logger.info("Parallel request results:")
            print(f" - {result1}")
            print(f" - {result2}")
            # 第三次请求（顺序执行）
            print("\n第三次请求，请求参数是请求1和请求2的响应结果")
            result3 = make_request(url, {"retContent": result1 + result2, 
                                         "sleepSeconds": "1"})
            print(f"Sequential request result: {result3}")
        return {"ret": result3}

def make_request(url, params=None):
    start = time.time()
    logger.info("开始请求远端")
    response = requests.get(url, params=params)
    duration = time.time() - start
    logger.info("耗时 {}", duration)
    return f"Response: {response.text} (took {duration:.2f}s)"


# python3 -m gunicorn --workers 2 --worker-class gevent --bind '0.0.0.0:51080' advance.pureflask:app run