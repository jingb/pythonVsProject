"""异常定义"""

from typing import Optional


class PhoneAPIException(Exception):
    """API异常基类
    
    所有API相关异常的父类，可用于统一捕获所有API异常
    """
    def __init__(self, message: str, error_code: Optional[str] = None):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)
    
    def is_retryable(self) -> bool:
        """判断该异常是否适合重试
        
        Returns:
            bool: True表示可以重试，False表示重试无意义
        """
        return False


# ========== 客户端错误（调用方的问题，不应重试）==========

class ClientError(PhoneAPIException):
    """客户端错误基类
    
    表示调用方传入的参数或使用方式有问题
    这类错误不应该重试，而应该修正参数或调用方式
    """
    pass


class InvalidPhoneNumberError(ClientError):
    """手机号不合法
    
    场景：
    - 手机号格式错误（不是11位数字）
    - 手机号为空或None
    - 号段不存在
    
    处理建议：检查并修正手机号，不要重试
    """
    pass


class InvalidParameterError(ClientError):
    """请求参数不合法
    
    场景：
    - timeout等参数值不合理
    - 必填参数缺失
    
    处理建议：检查并修正参数，不要重试
    """
    pass


class AuthenticationError(ClientError):
    """认证失败
    
    场景：
    - API密钥错误或已失效
    - 权限不足
    - 账户已欠费
    
    处理建议：检查API密钥配置，联系服务商，不要重试
    """
    pass


# ========== 服务端临时错误（可重试）==========

class RetryableError(PhoneAPIException):
    """可重试错误基类
    
    表示这是临时性问题，稍后重试可能会成功
    """
    def is_retryable(self) -> bool:
        return True


class RateLimitExceededError(RetryableError):
    """请求频率超限
    
    场景：
    - 短时间内请求次数过多
    - 触发了服务提供方的限流策略
    
    Attributes:
        retry_after: 建议多少秒后重试（如果服务方提供了该信息）
    
    处理建议：
    - 等待一段时间后重试
    - 优先使用retry_after指定的时间
    - 实施客户端限流策略
    """
    def __init__(self, message: str, retry_after: Optional[int] = None, error_code: Optional[str] = None):
        super().__init__(message, error_code)
        self.retry_after = retry_after


class TimeoutError(RetryableError):
    """请求超时
    
    场景：
    - 在指定时间内未收到响应
    - 可能是暂时性的延迟
    
    处理建议：
    - 可以重试，但注意控制重试次数
    - 考虑适当增加timeout参数
    """
    pass


class ServiceUnavailableError(RetryableError):
    """服务暂时不可用
    
    场景：
    - 服务提供方临时故障
    - 服务正在维护
    - 短暂的过载
    
    Attributes:
        retry_after: 建议多少秒后重试
    
    处理建议：
    - 可以重试，建议使用指数退避策略
    - 如果持续失败，考虑启用降级方案
    """
    def __init__(self, message: str, retry_after: Optional[int] = None, error_code: Optional[str] = None):
        super().__init__(message, error_code)
        self.retry_after = retry_after



