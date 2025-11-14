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
│   ├── INVALID_PARAMETER      # 参数不合法（包括格式、类型、值等）
│   └── MISSING_PARAMETER      # 缺少必需参数
│
├── 认证授权错误
│   ├── AUTH_FAILED            # 认证失败
│   ├── PERMISSION_DENIED      # 权限不足
│   └── CREDENTIALS_INVALID    # 凭证无效
│
├── 资源限制错误（可重试）
│   ├── RATE_LIMITED           # 请求频率超限
│   └── QUOTA_EXCEEDED         # 配额耗尽
│
├── 超时错误（可重试）
│   └── TIMEOUT                # 请求超时
│
└── 服务状态错误（可重试）
    ├── SERVICE_UNAVAILABLE    # 服务不可用
    └── PARTIAL_FAILURE        # 部分功能不可用
```

---

## 错误枚举实现

```python
from enum import Enum

class ErrorCode(Enum):
    """通用错误码枚举
    
    每个错误码包含三个属性：
    - code: 错误码字符串
    - message: 错误描述
    - retryable: 是否可重试
    """
    
    def __init__(self, code: str, message: str, retryable: bool):
        self._code = code
        self._message = message
        self._retryable = retryable
    
    # ==================== 输入错误（调用方问题，不可重试）====================
    
    INVALID_PARAMETER = (
        "INVALID_PARAMETER",
        "参数不合法（包括格式错误、类型错误、值不合理等）",
        False
    )
    
    MISSING_PARAMETER = (
        "MISSING_PARAMETER",
        "缺少必需参数",
        False
    )
    
    # ==================== 属性访问 ====================
    
    @property
    def code(self) -> str:
        """错误码字符串"""
        return self._code
    
    @property
    def message(self) -> str:
        """错误描述"""
        return self._message
    
    @property
    def retryable(self) -> bool:
        """是否可重试"""
        return self._retryable
    
    # ==================== 认证授权错误（不可重试）====================
    
    AUTH_FAILED = ("AUTH_FAILED", "认证失败", False)
    PERMISSION_DENIED = ("PERMISSION_DENIED", "权限不足", False)
    CREDENTIALS_INVALID = ("CREDENTIALS_INVALID", "凭证无效", False)
    
    # ==================== 资源限制错误（可重试）====================
    
    RATE_LIMITED = ("RATE_LIMITED", "请求频率超限", True)
    QUOTA_EXCEEDED = ("QUOTA_EXCEEDED", "配额耗尽", True)
    
    # ==================== 超时错误（可重试）====================
    
    TIMEOUT = ("TIMEOUT", "请求超时", True)
    
    # ==================== 服务状态错误（可重试）====================
    
    SERVICE_UNAVAILABLE = ("SERVICE_UNAVAILABLE", "服务不可用", True)
    PARTIAL_FAILURE = ("PARTIAL_FAILURE", "部分功能不可用，无法返回完整数据", True)
    
    # ==================== 方法 ====================
    
    def to_http_status(self) -> int:
        """转换为 HTTP 状态码（仅用于 HTTP 接口）
        
        Returns:
            int: HTTP 状态码
        """
        mapping = {
            ErrorCode.INVALID_PARAMETER: 400,
            ErrorCode.MISSING_PARAMETER: 400,
            ErrorCode.AUTH_FAILED: 401,
            ErrorCode.CREDENTIALS_INVALID: 401,
            ErrorCode.PERMISSION_DENIED: 403,
            ErrorCode.RATE_LIMITED: 429,
            ErrorCode.QUOTA_EXCEEDED: 429,
            ErrorCode.TIMEOUT: 504,
            ErrorCode.SERVICE_UNAVAILABLE: 503,
            ErrorCode.PARTIAL_FAILURE: 503,
        }
        return mapping.get(self, 500)
    
    @classmethod
    def from_code(cls, code: str) -> 'ErrorCode':
        """根据错误码字符串获取枚举值"""
        for error in cls:
            if error.code == code:
                return error
        raise ValueError(f"Unknown error code: {code}")
    
```

---

## 使用示例

### 在 Service 中使用

```python
def query(self, phone_number: str) -> QueryResult:
    # 参数校验
    if not phone_number:
        return QueryResult.error(
            error_code=ErrorCode.MISSING_PARAMETER,
            error_message="phone_number 参数为空"
        )
    
    if not self._validate_phone_format(phone_number):
        return QueryResult.error(
            error_code=ErrorCode.INVALID_PARAMETER,
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
        retry_after = result.metadata.get("retry_after", 60)
        print(f"被限流，{retry_after} 秒后重试")
        time.sleep(retry_after)
        # 重试
    elif result.error_code == ErrorCode.INVALID_PARAMETER:
        print(f"参数错误: {result.error_message}")
        # 修正参数
    
    # 方式2：根据 retryable 判断
    if result.error_code.retryable:
        print("这是临时错误，可以重试")
    else:
        print("这是永久错误，不应重试")
    
    # 方式3：获取错误信息
    print(f"错误码: {result.error_code.code}")
    print(f"错误描述: {result.error_code.desc}")
    print(f"HTTP状态码: {result.error_code.to_http_status()}")
```

### 映射到 HTTP 状态码

ErrorCode 内置了 `to_http_status()` 方法，可以直接转换为 HTTP 状态码：

```python
# 直接使用
error = ErrorCode.RATE_LIMITED
http_status = error.to_http_status()  # 429

# 在 HTTP 接口中使用
@app.post("/api/query")
def query_api():
    result = service.query(request.json["phone"])
    
    # Result 类的 to_http_status() 会委托给 ErrorCode.to_http_status()
    return jsonify(result.to_dict()), result.to_http_status()
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
| 手机号格式错误 | `INVALID_PARAMETER` |
| 手机号为空 | `MISSING_PARAMETER` |
| timeout 参数不合法 | `INVALID_PARAMETER` |
| API密钥错误 | `CREDENTIALS_INVALID` |
| 权限不足/账户欠费 | `PERMISSION_DENIED` |
| 请求过于频繁 | `RATE_LIMITED` |
| 请求超时 | `TIMEOUT` |
| 远程服务不可用 | `SERVICE_UNAVAILABLE` |
| 部分数据不可用 | `PARTIAL_FAILURE` |

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

## 总结

当前错误码设计包含 **9 个通用错误码**，分为 5 大类：

| 分类 | 错误码 | 数量 |
|------|--------|------|
| 输入错误 | INVALID_PARAMETER, MISSING_PARAMETER | 2 |
| 认证错误 | AUTH_FAILED, PERMISSION_DENIED, CREDENTIALS_INVALID | 3 |
| 资源限制 | RATE_LIMITED, QUOTA_EXCEEDED | 2 |
| 超时错误 | TIMEOUT | 1 |
| 服务状态 | SERVICE_UNAVAILABLE, PARTIAL_FAILURE | 2 |

**设计原则**：
- ✅ 通用性：不绑定具体业务
- ✅ 协议无关：不使用 HTTP 状态码
- ✅ 语义清晰：使用字符串常量
- ✅ 结构化：包含码、描述、可重试标志
- ✅ 易于扩展：添加新错误类型简单

---

**版本**: V2.3.0  
**最后更新**: 2024-11-12  
**重要变更**: 
- V2.3.0: HTTP 状态码映射移至 ErrorCode.to_http_status()
- V2.2.0: 合并 ErrorType 和 ErrorCode 为单一枚举类

