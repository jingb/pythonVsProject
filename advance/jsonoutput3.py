import os
import json
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import (
    JsonOutputParser,
)
from langchain.prompts import ChatPromptTemplate
from langchain.schema import StrOutputParser
from flask import Flask, Response, request
from flask_cors import CORS
from typing import Generator, Dict, Any, Optional

# 请确保您已将 API Key 存储在环境变量 ARK_API_KEY 中
os.environ["ARK_API_KEY"] = ""
# 从环境变量中获取您的 API Key

# 创建 Flask 应用
app = Flask(__name__)
CORS(app)  # 允许跨域请求

# 请求数据
data = {
    "model": "doubao-1-5-pro-32k-250115",
    "messages": [
        {"role": "system", "content": "你是一个JSON生成助手。请严格按照指定的JSON格式输出内容，确保输出的JSON格式正确且可以被解析。"},
        {"role": "user", "content": "请生成一个包含title和summary字段的JSON字符串。title字段包含一个标题内容，summary字段包含一个摘要内容（可能很长）。请严格按照以下格式输出，不要添加任何额外的文字说明：\n\n{\n\t\"title\":\"标题的内容\",\n\t\"summary\":\"摘要的内容，可能非常长……\"\n}"},
    ],
    "stream": True
}


class IncrementalProcessor:
    """
    增量处理器 - 基于 JSON Patch 的简单实现
    负责处理 JsonOutputParser(diff=True) 返回的 patch 数据，
    提取增量部分并返回给客户端
    """
    
    def __init__(self):
        # 维护当前状态
        self.current_title = ""
        self.current_summary = ""
    
    def process_patch(self, chunk) -> Optional[Dict[str, str]]:
        """
        处理 JSON Patch 数据，提取增量部分
        
        Args:
            chunk: JSON Patch 格式的数据块
                示例: [{'op': 'replace', 'path': '/title', 'value': '科技发展新趋势'}]
        
        Returns:
            Optional[Dict[str, str]]: 增量数据，格式如 {"title": "趋势"} 或 {"summary": "时代"}
        """
        
        for patch in chunk:
            op = patch['op']
            path = patch['path']
            new_value = patch['value']
            
            if path == '/title':
                return self._process_title_patch(op, new_value)
            elif path == '/summary':
                return self._process_summary_patch(op, new_value)
        
        return None
    
    def _process_title_patch(self, op: str, new_value: str) -> Dict[str, str]:
        """处理 title 字段的 patch"""
        if op == 'add':
            # 新增字段，返回完整值
            self.current_title = new_value
            return {"title": new_value}
        elif op == 'replace':
            # 替换操作，计算增量
            old_value = self.current_title
            increment = self._extract_increment(old_value, new_value)
            self.current_title = new_value
            return {"title": increment}
        return {}
    
    def _process_summary_patch(self, op: str, new_value: str) -> Dict[str, str]:
        """处理 summary 字段的 patch"""
        if op == 'add':
            # 新增字段，返回完整值
            self.current_summary = new_value
            return {"summary": new_value}
        elif op == 'replace':
            # 替换操作，计算增量
            old_value = self.current_summary
            increment = self._extract_increment(old_value, new_value)
            self.current_summary = new_value
            return {"summary": increment}
        return {}
    
    def _extract_increment(self, old_value: str, new_value: str) -> str:
        """
        提取增量部分
        
        Args:
            old_value: 之前的值
            new_value: 新的值
            
        Returns:
            str: 增量部分
            
        示例：
        old_value = "科技发展新"
        new_value = "科技发展新趋势"
        返回: "趋势"
        """
        if old_value == "":
            # 如果之前是空字符串，返回完整新值
            return new_value
        
        if new_value.startswith(old_value):
            # 新值以旧值开头，返回后缀部分
            return new_value[len(old_value):]
        else:
            # 内容不匹配，返回完整新值（异常情况）
            return new_value


def getByLangchain(prompt: dict) -> None:
    """
    获取大模型流式响应（控制台输出版本）
    
    Args:
        prompt: 包含模型配置和消息的字典
    """
    # 创建 JSON 输出解析器
    json_parser = JsonOutputParser(diff=False)
    
    # 创建 LLM
    llm = ChatOpenAI(
        openai_api_base="https://ark.cn-beijing.volces.com/api/v3",
        openai_api_key=os.environ.get("ARK_API_KEY"),
        model_name=prompt["model"],
        temperature=0,  # 设置为0以获得更稳定的输出
    )
    
    # 创建提示模板，包含 JSON 解析器的格式说明
    prompt_template = ChatPromptTemplate.from_messages([
        ("system", "你是一个JSON生成助手。请严格按照指定的JSON格式输出内容，确保输出的JSON格式正确且可以被解析。"),
        ("user", "请生成一个包含title和summary字段的JSON字符串。title字段包含一个标题内容，summary字段包含一个摘要内容（可能很长）。请严格按照以下格式输出，不要添加任何额外的文字说明：\n\n{{\n\t\"title\":\"标题的内容\",\n\t\"summary\":\"摘要的内容，可能非常长……\"\n}}")
    ])
    
    # 创建链
    chain = prompt_template | llm | json_parser
    
    # 使用流式输出
    for chunk in chain.stream({}):
        print(chunk, flush=True)
    print("\n=== 流式输出完成 ===")


def getByLangchainGenerator(prompt: dict) -> Generator[list, None, None]:
    """
    生成器函数，用于SSE流式返回
    
    Args:
        prompt: 包含模型配置和消息的字典
        
    Yields:
        list: JSON Patch 格式的数据块
              示例: [{'op': 'replace', 'path': '/title', 'value': '科技发展新趋势'}]
    """
    # 创建 JSON 输出解析器，启用 diff 模式
    json_parser = JsonOutputParser(diff=True)
    
    # 创建 LLM
    llm = ChatOpenAI(
        openai_api_base="https://ark.cn-beijing.volces.com/api/v3",
        openai_api_key=os.environ.get("ARK_API_KEY"),
        model_name=prompt["model"],
        temperature=0,  # 设置为0以获得更稳定的输出
    )
    
    # 创建提示模板，包含 JSON 解析器的格式说明
    prompt_template = ChatPromptTemplate.from_messages([
        ("system", "你是一个JSON生成助手。请严格按照指定的JSON格式输出内容，确保输出的JSON格式正确且可以被解析。"),
        ("user", "请生成一个包含title和summary字段的JSON字符串。title字段包含一个标题内容，summary字段包含一个摘要内容（可能很长）。请严格按照以下格式输出，不要添加任何额外的文字说明：\n\n{{\n\t\"title\":\"标题的内容\",\n\t\"summary\":\"摘要的内容，可能非常长……\"\n}}")
    ])
    
    # 创建链
    chain = prompt_template | llm | json_parser
    
    # 使用流式输出并yield每个chunk
    for chunk in chain.stream({}):
        yield chunk


@app.route('/helloworld', methods=['GET'])
def helloworld():
    """SSE接口，流式返回大模型响应"""
    def generate():
        # 创建增量处理器
        processor = IncrementalProcessor()
        
        try:
            # 设置SSE响应头
            yield "data: {\"status\": \"start\", \"message\": \"开始生成响应...\"}\n\n"
            
            # 调用生成器函数获取流式响应
            for chunk in getByLangchainGenerator(data):
                # 处理 patch 数据，提取增量
                increment = processor.process_patch(chunk)
                
                if increment:
                    # 将增量数据转换为JSON字符串并发送
                    chunk_data = {
                        "status": "chunk",
                        "data": increment
                    }
                    yield f"data: {json.dumps(chunk_data, ensure_ascii=False)}\n\n"
            
            # 发送结束信号
            yield "data: {\"status\": \"end\", \"message\": \"响应生成完成\"}\n\n"
            
        except Exception as e:
            # 发送错误信息
            error_data = {
                "status": "error",
                "message": str(e)
            }
            yield f"data: {json.dumps(error_data, ensure_ascii=False)}\n\n"
    
    return Response(
        generate(),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Cache-Control'
        }
    )


@app.route('/health', methods=['GET'])
def health():
    """健康检查接口"""
    return {"status": "ok", "message": "Server is running"}


if __name__ == "__main__":
    # 测试新的方法
    # print("=== 使用 JsonOutputParser 的方法 ===")
    #getByLangchain(data)
    
    # 启动Flask服务器
    print("\n=== 启动HTTP服务器 ===")
    print("访问 http://localhost:5001/helloworld 获取SSE流式响应")
    print("访问 http://localhost:5001/health 进行健康检查")
    app.run(host='0.0.0.0', port=5001, debug=True)

