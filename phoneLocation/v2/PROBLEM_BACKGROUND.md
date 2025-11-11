# V2 设计背景 - 为什么需要重新设计

## 核心问题

V1 设计使用 Python 异常机制传递错误信息。这种设计在**本地调用**（同进程）场景下工作良好，但在**远程调用**（跨进程/跨网络）场景下存在根本性问题。

---

## 场景对比

### ✅ 场景1：本地调用（同进程内）

```
┌─────────────────────────────────────────────┐
│           单体应用进程                       │
│                                             │
│  ┌──────────┐       ┌──────────────────┐   │
│  │ 业务模块 │ ────> │ PhoneLocation    │   │
│  │          │       │ Service          │   │
│  └──────────┘       └──────────────────┘   │
│                                             │
│        直接调用，Python 异常传递             │
└─────────────────────────────────────────────┘
```

**V1 代码示例**：
```python
from phoneLocation.v1 import (
    PhoneLocationService,
    ClientError,
    RetryableError,
    RateLimitExceededError,
)

service = PhoneLocationService(api_key="key")

try:
    location = service.query("13800138000")
    print(f"查询成功: {location.city}")
except ClientError as e:
    # ✅ 可以捕获精确的异常类型
    print(f"客户端错误: {e.message}")
except RateLimitExceededError as e:
    # ✅ 可以访问异常属性
    print(f"被限流，等待 {e.retry_after} 秒")
except RetryableError as e:
    # ✅ 可以根据异常基类分类处理
    print(f"可重试错误: {e.message}")
```

**效果**：
- ✅ 异常机制工作完美
- ✅ 可以捕获精确的异常类型
- ✅ 可以访问异常属性（如 `retry_after`）
- ✅ IDE 支持良好
- ✅ 符合 Python 的 EAFP 哲学

---

### ❌ 场景2：远程调用（跨进程/跨网络）

```
┌─────────────┐                    ┌──────────────────┐
│  客户端模块 │   HTTP/gRPC 调用    │  服务端           │
│             │ ──────────────────> │                  │
│             │                     │ PhoneLocation    │
│             │   JSON/Protobuf     │ Service          │
│             │ <────────────────── │ (包装为 API)     │
└─────────────┘                    └──────────────────┘
```

#### 问题1：异常对象无法序列化传输

Python 异常对象无法通过网络传输（JSON、Protobuf 等）。

**服务端代码**：
```python
from phoneLocation.v1 import PhoneLocationService, RateLimitExceededError
from flask import Flask, jsonify

app = Flask(__name__)
service = PhoneLocationService(api_key="key")

@app.post("/api/query")
def query():
    try:
        location = service.query(request.json["phone"])
        return jsonify({"success": True, "data": location.__dict__}), 200
    except RateLimitExceededError as e:
        # ❌ 不能这样做：
        # return e  # 异常对象无法序列化为 JSON
        
        # ✅ 只能手动转换：
        return jsonify({
            "success": False,
            "error": e.message,
            "retry_after": e.retry_after  # 容易遗漏！
        }), 429
```

#### 问题2：需要为每种协议手动映射异常

**HTTP 服务端映射**：
```python
@app.post("/api/query")
def query():
    try:
        location = service.query(request.json["phone"])
        return jsonify({"success": True, "data": location.__dict__}), 200
    except InvalidPhoneNumberError as e:
        return jsonify({"error": e.message}), 400
    except InvalidParameterError as e:
        return jsonify({"error": e.message}), 400
    except AuthenticationError as e:
        return jsonify({"error": e.message}), 401
    except RateLimitExceededError as e:
        return jsonify({"error": e.message, "retry_after": e.retry_after}), 429
    except TimeoutError as e:
        return jsonify({"error": e.message}), 504
    except ServiceUnavailableError as e:
        return jsonify({"error": e.message}), 503
    # ... 需要手动映射每个异常！
```

**gRPC 服务端映射**：
```python
def Query(self, request, context):
    try:
        location = service.query(request.phone_number)
        return QueryResponse(success=True, location=location)
    except InvalidPhoneNumberError as e:
        context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
        context.set_details("Invalid phone number")
        return QueryResponse()
    except RateLimitExceededError as e:
        context.set_code(grpc.StatusCode.RESOURCE_EXHAUSTED)
        context.set_details(f"Rate limit exceeded")
        # ❌ retry_after 信息需要额外处理，容易遗漏
        return QueryResponse()
    # ... 又要写一遍映射逻辑！
```

**问题**：
- ❌ 每种协议（HTTP、gRPC、消息队列等）都要写一遍映射
- ❌ 维护成本高，容易出错
- ❌ 新增异常类型时，所有协议适配层都要修改

#### 问题3：客户端无法精确判断错误类型

**HTTP 客户端**：
```python
import requests

response = requests.post("http://service/api/query", 
                        json={"phone": "13800138000"})

if response.status_code == 200:
    data = response.json()["data"]
    print(f"成功: {data['city']}")
elif response.status_code == 400:
    # ❌ 400 可能是多种错误：
    #    - InvalidPhoneNumberError
    #    - InvalidParameterError
    #    - 其他参数错误
    # 无法精确区分！
    print("参数错误")
elif response.status_code == 429:
    # ❌ retry_after 在哪里？需要服务端记得传
    # ❌ 无法精确区分是哪种限流
    print("被限流")
else:
    print("失败")
```

**问题**：
- ❌ 只能拿到 HTTP 状态码，无法精确判断错误类型
- ❌ 同一个状态码可能对应多种错误
- ❌ 异常属性（如 `retry_after`）容易丢失

#### 问题4：信息丢失

在网络传输过程中，异常的很多信息会丢失：

| 信息 | V1 本地调用 | V1 远程调用 |
|-----|-----------|-----------|
| 异常类型 | ✅ 精确的类 | ❌ 只有 HTTP 状态码 |
| 错误消息 | ✅ `e.message` | ⚠️ 需要手动传 |
| 错误码 | ✅ `e.error_code` | ⚠️ 需要手动传 |
| 是否可重试 | ✅ `e.is_retryable()` | ❌ 客户端需要自己判断 |
| retry_after | ✅ `e.retry_after` | ❌ 容易遗漏 |
| 其他属性 | ✅ 完整 | ❌ 容易丢失 |

---

## 问题根源

**Python 异常机制的局限性**：

1. **设计目标不同**
   - 异常机制设计用于**同进程内**的错误传播
   - 不是为**跨进程/跨网络**设计的

2. **序列化困难**
   - Python 对象不能直接序列化为 JSON/Protobuf
   - 异常类的继承关系无法在网络传输中保留

3. **协议无关性差**
   - 异常是 Python 特有的概念
   - HTTP、gRPC 等协议有自己的错误表示方式
   - 需要手动映射，维护成本高

---

## V2 设计目标

基于上述问题，V2 需要满足：

### 1. 统一性
- ✅ 本地调用和远程调用使用**相同的 API**
- ✅ 不需要为不同协议写不同的适配层

### 2. 完整性
- ✅ 错误信息**不会丢失**（retry_after 等属性）
- ✅ 错误类型可以**精确传递**

### 3. 可序列化
- ✅ 天然支持 JSON、Protobuf 等序列化格式
- ✅ 无需手动转换

### 4. 协议无关
- ✅ 错误码设计不依赖特定协议（不绑定 HTTP 状态码）
- ✅ 易于映射到各种协议

### 5. 通用性
- ✅ 错误码设计不绑定具体业务（phone location）
- ✅ 可以复用到其他服务

---

## V2 设计方向

**采用：错误枚举 + 结果对象模式**

核心思想：
- **不抛异常**，而是返回统一的结果对象
- 使用**错误枚举**表示错误类型（包含码和描述）
- 错误码设计**通用**，不绑定协议和具体实现

这样设计的好处：
- ✅ 本地调用和远程调用使用相同的 API
- ✅ 所有错误信息完整保留
- ✅ 易于序列化（天然支持 JSON、Protobuf）
- ✅ 客户端可以精确判断错误类型
- ✅ 不需要为每种协议写映射逻辑
- ✅ 易于测试（不需要 try-except）

---

## 下一步

V2 将实现：
1. `error_types.py` - 通用的错误枚举定义（包含码和描述）
2. `models.py` - QueryResult 结果对象
3. `service.py` - PhoneLocationService 实现
4. `test_service.py` - 完整的测试用例
5. `API_REFERENCE.md` - API 文档

