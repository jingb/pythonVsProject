# SSE 增量流式响应服务器

这个项目提供了一个基于 Flask 的 HTTP 服务器，使用 Server-Sent Events (SSE) 技术来流式返回大模型的响应，并实现了增量内容推送功能。

## 功能特性

- 🚀 **SSE 流式响应**: 使用 Server-Sent Events 技术实时推送大模型响应
- 🔄 **增量内容推送**: 将大模型的增量内容实时返回给客户端，实现打字机效果
- 📝 **字段分离显示**: title 和 summary 字段分别显示，便于用户阅读
- 🌐 **跨域支持**: 支持跨域请求
- 🛡️ **错误处理**: 完善的错误处理和状态反馈
- 📊 **健康检查**: 提供健康检查接口

## 技术实现

### 增量处理机制

服务器使用 `JsonOutputParser(diff=True)` 获取 JSON Patch 格式的数据流，然后通过 `IncrementalProcessor` 类处理增量内容：

JsonOutputParser diff参数为true，模型大概会这么返回数据，jsonpatch的模式已经告诉我们变化的是什么字段，前后两笔报文很容易算出增量的是什么字段的什么内容

[{'op': 'replace', 'path': '', 'value': {}}]
[{'op': 'add', 'path': '/title', 'value': ''}]
[{'op': 'replace', 'path': '/title', 'value': '科技'}]
[{'op': 'replace', 'path': '/title', 'value': '科技发展'}]
[{'op': 'replace', 'path': '/title', 'value': '科技发展新'}]
[{'op': 'replace', 'path': '/title', 'value': '科技发展新趋势'}]
[{'op': 'add', 'path': '/summary', 'value': ''}]
[{'op': 'replace', 'path': '/summary', 'value': '随着'}]
[{'op': 'replace', 'path': '/summary', 'value': '随着时代'}]

-> 



```python
# 输入数据格式（JSON Patch）
[{'op': 'replace', 'path': '/title', 'value': '科技发展新趋势'}]

# 输出数据格式（增量内容）
{"title": "趋势"}
```

### 增量计算算法

1. **状态管理**: 维护每个字段的当前值
2. **增量提取**: 比较新旧值，提取增量部分
3. **实时推送**: 将增量内容通过 SSE 推送给客户端

## 安装依赖

```bash
pip install -r requirements.txt
```

## 运行服务器

```bash
python jsonoutput3.py
```

服务器将在 `http://localhost:5001` 启动。

## API 接口

### 1. SSE 增量流式响应接口

**URL**: `GET /helloworld`

**描述**: 获取大模型的增量流式响应，使用 SSE 技术实时推送增量内容

**响应格式**: Server-Sent Events

**示例响应**:
```
data: {"status": "start", "message": "开始生成响应..."}

data: {"status": "chunk", "data": {"title": ""}}
data: {"status": "chunk", "data": {"title": "科技"}}
data: {"status": "chunk", "data": {"title": "发展"}}
data: {"status": "chunk", "data": {"title": "新"}}
data: {"status": "chunk", "data": {"title": "趋势"}}
data: {"status": "chunk", "data": {"summary": ""}}
data: {"status": "chunk", "data": {"summary": "随着"}}
data: {"status": "chunk", "data": {"summary": "时代"}}

data: {"status": "end", "message": "响应生成完成"}
```

### 2. 健康检查接口

**URL**: `GET /health`

**描述**: 检查服务器运行状态

**响应格式**: JSON

**示例响应**:
```json
{
  "status": "ok",
  "message": "Server is running"
}
```

## 客户端使用示例

### JavaScript 客户端

```javascript
// 创建 EventSource 连接
const eventSource = new EventSource('http://localhost:5001/helloworld');

// 维护内容状态
let titleContent = "";
let summaryContent = "";

// 监听消息
eventSource.onmessage = function(event) {
    const data = JSON.parse(event.data);
    
    switch(data.status) {
        case 'start':
            console.log('开始生成响应...');
            break;
        case 'chunk':
            // 处理增量数据
            if (data.data.title !== undefined) {
                titleContent += data.data.title;
                console.log('标题更新:', titleContent);
            }
            if (data.data.summary !== undefined) {
                summaryContent += data.data.summary;
                console.log('摘要更新:', summaryContent);
            }
            break;
        case 'end':
            console.log('响应生成完成');
            eventSource.close();
            break;
        case 'error':
            console.error('发生错误:', data.message);
            break;
    }
};

// 监听连接打开
eventSource.onopen = function(event) {
    console.log('SSE 连接已建立');
};

// 监听错误
eventSource.onerror = function(event) {
    console.error('SSE 连接错误:', event);
    eventSource.close();
};
```

### 使用测试客户端

项目包含了一个 HTML 测试客户端 (`test_sse_client.html`)，你可以：

1. 在浏览器中打开 `test_sse_client.html`
2. 点击"开始接收流式响应"按钮
3. 观察 title 和 summary 字段的增量更新效果

## 数据格式说明

### 开始信号
```json
{
  "status": "start",
  "message": "开始生成响应..."
}
```

### 增量数据块
```json
{
  "status": "chunk",
  "data": {
    "title": "增量标题内容"
  }
}
```

或者：

```json
{
  "status": "chunk",
  "data": {
    "summary": "增量摘要内容"
  }
}
```

### 结束信号
```json
{
  "status": "end",
  "message": "响应生成完成"
}
```

### 错误信号
```json
{
  "status": "error",
  "message": "错误描述"
}
```

## 核心类说明

### IncrementalProcessor

负责处理 JSON Patch 数据并提取增量内容：

```python
class IncrementalProcessor:
    def __init__(self):
        self.current_title = ""
        self.current_summary = ""
    
    def process_patch(self, chunk):
        # 处理 JSON Patch 数据
        # 返回增量内容
```

### 增量计算算法

```python
def _extract_increment(self, old_value, new_value):
    if old_value == "":
        return new_value
    
    if new_value.startswith(old_value):
        return new_value[len(old_value):]
    else:
        return new_value
```

## 技术架构

- **后端框架**: Flask
- **SSE 实现**: Flask Response with `text/event-stream` mimetype
- **大模型集成**: LangChain + OpenAI API
- **增量处理**: 基于 JSON Patch 的增量计算
- **流式处理**: 使用 Python 生成器函数实现流式数据推送
- **跨域支持**: Flask-CORS

## 注意事项

1. 确保环境变量 `ARK_API_KEY` 已正确设置
2. 服务器默认监听所有网络接口 (`0.0.0.0:5001`)
3. 在生产环境中建议使用 Gunicorn 等 WSGI 服务器
4. SSE 连接会保持开启状态直到响应完成或发生错误
5. 增量处理基于 JSON Patch 格式，确保 LangChain 配置正确

## 故障排除

### 常见问题

1. **连接被拒绝**: 检查服务器是否正在运行
2. **跨域错误**: 确保 Flask-CORS 已正确配置
3. **API 密钥错误**: 检查环境变量设置
4. **响应中断**: 检查网络连接和服务器日志
5. **增量计算错误**: 检查 JSON Patch 数据格式

### 调试模式

服务器默认运行在调试模式下，会显示详细的错误信息。在生产环境中请关闭调试模式。

### 性能优化

- 增量处理减少了网络传输量
- 客户端可以实时显示内容，提升用户体验
- 支持多客户端并发连接 