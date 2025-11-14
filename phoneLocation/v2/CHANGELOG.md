# 变更日志

## V2.3.0 (2024-11-12)

### 🎯 优化：HTTP 状态码映射移至 ErrorCode

#### 变更说明
将 HTTP 状态码映射逻辑从 `Result.to_http_status()` 移至 `ErrorCode.to_http_status()`，让错误码自己管理 HTTP 映射。

#### 优势
- ✅ **职责清晰**：ErrorCode 负责错误码到 HTTP 状态码的转换
- ✅ **易于维护**：新增错误码时，在同一处定义 HTTP 映射
- ✅ **代码简化**：Result.to_http_status() 从 35 行减少到 7 行
- ✅ **不增属性**：使用方法内部映射，不污染 ErrorCode 的属性

#### 修改内容
1. ErrorCode 新增 `to_http_status()` 方法
2. Result.to_http_status() 委托给 ErrorCode.to_http_status()
3. 所有 `.get_xxx()` 方法调用改为属性访问（`.code`, `.desc`, `.retryable`）

---

## V2.2.0 (2024-11-12)

### 🎯 代码重构：合并 ErrorType 和 ErrorCode

#### 变更说明
将 `ErrorType` 和 `ErrorCode` 两个类合并为单一的 `ErrorCode` 枚举类。

#### 重构前（2个类）
```python
@dataclass(frozen=True)
class ErrorType:
    code: str
    message: str
    retryable: bool

class ErrorCode(Enum):
    INVALID_PARAMETER = ErrorType(
        code="INVALID_PARAMETER",
        message="参数不合法",
        retryable=False
    )
```

#### 重构后（1个类）
```python
class ErrorCode(Enum):
    def __init__(self, code: str, message: str, retryable: bool):
        self._code = code
        self._message = message
        self._retryable = retryable
    
    INVALID_PARAMETER = (
        "INVALID_PARAMETER",
        "参数不合法（包括格式错误、类型错误、值不合理等）",
        False
    )
    
    @property
    def code(self) -> str:
        return self._code
```

#### 优势
- ✅ **更简洁**：从 2 个类减少到 1 个类
- ✅ **更直观**：`error.code` 而不是 `error.value.code`
- ✅ **更易维护**：只需维护一个类
- ✅ **类似 Java**：符合其他语言的枚举设计习惯
- ✅ **向后兼容**：保留了 `get_code()`、`is_retryable()` 等方法

#### 影响范围
- ✅ 代码使用方式**完全兼容**，无需修改
- ✅ `ErrorType` 类已移除，不再导出
- ✅ 现在可以直接用 `error.code`、`error.message`、`error.retryable` 访问属性

---

## V2.1.0 (2024-11-12)

### 🎯 错误码优化

#### 简化输入错误码
**之前（3个）**：
- `INVALID_INPUT` - 输入参数不合法
- `VALIDATION_FAILED` - 参数校验失败
- `MISSING_REQUIRED` - 缺少必需参数

**现在（2个）**：
- `INVALID_PARAMETER` - 参数不合法（包括格式错误、类型错误、值不合理等）
- `MISSING_PARAMETER` - 缺少必需参数

**原因**：
- 简化了错误码粒度，避免边界不清晰
- `INVALID_PARAMETER` 涵盖了所有参数不合法的情况
- 更易于使用和理解

#### 重命名服务降级错误
**之前**：
- `SERVICE_DEGRADED` - 服务降级，既效果会差些或者部分字段缺失，调用端自己识别结果是否可用

**现在**：
- `PARTIAL_FAILURE` - 部分功能不可用，无法返回完整数据

**原因**：
- 语义更明确：表示部分功能失败，无法返回完整数据
- 与"降级"概念区分：降级通常是成功但不完美的状态

### 📝 影响范围

**更新的文件**：
1. `error_types.py` - 错误枚举定义
2. `result.py` - HTTP 状态码映射
3. `ERROR_CODE_DESIGN.md` - 错误码设计文档
4. `README.md` - 主文档

**向后兼容性**：
- ⚠️ **不兼容**：旧代码使用 `INVALID_INPUT`、`VALIDATION_FAILED`、`MISSING_REQUIRED` 的地方需要更新
- ⚠️ **不兼容**：使用 `SERVICE_DEGRADED` 的地方需要改为 `PARTIAL_FAILURE`

**迁移指南**：
```python
# 旧代码
ErrorCode.INVALID_INPUT       → ErrorCode.INVALID_PARAMETER
ErrorCode.VALIDATION_FAILED   → ErrorCode.INVALID_PARAMETER
ErrorCode.MISSING_REQUIRED    → ErrorCode.MISSING_PARAMETER
ErrorCode.SERVICE_DEGRADED    → ErrorCode.PARTIAL_FAILURE
```

### 📊 当前错误码总览

共 **9 个错误码**，分为 5 大类：

| 分类 | 错误码 | 可重试 |
|------|--------|--------|
| **输入错误** | INVALID_PARAMETER, MISSING_PARAMETER | ❌ |
| **认证错误** | AUTH_FAILED, PERMISSION_DENIED, CREDENTIALS_INVALID | ❌ |
| **资源限制** | RATE_LIMITED, QUOTA_EXCEEDED | ✅ |
| **超时错误** | TIMEOUT | ✅ |
| **服务状态** | SERVICE_UNAVAILABLE, PARTIAL_FAILURE | ✅ |

---

## V2.0.0 (2024-11-06)

### 🎉 初始版本

- ✅ Result[T] 返回值类
- ✅ ErrorCode 错误枚举（原 10 个错误码）
- ✅ PhoneLocation 数据模型
- ✅ 完整的设计文档
- ⏳ Service 实现待完成


