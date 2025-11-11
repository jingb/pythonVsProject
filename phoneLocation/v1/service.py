"""手机号归属地查询服务（对外接口层）

这是对外暴露的服务层，调用方应该使用此层的类进行调用。
内部实现细节（如具体使用哪个供应商、如何调用等）对调用方透明。

注意：此文件当前为接口声明，具体实现待填充。
"""

from typing import Optional
from .models import PhoneLocation, CarrierType
from .exceptions import (
    PhoneAPIException,
    InvalidPhoneNumberError,
    InvalidParameterError,
    AuthenticationError,
    RateLimitExceededError,
    TimeoutError,
    ServiceUnavailableError,
)


class PhoneLocationService:
    """手机号归属地查询服务
    
    这是推荐的对外接口，封装了所有实现细节。
    调用方无需关心底层使用了哪个API供应商。
    """
    
    def __init__(
        self,
        api_key: str,
        timeout: int = 10
    ):
        """初始化手机号归属地查询服务
        
        Args:
            api_key: API密钥（必填）
            timeout: 默认超时时间（秒），默认10秒
                
        Raises:
            ValueError: 当api_key为空时
        """
        # TODO: 实现初始化逻辑
        pass
    
    def query(self, phone_number: str, timeout: Optional[int] = None) -> PhoneLocation:
        """查询手机号归属地
        
        Args:
            phone_number: 手机号码（11位数字字符串）
            timeout: 超时时间（秒），不指定则使用初始化时的默认值
            
        Returns:
            PhoneLocation: 手机号归属地信息，包含：
                - phone_number: 查询的手机号
                - province: 省份
                - city: 城市
                - carrier: 运营商（CarrierType枚举）
                - is_valid: 号码是否有效
            
        Raises:
            InvalidPhoneNumberError: 手机号格式不合法
                - 场景：格式错误、号段不存在
                - 处理：检查并修正手机号，不要重试
                
            InvalidParameterError: 参数不合法
                - 场景：timeout等参数不合理
                - 处理：检查并修正参数，不要重试
                
            AuthenticationError: 认证失败
                - 场景：API密钥错误、权限不足、账户欠费
                - 处理：检查API密钥配置，联系服务商
                
            RateLimitExceededError: 请求频率超限
                - 场景：请求过于频繁
                - 处理：等待retry_after秒后重试，或实施客户端限流
                
            TimeoutError: 请求超时
                - 场景：指定时间内未收到响应
                - 处理：可以重试，考虑增加timeout值
                
            ServiceUnavailableError: 服务暂时不可用
                - 场景：服务临时故障或维护
                - 处理：使用指数退避策略重试
        """
        # TODO: 实现查询逻辑
        pass
