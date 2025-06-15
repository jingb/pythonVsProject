from flask import Flask
from flask_restx import Api, Resource
import asyncio
import requests


app = Flask(__name__)
api = Api(app, title='Hello World API', description='A simple API example')

@api.route('/hello')
class HelloWorld(Resource):
    def get(self):
        from time import sleep
        sleep(3)
        return {'message': 'hello world'}
    
async def func1():
    from asyncio import sleep
    await sleep(1)
    return {'message': 'async fun1'}

async def func2():
    from asyncio import sleep
    await sleep(2)
    return {'message': 'async fun2'}

async def func3():
    from asyncio import sleep
    await sleep(3)
    return {'message': 'async fun3'}

@api.route('/hello/async')
class HelloWorldAsync(Resource):
    def get(self) -> dict[str, str]:
        result = asyncio.run(concurrentRun())
        return {
            f'func{i+1}': res['message'] 
            for i, res in enumerate(result)
        }
    
@api.route('/remote')
class Remote(Resource):
    def get(self) -> dict[str, str]:
        response = requests.get('http://localhost:8765/', params={'sleepSeconds': '3'})
        return {
            "responseBody": response.text
        }
    

async def concurrentRun():
    tasks = [asyncio.create_task(func()) for func in [func1, func2, func3]] 
    return await asyncio.gather(*tasks)
    


