# 错误码设计 - 通用、协议无关

## 设计原则

1. **通用性**：不绑定具体业务（phone location）
2. **协议无关**：不使用 HTTP 状态码（4xx、5xx）
3. **语义化**：使用清晰的字符串常量
4. **可扩展**：易于添加新的错误类型
5. **结构化**：包含错误码和描述

---

## 错误枚举设计

### 错误分类

```
错误类型
├── 输入错误（调用方问题）
│   ├── INVALID_INPUT          # 输入参数不合法
│   ├── VALIDATION_FAILED      # 参数校验失败
│   └── MISSING_REQUIRED       # 缺少必需参数
│
├── 认证授权错误
│   ├── AUTH_FAILED            # 认证失败
│   ├── PERMISSION_DENIED      # 权限不足
│   └── CREDENTIALS_INVALID    # 凭证无效
│
├── 资源限制错误（可重试）
│   ├── RATE_LIMITED           # 请求频率超限
│   ├── QUOTA_EXCEEDED         # 配额耗尽
│   └── RESOURCE_EXHAUSTED     # 资源耗尽
│
├── 超时错误（可重试）
│   ├── TIMEOUT                # 请求超时
│   └── DEADLINE_EXCEEDED      # 截止时间已过
│
└── 服务状态错误（可重试）
    ├── SERVICE_UNAVAILABLE    # 服务不可用
    ├── SERVICE_DEGRADED       # 服务降级
    └── MAINTENANCE            # 维护中
```

---

## 错误枚举实现

```python
from enum import Enum
from dataclasses import dataclass

@dataclass(frozen=True)
class ErrorType:
    """错误类型（包含码和描述）"""
    code: str         # 错误码（字符串常量）
    message: str      # 错误描述
    retryable: bool   # 是否可重试

class ErrorCode(Enum):
    """通用错误码枚举"""
    
    # ==================== 输入错误（调用方问题，不可重试）====================
    
    INVALID_INPUT = ErrorType(
        code="INVALID_INPUT",
        message="输入参数不合法",
        retryable=False
    )
    
    # ==================== 认证授权错误（不可重试）====================
    
    AUTH_FAILED = ErrorType(
        code="AUTH_FAILED",
        message="认证失败",
        retryable=False
    )
    
    PERMISSION_DENIED = ErrorType(
        code="PERMISSION_DENIED",
        message="权限不足",
        retryable=False
    )
    
    CREDENTIALS_INVALID = ErrorType(
        code="CREDENTIALS_INVALID",
        message="凭证无效",
        retryable=False
    )
    
    # ==================== 资源限制错误（可重试）====================
    
    RATE_LIMITED = ErrorType(
        code="RATE_LIMITED",
        message="请求频率超限",
        retryable=True
    )
    
    QUOTA_EXCEEDED = ErrorType(
        code="QUOTA_EXCEEDED",
        message="配额耗尽",
        retryable=True
    )
    
    # ==================== 超时错误（可重试）====================
    
    TIMEOUT = ErrorType(
        code="TIMEOUT",
        message="请求超时",
        retryable=True
    )
    
    # ==================== 服务状态错误（可重试）====================
    
    SERVICE_UNAVAILABLE = ErrorType(
        code="SERVICE_UNAVAILABLE",
        message="服务不可用",
        retryable=True
    )
    
    SERVICE_DEGRADED = ErrorType(
        code="SERVICE_DEGRADED",
        message="服务降级，既效果会差些或者部分字段缺失，调用端自己识别结果是否可用",
        retryable=True
    )
    
```

---

## 使用示例

### 在 Service 中使用

```python
def query(self, phone_number: str) -> QueryResult:
    # 参数校验
    if not phone_number:
        return QueryResult.error(
            error_code=ErrorCode.MISSING_REQUIRED,
            error_message="phone_number 参数为空"
        )
    
    if not self._validate_phone_format(phone_number):
        return QueryResult.error(
            error_code=ErrorCode.VALIDATION_FAILED,
            error_message=f"手机号格式不正确: {phone_number}"
        )
    
    # 认证检查
    if not self._check_auth():
        return QueryResult.error(
            error_code=ErrorCode.AUTH_FAILED,
            error_message="API密钥无效"
        )
    
    # 限流检查
    if self._is_rate_limited():
        return QueryResult.error(
            error_code=ErrorCode.RATE_LIMITED,
            error_message="请求过于频繁",
            retry_after=60
        )
    
    # 调用远程 API
    try:
        location = self._call_remote_api(phone_number)
        return QueryResult.success(data=location)
    except RemoteTimeoutError:
        return QueryResult.error(
            error_code=ErrorCode.TIMEOUT,
            error_message="远程API调用超时"
        )
    except RemoteServiceError:
        return QueryResult.error(
            error_code=ErrorCode.SERVICE_UNAVAILABLE,
            error_message="远程服务暂时不可用"
        )
```

### 客户端使用

```python
result = service.query("13800138000")

if result.success:
    print(f"查询成功: {result.data.city}")
else:
    # 方式1：精确判断错误类型
    if result.error_code == ErrorCode.RATE_LIMITED:
        print(f"被限流，{result.retry_after} 秒后重试")
        time.sleep(result.retry_after)
        # 重试
    elif result.error_code == ErrorCode.VALIDATION_FAILED:
        print(f"参数错误: {result.error_message}")
        # 修正参数
    
    # 方式2：根据 retryable 判断
    if result.error_code.value.retryable:
        print("这是临时错误，可以重试")
    else:
        print("这是永久错误，不应重试")
    
    # 方式3：获取错误码字符串（用于日志、监控等）
    error_code_str = result.error_code.value.code
    print(f"错误码: {error_code_str}")
```

### 映射到 HTTP 状态码（可选）

如果需要暴露为 HTTP API，可以提供映射函数：

```python
def error_code_to_http_status(error_code: ErrorCode) -> int:
    """将错误码映射到 HTTP 状态码（仅用于 HTTP 接口）"""
    mapping = {
        # 输入错误 -> 400
        ErrorCode.INVALID_INPUT: 400,
        ErrorCode.VALIDATION_FAILED: 400,
        ErrorCode.MISSING_REQUIRED: 400,
        
        # 认证错误 -> 401/403
        ErrorCode.AUTH_FAILED: 401,
        ErrorCode.CREDENTIALS_INVALID: 401,
        ErrorCode.PERMISSION_DENIED: 403,
        
        # 限流 -> 429
        ErrorCode.RATE_LIMITED: 429,
        ErrorCode.QUOTA_EXCEEDED: 429,
        ErrorCode.RESOURCE_EXHAUSTED: 429,
        
        # 超时 -> 504
        ErrorCode.TIMEOUT: 504,
        ErrorCode.DEADLINE_EXCEEDED: 504,
        
        # 服务不可用 -> 503
        ErrorCode.SERVICE_UNAVAILABLE: 503,
        ErrorCode.SERVICE_DEGRADED: 503,
        ErrorCode.MAINTENANCE: 503,
    }
    return mapping.get(error_code, 500)

# HTTP 接口使用
@app.post("/api/query")
def query_api():
    result = service.query(request.json["phone"])
    
    return jsonify({
        "success": result.success,
        "data": result.data.__dict__ if result.data else None,
        "error_code": result.error_code.value.code if result.error_code else None,
        "error_message": result.error_message,
        "retryable": result.error_code.value.retryable if result.error_code else False,
    }), error_code_to_http_status(result.error_code) if not result.success else 200
```

### 映射到 gRPC Status Code（可选）

```python
def error_code_to_grpc_status(error_code: ErrorCode) -> grpc.StatusCode:
    """将错误码映射到 gRPC 状态码（仅用于 gRPC 接口）"""
    mapping = {
        ErrorCode.INVALID_INPUT: grpc.StatusCode.INVALID_ARGUMENT,
        ErrorCode.VALIDATION_FAILED: grpc.StatusCode.INVALID_ARGUMENT,
        ErrorCode.MISSING_REQUIRED: grpc.StatusCode.INVALID_ARGUMENT,
        ErrorCode.AUTH_FAILED: grpc.StatusCode.UNAUTHENTICATED,
        ErrorCode.PERMISSION_DENIED: grpc.StatusCode.PERMISSION_DENIED,
        ErrorCode.RATE_LIMITED: grpc.StatusCode.RESOURCE_EXHAUSTED,
        ErrorCode.TIMEOUT: grpc.StatusCode.DEADLINE_EXCEEDED,
        ErrorCode.SERVICE_UNAVAILABLE: grpc.StatusCode.UNAVAILABLE,
    }
    return mapping.get(error_code, grpc.StatusCode.UNKNOWN)
```

---

## 针对 PhoneLocation 的错误码映射

虽然错误码是通用的，但在具体使用时需要映射：

| PhoneLocation 场景 | 使用的通用错误码 |
|------------------|----------------|
| 手机号格式错误 | `VALIDATION_FAILED` |
| 手机号为空 | `MISSING_REQUIRED` |
| timeout 参数不合法 | `INVALID_INPUT` |
| API密钥错误 | `CREDENTIALS_INVALID` |
| 权限不足/账户欠费 | `PERMISSION_DENIED` |
| 请求过于频繁 | `RATE_LIMITED` |
| 请求超时 | `TIMEOUT` |
| 远程服务不可用 | `SERVICE_UNAVAILABLE` |

---

## 优势

### 1. 通用性
- ✅ 错误码可以复用到其他服务
- ✅ 不绑定 phone location 业务

### 2. 协议无关
- ✅ 错误码本身不依赖任何协议
- ✅ 需要时可以映射到 HTTP、gRPC 等

### 3. 语义清晰
- ✅ 使用字符串常量，一目了然
- ✅ 不会和 HTTP 状态码混淆

### 4. 结构化
- ✅ 每个错误包含：码、描述、是否可重试
- ✅ 所有信息都在枚举定义中

### 5. 易于扩展
- ✅ 添加新错误类型只需在枚举中添加一项
- ✅ 不影响现有代码

---

## 问题讨论

### 1. 错误码粒度是否合适？

当前设计了 13 个通用错误码，是否需要：
- 更粗粒度？（例如合并 `TIMEOUT` 和 `DEADLINE_EXCEEDED`）
- 更细粒度？（例如区分不同类型的参数错误）

### 2. 是否需要错误码分组？

例如：
```python
class InputErrorCode(Enum):
    INVALID_INPUT = ...
    VALIDATION_FAILED = ...

class AuthErrorCode(Enum):
    AUTH_FAILED = ...
    PERMISSION_DENIED = ...
```

还是统一在一个 `ErrorCode` 枚举中？

### 3. ErrorType 的设计是否合适？

当前设计：
```python
@dataclass(frozen=True)
class ErrorType:
    code: str
    message: str
    retryable: bool
```

是否需要添加其他字段？例如：
- `category`: 错误分类（input/auth/resource/timeout/service）
- `severity`: 严重程度（error/warning）
- `http_status`: 默认的 HTTP 状态码

---

请告诉我你的想法，我会据此实现完整的代码！

