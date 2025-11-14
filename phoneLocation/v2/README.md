# PhoneLocation V2

手机号归属地查询服务 V2 - 使用 Result 返回值，适合本地和远程调用。

## 🎯 V2 核心改进

| 改进点 | V1 | V2 |
|-------|----|----|
| **返回值** | `PhoneLocation` 对象 | `Result[PhoneLocation]` 对象 |
| **错误处理** | 抛异常 | 返回 `Result.error()` |
| **错误码** | 异常类名 | 通用 `ErrorCode` 枚举 |
| **序列化** | ❌ 困难 | ✅ `result.to_dict()` |
| **远程调用** | ❌ 需手动映射 | ✅ 开箱即用 |
| **适用场景** | 本地调用 | 本地 + 远程调用 |

---

## 📦 快速开始

```python
from phoneLocation.v2 import PhoneLocationService, ErrorCode

# 初始化
service = PhoneLocationService(api_key="your_key")

# 查询
result = service.query("13800138000")

# 处理结果
if result.success:
    print(f"城市: {result.data.city}")
else:
    print(f"错误: {result.error_message}")
    if result.is_retryable():
        print("可以重试")
```

---

## 📁 文件结构

```
v2/
├── 📄 核心代码
│   ├── __init__.py           # 模块导出
│   ├── service.py            # PhoneLocationService
│   ├── result.py             # Result 返回值类
│   ├── models.py             # PhoneLocation、CarrierType
│   └── error_types.py        # ErrorCode 错误码枚举
│
└── 📝 文档
    ├── README.md             # 本文件
    ├── USAGE_EXAMPLE.md      # 使用示例（必看）
    ├── V1_VS_V2_COMPARISON.md # V1 vs V2 对比
    ├── PROBLEM_BACKGROUND.md  # 为什么需要 V2
    ├── RESULT_DESIGN.md       # Result 类设计说明
    └── ERROR_CODE_DESIGN.md   # 错误码设计说明
```

---

## 🚀 核心组件

### 1. PhoneLocationService

```python
class PhoneLocationService:
    def __init__(self, api_key: str, timeout: int = 10):
        """初始化服务"""
    
    def query(self, phone_number: str, timeout: Optional[int] = None) -> Result[PhoneLocation]:
        """查询手机号归属地"""
```

### 2. Result[T]

```python
@dataclass
class Result(Generic[T]):
    success: bool                           # 是否成功
    data: Optional[T] = None                # 成功时的数据
    error_code: Optional[ErrorCode] = None  # 失败时的错误码
    error_message: Optional[str] = None     # 失败时的错误信息
    metadata: Dict[str, Any] = {}           # 扩展字段
```

### 3. ErrorCode

```python
class ErrorCode(Enum):
    # 输入错误（不可重试）
    INVALID_PARAMETER     # 参数不合法（包括格式、类型、值等）
    MISSING_PARAMETER     # 缺少必需参数
    
    # 认证错误（不可重试）
    AUTH_FAILED           # 认证失败
    PERMISSION_DENIED     # 权限不足
    CREDENTIALS_INVALID   # 凭证无效
    
    # 资源限制（可重试）
    RATE_LIMITED          # 请求频率超限
    QUOTA_EXCEEDED        # 配额耗尽
    
    # 超时错误（可重试）
    TIMEOUT               # 请求超时
    
    # 服务状态（可重试）
    SERVICE_UNAVAILABLE   # 服务不可用
    PARTIAL_FAILURE       # 部分功能不可用
```

---

## 💡 使用场景

### 场景1：本地调用

```python
from phoneLocation.v2 import PhoneLocationService

service = PhoneLocationService(api_key="key")
result = service.query("13800138000")

if result.success:
    print(result.data.city)
else:
    if result.is_retryable():
        # 重试逻辑
        pass
    else:
        # 修正参数
        pass
```

### 场景2：HTTP 接口

```python
from flask import Flask, jsonify
from phoneLocation.v2 import PhoneLocationService

app = Flask(__name__)
service = PhoneLocationService(api_key="key")

@app.post("/api/query")
def query():
    result = service.query(request.json["phone"])
    # ✅ 直接返回，无需手动映射
    return jsonify(result.to_dict()), result.to_http_status()
```

---

## 📚 文档导航

### 新手入门
1. **[USAGE_EXAMPLE.md](USAGE_EXAMPLE.md)** ⭐ 必看
   - 8 个实用场景示例
   - 从基础到高级用法
   - 测试代码示例

### 设计理解
2. **[V1_VS_V2_COMPARISON.md](V1_VS_V2_COMPARISON.md)**
   - V1 和 V2 的详细对比
   - 适用场景分析
   - 迁移指南

3. **[PROBLEM_BACKGROUND.md](PROBLEM_BACKGROUND.md)**
   - 为什么需要 V2
   - V1 的问题分析

### 深入学习
4. **[RESULT_DESIGN.md](RESULT_DESIGN.md)**
   - Result 类的设计思路
   - 字段说明
   - 使用模式

5. **[ERROR_CODE_DESIGN.md](ERROR_CODE_DESIGN.md)**
   - 错误码的设计原则
   - 完整的错误码列表
   - 映射到 HTTP/gRPC

---

## ✨ 核心特性

### 1. 统一的返回值

```python
# ✅ 成功和失败都返回 Result
result = service.query(phone)  # 总是返回 Result

# ✅ 不需要 try-except
if result.success:
    use(result.data)
else:
    handle_error(result)
```

### 2. 完整的错误信息

```python
result = service.query(phone)

# ✅ 错误码（标准化）
error_code = result.error_code  # ErrorCode.VALIDATION_FAILED

# ✅ 错误消息（详细）
error_msg = result.error_message  # "手机号格式不正确: 138001380"

# ✅ 是否可重试
can_retry = result.is_retryable()  # False
```

### 3. 易于序列化

```python
result = service.query(phone)

# ✅ 转换为字典
result_dict = result.to_dict()
# {
#   "success": true,
#   "data": {...},
#   "error_code": null,
#   ...
# }

# ✅ 序列化为 JSON
import json
json_str = json.dumps(result_dict)
```

### 4. 协议无关

```python
# ✅ 可以映射到 HTTP
http_status = result.to_http_status()  # 200, 400, 429, 503...

# ✅ 可以映射到 gRPC
# grpc_code = result.to_grpc_code()

# ✅ 可以映射到任何协议
```

---

## 🆚 V1 vs V2 选择

### 选择 V1 的场景
- ✅ 单体应用（所有代码在同一进程）
- ✅ 只有本地调用
- ✅ 团队熟悉 Python 异常处理

### 选择 V2 的场景 ⭐
- ✅ 微服务架构
- ✅ 需要通过 HTTP/gRPC 暴露接口
- ✅ 需要在不同语言/平台间传递错误
- ✅ 需要完整保留错误信息

**建议**：如果你的服务需要通过网络暴露，选择 V2。

---

## 🔧 开发状态

| 组件 | 状态 | 说明 |
|-----|------|------|
| **错误码** | ✅ 完成 | ErrorCode 枚举（9个错误码） |
| **Result 类** | ✅ 完成 | 通用返回值类 |
| **数据模型** | ✅ 完成 | PhoneLocation、CarrierType |
| **Service 接口** | ✅ 声明 | 接口已定义，实现待填充 |
| **文档** | ✅ 完成 | 完整的设计文档和使用示例 |
| **测试** | ⏳ 待完成 | 单元测试待添加 |
| **实现** | ⏳ 待完成 | 远程 API 调用逻辑待实现 |

---

## 📝 TODO

- [ ] 实现 `PhoneLocationService.query()` 的远程 API 调用逻辑
- [ ] 添加完整的单元测试
- [ ] 添加集成测试
- [ ] 提供 HTTP/gRPC 接口示例
- [ ] 性能测试和优化

---

## 📖 学习路径

### 第一步：快速上手（5 分钟）
阅读本文档的"快速开始"部分，运行第一个示例。

### 第二步：学习使用（20 分钟）
阅读 [USAGE_EXAMPLE.md](USAGE_EXAMPLE.md)，了解 8 个实用场景。

### 第三步：理解设计（30 分钟）
阅读 [V1_VS_V2_COMPARISON.md](V1_VS_V2_COMPARISON.md)，理解为什么这样设计。

### 第四步：深入学习（1 小时）
阅读 [RESULT_DESIGN.md](RESULT_DESIGN.md) 和 [ERROR_CODE_DESIGN.md](ERROR_CODE_DESIGN.md)。

---

## 🤝 与 V1 对比

详见 [V1_VS_V2_COMPARISON.md](V1_VS_V2_COMPARISON.md)

**一句话总结**：
- V1：适合本地调用，使用 Python 异常机制
- V2：适合本地和远程调用，使用 Result 返回值

---

## 📞 反馈

如果你发现任何问题或有改进建议，欢迎反馈！

---

**版本**: V2.3.0  
**状态**: 接口设计完成，实现待填充  
**最后更新**: 2024-11-12  
**变更**: 
- V2.3.0: HTTP 状态码映射移至 ErrorCode，优化代码结构
- V2.2.0: 重构代码，合并 ErrorType 和 ErrorCode 为单一枚举类
- V2.1.0: 简化输入错误码，优化服务降级错误码

