# 手机号归属地查询服务 - API 参考文档

> **版本**: v1.0.0  
> **状态**: 接口声明完成，实现待填充

## 概述

本服务提供手机号归属地查询功能，包括省份、城市、运营商等信息。

**设计特点**：
- ✅ 接口清晰，开箱即用
- ✅ 异常按责任方分类（ClientError vs RetryableError）
- ✅ 完整的类型提示
- ✅ 智能重试判断（`is_retryable()`）

---

## 快速开始

```python
from phoneLocation.v1 import PhoneLocationService

# 初始化
service = PhoneLocationService(api_key="your_api_key")

# 查询
location = service.query("13800138000")
print(f"{location.province} {location.city} {location.carrier.value}")
```

---

## API 接口

### PhoneLocationService

#### 初始化

```python
service = PhoneLocationService(
    api_key: str,       # API密钥（必填）
    timeout: int = 10   # 默认超时时间（秒）
)
```

**参数说明**：
- `api_key`: API密钥，必填
- `timeout`: 默认超时时间（秒），默认10秒

**异常**：
- `ValueError`: 当 api_key 为空时

---

#### query() - 查询手机号归属地

```python
location: PhoneLocation = service.query(
    phone_number: str,           # 手机号（11位数字）
    timeout: Optional[int] = None # 超时时间（可选）
)
```

**参数说明**：
- `phone_number`: 手机号码（11位数字字符串）
- `timeout`: 超时时间（秒），不指定则使用初始化时的默认值

**返回值**：`PhoneLocation` 对象，包含：
- `phone_number`: 查询的手机号
- `province`: 省份
- `city`: 城市
- `carrier`: 运营商（CarrierType枚举）
- `is_valid`: 号码是否有效

**可能抛出的异常**：

| 异常类型 | 分类 | 可重试 | 场景 | 处理建议 |
|---------|------|--------|------|---------|
| `InvalidPhoneNumberError` | ClientError | ❌ | 手机号格式错误、号段不存在 | 检查并修正手机号 |
| `InvalidParameterError` | ClientError | ❌ | 参数不合法 | 检查并修正参数 |
| `AuthenticationError` | ClientError | ❌ | API密钥错误、权限不足 | 检查API密钥配置 |
| `RateLimitExceededError` | RetryableError | ✅ | 请求频率超限 | 等待 retry_after 秒后重试 |
| `TimeoutError` | RetryableError | ✅ | 请求超时 | 重试，考虑增加 timeout |
| `ServiceUnavailableError` | RetryableError | ✅ | 服务临时不可用 | 使用指数退避策略重试 |

---

## 数据模型

### PhoneLocation - 查询结果

```python
@dataclass
class PhoneLocation:
    phone_number: str    # 手机号码
    province: str        # 省份
    city: str           # 城市
    carrier: CarrierType # 运营商
    is_valid: bool       # 是否有效
```

**示例**：
```python
PhoneLocation(
    phone_number="13800138000",
    province="北京市",
    city="北京市",
    carrier=CarrierType.CHINA_MOBILE,
    is_valid=True
)
```

---

### CarrierType - 运营商枚举

```python
class CarrierType(Enum):
    CHINA_MOBILE = "中国移动"
    CHINA_UNICOM = "中国联通"
    CHINA_TELECOM = "中国电信"
    UNKNOWN = "未知"
```

---

## 异常体系

### 异常分类

```
PhoneAPIException (基类)
├── ClientError (客户端错误，不可重试)
│   ├── InvalidPhoneNumberError
│   ├── InvalidParameterError
│   └── AuthenticationError
│
└── RetryableError (可重试错误)
    ├── RateLimitExceededError
    ├── TimeoutError
    └── ServiceUnavailableError
```

### 异常基类

```python
class PhoneAPIException(Exception):
    message: str              # 错误消息
    error_code: Optional[str] # 错误码（可选）
    
    def is_retryable() -> bool:
        """判断是否可重试
        
        Returns:
            True: 可以重试（临时问题）
            False: 不应重试（永久问题）
        """
```

### 特殊异常属性

**RateLimitExceededError** 和 **ServiceUnavailableError** 提供：

```python
retry_after: Optional[int]  # 建议多少秒后重试
```

使用示例：
```python
except RateLimitExceededError as e:
    wait_time = e.retry_after or 60
    time.sleep(wait_time)
    # 重试
```

---

## 使用指南

### 1. 基本使用

```python
from phoneLocation.v1 import PhoneLocationService

service = PhoneLocationService(api_key="your_api_key")
location = service.query("13800138000")
print(f"{location.province} {location.city}")
```

---

### 2. 异常处理

#### 方式1：详细处理每种异常

```python
from phoneLocation.v1 import (
    PhoneLocationService,
    InvalidPhoneNumberError,
    RateLimitExceededError,
    TimeoutError,
)

service = PhoneLocationService(api_key="your_api_key")

try:
    location = service.query("13800138000")
    print(f"查询成功: {location}")
    
except InvalidPhoneNumberError:
    print("❌ 手机号格式错误，请检查")
    
except RateLimitExceededError as e:
    wait_time = e.retry_after or 60
    print(f"⚠️ 请求过于频繁，{wait_time}秒后重试")
    
except TimeoutError:
    print("⚠️ 请求超时，可以重试")
```

---

#### 方式2：按分类处理

```python
from phoneLocation.v1 import ClientError, RetryableError

try:
    location = service.query("13800138000")
    
except ClientError as e:
    # 这是调用方的问题（参数错误、认证失败等）
    print(f"🔴 客户端错误: {e.message}")
    # 处理：修正参数或配置，不要重试
    
except RetryableError as e:
    # 这是临时问题（限流、超时、服务不可用等）
    print(f"🟡 临时错误: {e.message}")
    # 处理：可以重试
```

---

#### 方式3：智能判断

```python
from phoneLocation.v1 import PhoneAPIException

try:
    location = service.query("13800138000")
    
except PhoneAPIException as e:
    if e.is_retryable():
        print(f"临时错误，可以重试: {e.message}")
        # 实施重试逻辑
    else:
        print(f"永久错误，需要修正参数: {e.message}")
        # 记录日志，修正参数
```

---

### 3. 智能重试策略

```python
from phoneLocation.v1 import PhoneLocationService, PhoneAPIException
import time

service = PhoneLocationService(api_key="your_api_key")

max_retries = 3
for attempt in range(max_retries):
    try:
        location = service.query("13800138000")
        print(f"查询成功: {location.city}")
        break
        
    except PhoneAPIException as e:
        # 使用 is_retryable() 判断是否应该重试
        if e.is_retryable() and attempt < max_retries - 1:
            wait_time = 2 ** attempt  # 指数退避：1秒、2秒、4秒
            print(f"第 {attempt + 1} 次失败，等待 {wait_time} 秒后重试")
            time.sleep(wait_time)
            continue
        else:
            print(f"不可重试或达到最大重试次数: {e.message}")
            raise
```

---

### 4. 尊重限流建议

```python
from phoneLocation.v1 import RateLimitExceededError
import time

try:
    location = service.query("13800138000")
    
except RateLimitExceededError as e:
    # 获取服务方建议的等待时间
    wait_time = e.retry_after
    if wait_time:
        print(f"被限流，建议等待 {wait_time} 秒")
        time.sleep(wait_time)
        
        # 重试
        location = service.query("13800138000")
        print(f"重试成功: {location.city}")
    else:
        print("被限流，使用默认等待时间")
        time.sleep(60)
```

---

### 5. 自定义超时时间

```python
# 方式1：设置默认超时
service = PhoneLocationService(api_key="your_api_key", timeout=15)

# 方式2：针对特定请求设置超时
location = service.query("13800138000", timeout=20)
```

---

## 设计原则

### 1. 接口与实现分离

- **Service 层**：对外暴露的接口（稳定）
- **Client 层**：内部实现细节（可变更）
- 调用方只使用 `PhoneLocationService`，不关心内部实现
- 未来可以切换供应商而不影响调用方代码

### 2. 异常按责任方分类

- **ClientError**：调用方的问题（参数错误、认证失败）
  - 特点：不可重试，需要修正代码或配置
  
- **RetryableError**：临时问题（限流、超时、服务不可用）
  - 特点：可以重试，通常是短暂的故障

- 使用 `is_retryable()` 方法统一判断是否可重试

### 3. 清晰的错误信息

每个异常都提供：
- `message`: 人类可读的错误描述
- `error_code`: 机器可读的错误代码（可选）
- `retry_after`: 服务方建议的等待时间（适用于限流等场景）

### 4. 类型安全

- 完整的类型提示（type hints）
- 使用 `dataclass` 定义数据结构
- 使用 `Enum` 定义枚举类型
- IDE 支持自动补全和类型检查

---

## 调用方的职责

PhoneLocationService 的 API 设计已经足够清晰和友好，不需要封装即可使用。

作为调用方，你需要根据业务场景决定：

1. **是否重试**
   - 根据 `is_retryable()` 或异常类型判断
   - `ClientError` 不应重试
   - `RetryableError` 可以重试

2. **重试策略**
   - 指数退避（推荐）：等待时间翻倍
   - 固定间隔：每次等待固定时间
   - 尊重 `retry_after`：优先使用服务方建议的时间

3. **最大重试次数**
   - 根据业务 SLA 决定
   - 避免无限重试

4. **日志记录**
   - 记录查询请求和异常信息
   - 便于问题排查和监控

5. **降级策略**
   - 当服务持续不可用时的备选方案
   - 例如：返回默认值、使用缓存、切换供应商等

---

## 最佳实践

详细的最佳实践示例请参考：
- **[test_service.py](test_service.py)** - 包含5个真实生产场景的完整示例
- **[RUN_TESTS.md](RUN_TESTS.md)** - 测试运行指南和最佳实践说明

---

## 实现状态

### ✅ 已完成
- [x] 接口声明
- [x] 数据模型
- [x] 异常体系
- [x] 类型提示
- [x] 完整文档

### ⏳ 待实现
- [ ] Service 层实现
- [ ] HTTP 客户端实现
- [ ] 连接真实API

---

## 注意事项

1. **只使用 PhoneLocationService**
   - 不要直接使用内部实现（如 Client 层）
   - 内部实现可能随时变更

2. **异常处理建议**
   - 优先使用 `is_retryable()` 判断是否重试
   - 利用异常基类（ClientError/RetryableError）分类处理
   - 尊重 `retry_after` 建议，避免过于频繁的重试

3. **超时设置建议**
   - 根据业务场景设置合理的超时时间
   - 可以在方法级别覆盖默认超时时间

4. **监控和日志**
   - 记录所有API调用和异常
   - 监控限流频率和成功率
   - 及时发现和处理问题

---

## 版本信息

- **当前版本**: v1.0.0
- **状态**: 接口声明完成，实现待填充
- **最后更新**: 2025-11-06

---

## 相关文档

- **[RUN_TESTS.md](RUN_TESTS.md)** - 测试运行指南和最佳实践
- **[test_service.py](test_service.py)** - 生产环境使用示例

