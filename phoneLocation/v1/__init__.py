"""手机号归属地查询服务 v1

对外接口说明：
- 调用方应该使用 PhoneLocationService 类
- 不要直接使用内部的 client、models 等模块（实现细节可能变更）
"""

# 对外暴露的服务层
from .service import PhoneLocationService

# 对外暴露的数据模型
from .models import PhoneLocation, CarrierType

# 对外暴露的异常体系
from .exceptions import (
    PhoneAPIException,
    ClientError,
    RetryableError,
    InvalidPhoneNumberError,
    InvalidParameterError,
    AuthenticationError,
    RateLimitExceededError,
    TimeoutError,
    ServiceUnavailableError,
)

__version__ = "1.0.0"

# 对外暴露的接口（推荐调用方只使用这些）
__all__ = [
    # ===== 服务层（推荐使用）=====
    "PhoneLocationService",
    
    # ===== 数据模型 =====
    "PhoneLocation",      # 返回结果
    "CarrierType",        # 运营商枚举
    
    # ===== 异常体系 =====
    # 基类
    "PhoneAPIException",
    "ClientError",        # 客户端错误基类（不可重试）
    "RetryableError",     # 可重试错误基类
    
    # 具体异常
    "InvalidPhoneNumberError",      # 手机号不合法
    "InvalidParameterError",        # 参数不合法
    "AuthenticationError",          # 认证失败
    "RateLimitExceededError",       # 频率超限（可重试）
    "TimeoutError",                 # 超时（可重试）
    "ServiceUnavailableError",      # 服务不可用（可重试）
]

