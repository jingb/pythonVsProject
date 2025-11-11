# V2 使用示例

## 快速开始

```python
from phoneLocation.v2 import PhoneLocationService, ErrorCode

# 初始化服务
service = PhoneLocationService(api_key="your_api_key", timeout=10)

# 查询手机号
result = service.query("13800138000")

# 处理结果
if result.success:
    print(f"查询成功:")
    print(f"  城市: {result.data.city}")
    print(f"  省份: {result.data.province}")
    print(f"  运营商: {result.data.carrier.value}")
else:
    print(f"查询失败:")
    print(f"  错误码: {result.error_code.get_code()}")
    print(f"  错误信息: {result.error_message}")
    print(f"  是否可重试: {result.is_retryable()}")
```

---

## 场景1：基本查询

```python
from phoneLocation.v2 import PhoneLocationService

service = PhoneLocationService(api_key="your_key")

# 查询
result = service.query("13800138000")

# 方式1：显式检查
if result.success:
    location = result.data
    print(f"{location.phone_number} 归属地: {location.city}")
else:
    print(f"查询失败: {result.error_message}")

# 方式2：使用布尔判断
if result:  # 等价于 if result.success:
    print(f"成功: {result.data.city}")
else:
    print(f"失败: {result.error_message}")
```

---

## 场景2：错误处理

### 2.1 精确处理每种错误

```python
from phoneLocation.v2 import PhoneLocationService, ErrorCode

service = PhoneLocationService(api_key="your_key")
result = service.query("13800138000")

if result.success:
    print(f"成功: {result.data.city}")
else:
    # 根据具体错误码处理
    if result.error_code == ErrorCode.VALIDATION_FAILED:
        print(f"❌ 手机号格式错误: {result.error_message}")
        # 修正手机号
        
    elif result.error_code == ErrorCode.MISSING_REQUIRED:
        print(f"❌ 缺少必需参数: {result.error_message}")
        # 提供参数
        
    elif result.error_code == ErrorCode.CREDENTIALS_INVALID:
        print(f"❌ API密钥无效: {result.error_message}")
        # 检查配置
        
    elif result.error_code == ErrorCode.RATE_LIMITED:
        print(f"⚠️ 被限流: {result.error_message}")
        # 等待后重试
        
    elif result.error_code == ErrorCode.TIMEOUT:
        print(f"⚠️ 请求超时: {result.error_message}")
        # 重试
        
    elif result.error_code == ErrorCode.SERVICE_UNAVAILABLE:
        print(f"⚠️ 服务不可用: {result.error_message}")
        # 等待后重试
        
    else:
        print(f"❌ 未知错误: {result.error_message}")
```

### 2.2 使用 is_retryable() 通用处理

```python
result = service.query("13800138000")

if result.success:
    print(f"成功: {result.data.city}")
else:
    # 根据是否可重试分类处理
    if result.is_retryable():
        print(f"⚠️ 临时错误（可重试）: {result.error_message}")
        # 实施重试逻辑
    else:
        print(f"❌ 永久错误（不应重试）: {result.error_message}")
        # 修正参数或配置
```

---

## 场景3：重试逻辑

### 3.1 简单重试

```python
import time
from phoneLocation.v2 import PhoneLocationService

service = PhoneLocationService(api_key="your_key")

max_retries = 3
for attempt in range(max_retries):
    result = service.query("13800138000")
    
    if result.success:
        print(f"✅ 查询成功: {result.data.city}")
        break
    
    if result.is_retryable() and attempt < max_retries - 1:
        wait_time = 2 ** attempt  # 指数退避：1秒、2秒、4秒
        print(f"⚠️ 第 {attempt + 1} 次失败，等待 {wait_time} 秒后重试")
        time.sleep(wait_time)
    else:
        print(f"❌ 不可重试或达到最大重试次数: {result.error_message}")
        break
```

### 3.2 智能重试（处理限流）

```python
import time
from phoneLocation.v2 import PhoneLocationService, ErrorCode

service = PhoneLocationService(api_key="your_key")

def query_with_retry(phone_number: str, max_retries: int = 3):
    """带智能重试的查询"""
    for attempt in range(max_retries):
        result = service.query(phone_number)
        
        if result.success:
            return result
        
        # 如果是限流，使用服务方建议的等待时间
        if result.error_code == ErrorCode.RATE_LIMITED:
            retry_after = result.metadata.get("retry_after", 60)
            print(f"⚠️ 被限流，等待 {retry_after} 秒后重试")
            time.sleep(retry_after)
            continue
        
        # 其他可重试错误，使用指数退避
        if result.is_retryable() and attempt < max_retries - 1:
            wait_time = 2 ** attempt
            print(f"⚠️ 临时错误，等待 {wait_time} 秒后重试")
            time.sleep(wait_time)
            continue
        
        # 不可重试或达到最大次数
        print(f"❌ {result.error_message}")
        return result
    
    return result

# 使用
result = query_with_retry("13800138000")
if result.success:
    print(f"✅ 成功: {result.data.city}")
```

---

## 场景4：HTTP 接口（Flask）

```python
from flask import Flask, request, jsonify
from phoneLocation.v2 import PhoneLocationService

app = Flask(__name__)
service = PhoneLocationService(api_key="your_key")

@app.post("/api/v2/query")
def query_api():
    """查询接口（V2）"""
    phone = request.json.get("phone")
    
    # 调用服务
    result = service.query(phone)
    
    # 直接返回，无需手动映射
    return jsonify(result.to_dict()), result.to_http_status()

if __name__ == "__main__":
    app.run(port=5000)
```

**客户端调用**：
```python
import requests

# 发送请求
response = requests.post(
    "http://localhost:5000/api/v2/query",
    json={"phone": "13800138000"}
)

data = response.json()

# 处理响应
if data["success"]:
    print(f"✅ 城市: {data['data']['city']}")
else:
    print(f"❌ 错误: {data['error_message']}")
    print(f"   错误码: {data['error_code']}")
    print(f"   可重试: {data['retryable']}")
```

---

## 场景5：序列化

```python
import json
from phoneLocation.v2 import PhoneLocationService

service = PhoneLocationService(api_key="your_key")
result = service.query("13800138000")

# 转换为字典
result_dict = result.to_dict()

# 序列化为 JSON
json_str = json.dumps(result_dict, ensure_ascii=False, indent=2)
print(json_str)

# 输出示例（成功）：
# {
#   "success": true,
#   "data": {
#     "phone_number": "13800138000",
#     "province": "北京市",
#     "city": "北京市",
#     "carrier": "CHINA_MOBILE",
#     "is_valid": true
#   }
# }

# 输出示例（失败）：
# {
#   "success": false,
#   "error_code": "VALIDATION_FAILED",
#   "error_message": "手机号格式不正确: invalid",
#   "retryable": false
# }
```

---

## 场景6：带元数据

```python
from phoneLocation.v2 import PhoneLocationService, ErrorCode
import time

service = PhoneLocationService(api_key="your_key")

# 假设服务返回了带元数据的结果
# result = Result.error(
#     error_code=ErrorCode.RATE_LIMITED,
#     error_message="请求过于频繁",
#     metadata={
#         "retry_after": 60,
#         "request_id": "req_123",
#         "timestamp": int(time.time())
#     }
# )

# 使用元数据
result = service.query("13800138000")
if not result.success:
    # 读取元数据
    request_id = result.metadata.get("request_id")
    retry_after = result.metadata.get("retry_after")
    
    print(f"请求ID: {request_id}")
    if retry_after:
        print(f"建议 {retry_after} 秒后重试")
```

---

## 场景7：批量查询（自己实现）

V2 不提供 `batch_query` 方法，但你可以自己实现：

```python
from phoneLocation.v2 import PhoneLocationService

service = PhoneLocationService(api_key="your_key")

def batch_query(phone_numbers: list[str]) -> dict:
    """批量查询（自己实现）"""
    results = {}
    
    for phone in phone_numbers:
        result = service.query(phone)
        if result.success:
            results[phone] = result.data
        else:
            print(f"❌ {phone} 查询失败: {result.error_message}")
    
    return results

# 使用
phones = ["13800138000", "13900139000", "15800158000"]
results = batch_query(phones)

for phone, location in results.items():
    print(f"{phone}: {location.city}")
```

---

## 场景8：测试

```python
import pytest
from phoneLocation.v2 import PhoneLocationService, ErrorCode

def test_query_success():
    """测试查询成功"""
    service = PhoneLocationService(api_key="test_key")
    
    # 假设这里 mock 了远程 API
    result = service.query("13800138000")
    
    assert result.success
    assert result.data is not None
    assert result.data.city == "北京市"

def test_query_validation_error():
    """测试参数校验错误"""
    service = PhoneLocationService(api_key="test_key")
    
    # 空手机号
    result = service.query("")
    assert not result.success
    assert result.error_code == ErrorCode.MISSING_REQUIRED
    assert not result.is_retryable()

def test_query_format_error():
    """测试格式错误"""
    service = PhoneLocationService(api_key="test_key")
    
    # 格式不正确
    result = service.query("invalid")
    assert not result.success
    assert result.error_code == ErrorCode.VALIDATION_FAILED
    assert not result.is_retryable()

def test_is_retryable():
    """测试重试判断"""
    service = PhoneLocationService(api_key="test_key")
    
    # 参数错误不可重试
    result = service.query("")
    assert not result.is_retryable()
    
    # （假设模拟了超时错误）
    # result = Result.error(error_code=ErrorCode.TIMEOUT)
    # assert result.is_retryable()
```

---

## 常见问题

### Q1: 如何知道是否应该重试？

**A**: 使用 `result.is_retryable()` 方法：

```python
if not result.success:
    if result.is_retryable():
        # 可以重试
        print("临时错误，可以重试")
    else:
        # 不应重试
        print("永久错误，修正参数")
```

### Q2: 如何获取限流的等待时间？

**A**: 从 `metadata` 中获取：

```python
if result.error_code == ErrorCode.RATE_LIMITED:
    retry_after = result.metadata.get("retry_after", 60)
    time.sleep(retry_after)
```

### Q3: 如何序列化为 JSON？

**A**: 使用 `to_dict()` 方法：

```python
result_dict = result.to_dict()
json_str = json.dumps(result_dict)
```

### Q4: V2 比 V1 有什么优势？

**A**: 
- ✅ 适合远程调用（HTTP/gRPC）
- ✅ 错误信息不会丢失
- ✅ 易于序列化
- ✅ 统一的错误处理

详见 [V1_VS_V2_COMPARISON.md](V1_VS_V2_COMPARISON.md)

---

## 总结

V2 的核心改进：
1. ✅ 使用 `Result[PhoneLocation]` 而不是抛异常
2. ✅ 使用通用的 `ErrorCode` 枚举
3. ✅ 支持序列化（`to_dict()`）
4. ✅ 适合本地和远程调用

**开始使用 V2**：
```python
from phoneLocation.v2 import PhoneLocationService

service = PhoneLocationService(api_key="your_key")
result = service.query("13800138000")

if result.success:
    print(result.data.city)
else:
    print(result.error_message)
```

