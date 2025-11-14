"""手机号归属地查询服务 V2

V2 改进：
- 使用 Result[PhoneLocation] 作为返回值，不抛异常
- 适合本地调用和远程调用（HTTP/gRPC）
- 错误信息完整，易于序列化
- 使用通用的 ErrorCode 枚举

主要接口：
- PhoneLocationService: 查询服务
- Result: 返回值类
- PhoneLocation: 归属地信息
- CarrierType: 运营商枚举
- ErrorCode: 错误码枚举
"""

from .service import PhoneLocationService
from .result import Result
from .models import PhoneLocation, CarrierType
from .error_types import ErrorCode

__version__ = "2.3.0"

__all__ = [
    # 服务
    "PhoneLocationService",
    
    # 返回值
    "Result",
    
    # 数据模型
    "PhoneLocation",
    "CarrierType",
    
    # 错误类型
    "ErrorCode",
]

