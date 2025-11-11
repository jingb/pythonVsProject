# V1 vs V2 对比

## 核心区别

| 特性 | V1 | V2 |
|-----|----|----|
| **返回值** | `PhoneLocation` 对象 | `Result[PhoneLocation]` 对象 |
| **错误处理** | 抛异常 | 返回 `Result.error()` |
| **错误码** | 异常类名 | `ErrorCode` 枚举 |
| **适用场景** | 本地调用（同进程） | 本地 + 远程调用 |
| **序列化** | ❌ 困难 | ✅ `result.to_dict()` |
| **远程调用** | ❌ 需要手动映射 | ✅ 开箱即用 |

---

## 代码对比

### 1. 方法签名

#### V1
```python
def query(self, phone_number: str, timeout: Optional[int] = None) -> PhoneLocation:
    """查询手机号归属地"""
```

#### V2
```python
def query(self, phone_number: str, timeout: Optional[int] = None) -> Result[PhoneLocation]:
    """查询手机号归属地"""
```

---

### 2. 成功情况

#### V1
```python
# 服务端
def query(self, phone_number: str) -> PhoneLocation:
    # ... 校验和处理
    location = PhoneLocation(...)
    return location  # 直接返回对象

# 调用方
location = service.query("13800138000")  # 直接得到结果
print(location.city)
```

#### V2
```python
# 服务端
def query(self, phone_number: str) -> Result[PhoneLocation]:
    # ... 校验和处理
    location = PhoneLocation(...)
    return Result.success(data=location)  # 包装为 Result

# 调用方
result = service.query("13800138000")
if result.success:  # 需要检查 success
    print(result.data.city)
```

---

### 3. 错误情况

#### V1 - 抛异常
```python
# 服务端
def query(self, phone_number: str) -> PhoneLocation:
    if not phone_number:
        raise InvalidPhoneNumberError("手机号为空")  # 抛异常
    
    if not self._validate_format(phone_number):
        raise InvalidPhoneNumberError("格式错误")
    
    # ...

# 调用方
try:
    location = service.query("invalid")
except InvalidPhoneNumberError as e:
    print(f"参数错误: {e.message}")
except RateLimitExceededError as e:
    print(f"被限流，等待 {e.retry_after} 秒")
    time.sleep(e.retry_after)
except TimeoutError:
    print("超时，可以重试")
```

#### V2 - 返回 Result
```python
# 服务端
def query(self, phone_number: str) -> Result[PhoneLocation]:
    if not phone_number:
        return Result.error(
            error_code=ErrorCode.MISSING_REQUIRED,
            error_message="手机号为空"
        )
    
    if not self._validate_format(phone_number):
        return Result.error(
            error_code=ErrorCode.VALIDATION_FAILED,
            error_message="格式错误"
        )
    
    # ...

# 调用方
result = service.query("invalid")
if not result.success:
    if result.error_code == ErrorCode.VALIDATION_FAILED:
        print(f"参数错误: {result.error_message}")
    elif result.error_code == ErrorCode.RATE_LIMITED:
        retry_after = result.metadata.get("retry_after", 60)
        print(f"被限流，等待 {retry_after} 秒")
        time.sleep(retry_after)
    elif result.is_retryable():
        print("可以重试")
```

---

### 4. 重试判断

#### V1
```python
try:
    location = service.query(phone)
except PhoneAPIException as e:
    if e.is_retryable():  # 异常对象的方法
        print("可以重试")
    else:
        print("不应重试")
```

#### V2
```python
result = service.query(phone)
if not result.success:
    if result.is_retryable():  # Result 对象的方法
        print("可以重试")
    else:
        print("不应重试")
```

---

## 使用场景对比

### 场景1：本地调用（同进程）

#### V1 ✅ 简洁
```python
from phoneLocation.v1 import PhoneLocationService

service = PhoneLocationService(api_key="key")

try:
    location = service.query("13800138000")
    print(f"城市: {location.city}")
except ClientError:
    print("参数错误")
except RetryableError:
    print("可以重试")
```

#### V2 ✅ 统一
```python
from phoneLocation.v2 import PhoneLocationService

service = PhoneLocationService(api_key="key")

result = service.query("13800138000")
if result.success:
    print(f"城市: {result.data.city}")
elif result.is_retryable():
    print("可以重试")
else:
    print("参数错误")
```

**对比**：
- V1 更符合 Python 习惯（EAFP）
- V2 统一处理，但稍显冗长

---

### 场景2：HTTP 服务端

#### V1 ❌ 需要手动映射
```python
from flask import Flask, jsonify
from phoneLocation.v1 import PhoneLocationService, PhoneAPIException

app = Flask(__name__)
service = PhoneLocationService(api_key="key")

@app.post("/api/query")
def query():
    try:
        location = service.query(request.json["phone"])
        return jsonify({
            "success": True,
            "data": location.__dict__
        }), 200
        
    except InvalidPhoneNumberError as e:
        return jsonify({"error": e.message}), 400
    except RateLimitExceededError as e:
        # ❌ retry_after 容易遗漏
        return jsonify({"error": e.message}), 429
    except TimeoutError:
        return jsonify({"error": "timeout"}), 504
    except PhoneAPIException as e:
        return jsonify({"error": e.message}), 500
```

#### V2 ✅ 直接返回
```python
from flask import Flask, jsonify
from phoneLocation.v2 import PhoneLocationService

app = Flask(__name__)
service = PhoneLocationService(api_key="key")

@app.post("/api/query")
def query():
    result = service.query(request.json["phone"])
    
    # ✅ 直接序列化，无需手动映射
    return jsonify(result.to_dict()), result.to_http_status()
```

**对比**：
- V1 需要为每个异常写映射逻辑
- V2 开箱即用，代码简洁

---

### 场景3：HTTP 客户端

#### V1 ❌ 信息丢失
```python
import requests

response = requests.post("http://api/query", json={"phone": "13800138000"})

if response.status_code == 200:
    data = response.json()["data"]
    print(f"成功: {data['city']}")
elif response.status_code == 429:
    # ❌ retry_after 在哪里？
    # ❌ 无法知道具体是哪种限流
    print("被限流")
elif response.status_code == 400:
    # ❌ 400 可能是多种错误
    print("参数错误")
```

#### V2 ✅ 信息完整
```python
import requests

response = requests.post("http://api/query", json={"phone": "13800138000"})
data = response.json()

if data["success"]:
    print(f"成功: {data['data']['city']}")
else:
    # ✅ 可以精确判断错误类型
    if data["error_code"] == "RATE_LIMITED":
        retry_after = data.get("metadata", {}).get("retry_after", 60)
        print(f"被限流，等待 {retry_after} 秒")
    elif data["error_code"] == "VALIDATION_FAILED":
        print(f"参数错误: {data['error_message']}")
    
    # ✅ 通用处理
    if data["retryable"]:
        print("可以重试")
```

**对比**：
- V1 错误信息容易丢失，只能靠 HTTP 状态码判断
- V2 错误信息完整，可以精确判断

---

### 场景4：gRPC

#### V1 ❌ 需要手动映射
```python
# V1 gRPC 服务端
def Query(self, request, context):
    try:
        location = service.query(request.phone_number)
        return QueryResponse(success=True, location=location)
    except InvalidPhoneNumberError:
        context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
        return QueryResponse()
    except RateLimitExceededError as e:
        context.set_code(grpc.StatusCode.RESOURCE_EXHAUSTED)
        # ❌ retry_after 需要额外处理
        return QueryResponse()
    # ... 每个异常都要映射
```

#### V2 ✅ 直接映射
```python
# V2 gRPC 服务端
def Query(self, request, context):
    result = service.query(request.phone_number)
    
    return QueryResponse(
        success=result.success,
        location=result.data if result.success else None,
        error_code=result.error_code.get_code() if not result.success else "",
        error_message=result.error_message or "",
        retryable=result.is_retryable(),
    )
```

**对比**：
- V1 需要为每个异常写 gRPC 映射
- V2 统一映射，代码简洁

---

## 迁移指南

### 从 V1 迁移到 V2

#### 1. 更新导入
```python
# V1
from phoneLocation.v1 import PhoneLocationService

# V2
from phoneLocation.v2 import PhoneLocationService
```

#### 2. 更新错误处理

**V1 代码**：
```python
try:
    location = service.query(phone)
    use_location(location)
except InvalidPhoneNumberError:
    handle_invalid_phone()
except RateLimitExceededError as e:
    wait_and_retry(e.retry_after)
except TimeoutError:
    retry()
```

**迁移到 V2**：
```python
result = service.query(phone)

if result.success:
    use_location(result.data)
else:
    if result.error_code == ErrorCode.VALIDATION_FAILED:
        handle_invalid_phone()
    elif result.error_code == ErrorCode.RATE_LIMITED:
        retry_after = result.metadata.get("retry_after", 60)
        wait_and_retry(retry_after)
    elif result.error_code == ErrorCode.TIMEOUT:
        retry()
```

#### 3. 更新测试代码

**V1 测试**：
```python
def test_invalid_phone():
    with pytest.raises(InvalidPhoneNumberError):
        service.query("invalid")
```

**V2 测试**：
```python
def test_invalid_phone():
    result = service.query("invalid")
    assert not result.success
    assert result.error_code == ErrorCode.VALIDATION_FAILED
```

---

## 选择建议

### 选择 V1（异常模式）的场景：
- ✅ 单体应用（所有模块在同一进程）
- ✅ 只有本地调用
- ✅ 团队熟悉 Python 异常处理
- ✅ 想要更 Pythonic 的代码

### 选择 V2（Result 模式）的场景：
- ✅ 微服务架构
- ✅ 需要通过 HTTP/gRPC 暴露接口
- ✅ 需要在不同语言/平台间传递错误信息
- ✅ 需要统一的错误处理逻辑
- ✅ 需要完整保留错误信息（不丢失）

---

## 总结

| 方面 | V1（异常模式） | V2（Result 模式） |
|-----|-------------|-----------------|
| **Python 习惯** | ✅ 符合 EAFP | ⚠️ 类似函数式编程 |
| **代码简洁性** | ✅ 简洁 | ⚠️ 稍显冗长 |
| **本地调用** | ✅ 优秀 | ✅ 良好 |
| **远程调用** | ❌ 需要适配 | ✅ 开箱即用 |
| **错误信息** | ⚠️ 容易丢失 | ✅ 完整保留 |
| **序列化** | ❌ 困难 | ✅ 简单 |
| **协议映射** | ❌ 每个协议都要写 | ✅ 统一处理 |
| **学习曲线** | ✅ 低（Python 开发者熟悉） | ⚠️ 中等 |

**推荐**：
- 如果你的服务只在内部使用（本地调用），选择 **V1**
- 如果你的服务需要通过网络暴露（HTTP/gRPC），选择 **V2**
- 如果两者都需要，V2 可以统一处理

