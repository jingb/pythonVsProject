# Result 类设计说明

## 设计目标

创建一个**通用的返回值类**，满足：
1. **通用性**：不绑定任何具体业务
2. **类型安全**：使用泛型支持任意数据类型
3. **完整性**：包含成功和失败的所有必要信息
4. **易用性**：提供便捷的 API
5. **可序列化**：支持 JSON 等格式

---

## 核心字段

```python
@dataclass
class Result(Generic[T]):
    # 必需字段
    success: bool                        # 是否成功
    
    # 成功时有值
    data: Optional[T] = None             # 返回的数据（泛型）
    
    # 失败时有值
    error_code: Optional[ErrorCode] = None      # 错误码
    error_message: Optional[str] = None         # 详细错误信息
    
    # 扩展字段
    metadata: Dict[str, Any] = field(default_factory=dict)  # 扩展字段（可包含 retry_after 等）
```

---

## 字段说明

### 1. success: bool ✅
**用途**：判断调用是否成功

**为什么需要**：
- 调用方第一眼就能知道成功还是失败
- 支持布尔判断：`if result:` 等价于 `if result.success:`

### 2. data: Optional[T] 📦
**用途**：存储成功时的返回数据

**特点**：
- 使用泛型 `T`，支持任意数据类型
- 只在 `success=True` 时有值

**示例**：
```python
# 返回简单对象
Result[PhoneLocation].success(data=PhoneLocation(...))

# 返回字典
Result[dict].success(data={"city": "北京"})

# 返回列表
Result[list].success(data=[1, 2, 3])
```

### 3. error_code: Optional[ErrorCode] 🔴
**用途**：标识错误类型

**特点**：
- 使用标准化的 ErrorCode 枚举
- 只在 `success=False` 时有值
- 包含错误码、描述、是否可重试等信息

### 4. error_message: Optional[str] 💬
**用途**：提供详细的错误信息

**为什么需要**：
- ErrorCode 的描述是通用的（如"参数校验失败"）
- error_message 可以提供具体信息（如"手机号格式不正确: 138001380"）

**示例**：
```python
Result.error(
    error_code=ErrorCode.VALIDATION_FAILED,  # 通用描述："参数校验失败"
    error_message="手机号格式不正确: 138001380"  # 具体信息
)
```

### 5. metadata: Dict[str, Any] 🏷️
**用途**：扩展字段，存放额外信息

**常见用途**：
- `request_id`：请求追踪 ID
- `timestamp`：请求时间戳
- `server_time`：服务器时间
- `retry_after`：建议的等待时间（秒），用于限流等场景
- `version`：API 版本
- `region`：服务区域
- 任何其他业务需要的信息

**示例**：
```python
Result.success(
    data=location,
    metadata={
        "request_id": "req_123456",
        "timestamp": 1699234567,
        "server_time": "2024-11-06T10:30:00Z"
    }
)
```

---

## 核心方法

### 1. success() - 工厂方法 ✅
```python
@classmethod
def success(
    cls,
    data: T,
    metadata: Optional[Dict[str, Any]] = None
) -> 'Result[T]':
    """创建成功的结果"""
```

**使用示例**：
```python
# 简单使用
result = Result.success(data={"city": "北京"})

# 带元数据
result = Result.success(
    data={"city": "北京"},
    metadata={"request_id": "req_123"}
)
```

### 2. error() - 工厂方法 ❌
```python
@classmethod
def error(
    cls,
    error_code: ErrorCode,
    error_message: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> 'Result[T]':
    """创建失败的结果"""
```

**使用示例**：
```python
# 使用默认描述
result = Result.error(error_code=ErrorCode.VALIDATION_FAILED)
# error_message 自动为："参数校验失败"

# 提供详细描述
result = Result.error(
    error_code=ErrorCode.VALIDATION_FAILED,
    error_message="手机号格式不正确: 138001380"
)

# 限流场景（retry_after 放在 metadata 中）
result = Result.error(
    error_code=ErrorCode.RATE_LIMITED,
    error_message="请求过于频繁",
    metadata={"retry_after": 60}
)
```

### 3. is_retryable() - 判断是否可重试
```python
def is_retryable(self) -> bool:
    """判断该错误是否可重试"""
```

**使用示例**：
```python
result = service.query("13800138000")

if not result.success:
    if result.is_retryable():
        print("可以重试")
        # 从 metadata 中获取 retry_after
        retry_after = result.metadata.get("retry_after", 5)
        time.sleep(retry_after)
        # 重试
    else:
        print("不应重试，检查参数")
```

### 4. to_dict() - 序列化
```python
def to_dict(self) -> Dict[str, Any]:
    """转换为字典（用于序列化）"""
```

**使用示例**：
```python
# 成功的结果
result = Result.success(data={"city": "北京"})
print(result.to_dict())
# {
#     "success": True,
#     "data": {"city": "北京"}
# }

# 失败的结果
result = Result.error(
    error_code=ErrorCode.RATE_LIMITED,
    error_message="请求过于频繁",
    metadata={"retry_after": 60}
)
print(result.to_dict())
# {
#     "success": False,
#     "error_code": "RATE_LIMITED",
#     "error_message": "请求过于频繁",
#     "retryable": True,
#     "metadata": {"retry_after": 60}
# }
```

### 5. to_http_status() - 映射到 HTTP 状态码
```python
def to_http_status(self) -> int:
    """转换为 HTTP 状态码（可选，用于 HTTP 接口）"""
```

**使用示例**：
```python
@app.post("/api/query")
def query_api():
    result = service.query(request.json["phone"])
    return jsonify(result.to_dict()), result.to_http_status()
```

---

## 使用场景

### 场景1：简单查询
```python
def query(phone_number: str) -> Result[PhoneLocation]:
    if not phone_number:
        return Result.error(
            error_code=ErrorCode.MISSING_REQUIRED,
            error_message="phone_number 参数为空"
        )
    
    location = self._do_query(phone_number)
    return Result.success(data=location)

# 调用方
result = service.query("13800138000")
if result.success:
    print(f"城市: {result.data.city}")
else:
    print(f"错误: {result.error_message}")
```

### 场景2：带重试逻辑
```python
result = service.query("13800138000")

if not result.success:
    if result.error_code == ErrorCode.RATE_LIMITED:
        retry_after = result.metadata.get("retry_after", 60)
        print(f"被限流，等待 {retry_after} 秒后重试")
        time.sleep(retry_after)
        result = service.query("13800138000")  # 重试
    elif result.is_retryable():
        print("临时错误，可以重试")
        time.sleep(5)
        result = service.query("13800138000")  # 重试
    else:
        print(f"永久错误: {result.error_message}")
```

### 场景3：HTTP 接口
```python
from flask import Flask, jsonify, request

app = Flask(__name__)

@app.post("/api/query")
def query_api():
    phone = request.json.get("phone")
    
    # 调用服务
    result = service.query(phone)
    
    # 直接返回，无需手动映射
    return jsonify(result.to_dict()), result.to_http_status()

# 客户端收到的 JSON：
# 成功时：
# {
#     "success": true,
#     "data": {"city": "北京", "province": "北京市", ...}
# }
#
# 失败时：
# {
#     "success": false,
#     "error_code": "VALIDATION_FAILED",
#     "error_message": "手机号格式不正确",
#     "retryable": false
# }
```

### 场景4：gRPC 接口
```python
def Query(self, request, context):
    result = service.query(request.phone_number)
    
    if result.success:
        return QueryResponse(
            success=True,
            location=result.data,
        )
    else:
        return QueryResponse(
            success=False,
            error_code=result.error_code.get_code(),
            error_message=result.error_message,
            retryable=result.is_retryable(),
            retry_after=result.metadata.get("retry_after", 0),
        )
```

---

## 设计考虑

### ✅ 已考虑的问题

#### 1. 类型安全
- 使用泛型 `Generic[T]`，支持任意数据类型
- IDE 可以自动推导类型

```python
result: Result[PhoneLocation] = service.query("13800138000")
if result.success:
    # IDE 知道 result.data 的类型是 PhoneLocation
    print(result.data.city)
```

#### 2. 避免字段冲突
- 成功时只有 `data`
- 失败时只有 `error_code`、`error_message`、`retry_after`
- 不会出现 `success=True` 但有 `error_code` 的情况

#### 3. 默认值合理
- `error_message` 可以不提供，会自动使用 `error_code` 的默认描述
- `retry_after` 可以不提供（`None`），调用方自己决定等待时间
- `metadata` 默认为空字典

#### 4. 易于使用
- 工厂方法 `success()` 和 `error()` 语义清晰
- 支持布尔判断：`if result:` 等价于 `if result.success:`
- 提供便捷方法：`is_retryable()`, `to_dict()`, `to_http_status()`

#### 5. 可序列化
- `to_dict()` 方法可以直接序列化为 JSON
- 只包含必要的字段，不冗余

#### 6. 协议无关
- `Result` 本身不依赖任何协议
- 提供可选的映射方法（`to_http_status()`）

---

## 可能的扩展

### 1. 添加 warning 字段？
```python
warnings: List[str] = field(default_factory=list)  # 警告信息
```

**使用场景**：
- 成功了，但有些字段降级了
- 成功了，但用了备用方案

**是否需要**：可以用 `metadata` 替代

### 2. 添加 request_id 字段？
```python
request_id: Optional[str] = None  # 请求追踪 ID
```

**是否需要**：可以用 `metadata` 替代，更灵活

### 3. 添加 timestamp 字段？
```python
timestamp: float = field(default_factory=time.time)  # 时间戳
```

**是否需要**：可以用 `metadata` 替代

### 4. 添加分页字段？
```python
pagination: Optional[Pagination] = None  # 分页信息
```

**是否需要**：这是业务特定的，不应该在通用类中

---

## 与 V1 的对比

| 特性 | V1（异常模式） | V2（Result 模式） |
|-----|-------------|-----------------|
| 表示成功 | 返回数据 | `Result.success(data=...)` |
| 表示失败 | 抛异常 | `Result.error(error_code=...)` |
| 错误信息 | 异常对象 | `error_code` + `error_message` |
| 是否可重试 | `exception.is_retryable()` | `result.is_retryable()` |
| 限流等待时间 | `exception.retry_after` | `result.metadata["retry_after"]` |
| 序列化 | ❌ 困难 | ✅ `result.to_dict()` |
| 远程调用 | ❌ 需要手动映射 | ✅ 开箱即用 |

---

## 总结

`Result` 类的设计：
- ✅ **通用**：不绑定业务，可用于任何服务
- ✅ **类型安全**：泛型支持，IDE 友好
- ✅ **完整**：包含所有必要信息（错误码、描述等），扩展信息通过 metadata 存放
- ✅ **易用**：工厂方法、布尔判断、便捷方法
- ✅ **可序列化**：支持 JSON 等格式
- ✅ **可扩展**：`metadata` 字段支持任意扩展（retry_after、request_id 等）

这个设计适用于：
- 本地调用（同进程）
- 远程调用（HTTP、gRPC、消息队列等）
- 任何需要统一返回值的场景

