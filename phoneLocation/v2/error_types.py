"""
通用错误类型定义

这个模块定义了通用的错误码枚举，设计原则：
1. 通用性：不绑定具体业务
2. 协议无关：不使用 HTTP 状态码（4xx、5xx）
3. 语义化：使用清晰的字符串常量
4. 可扩展：易于添加新的错误类型
5. 结构化：包含错误码、描述和是否可重试
"""

from enum import Enum
from dataclasses import dataclass


@dataclass(frozen=True)
class ErrorType:
    """错误类型（包含码、描述和重试信息）
    
    Attributes:
        code: 错误码（字符串常量）
        message: 错误描述
        retryable: 是否可重试
    """
    code: str
    message: str
    retryable: bool


class ErrorCode(Enum):
    """通用错误码枚举
    
    分类：
    - 输入错误（调用方问题，不可重试）
    - 认证授权错误（不可重试）
    - 资源限制错误（可重试）
    - 超时错误（可重试）
    - 服务状态错误（可重试）
    """
    
    # ==================== 输入错误（调用方问题，不可重试）====================
    
    INVALID_INPUT = ErrorType(
        code="INVALID_INPUT",
        message="输入参数不合法",
        retryable=False
    )
    
    VALIDATION_FAILED = ErrorType(
        code="VALIDATION_FAILED",
        message="参数校验失败",
        retryable=False
    )
    
    MISSING_REQUIRED = ErrorType(
        code="MISSING_REQUIRED",
        message="缺少必需参数",
        retryable=False
    )
    
    # ==================== 认证授权错误（不可重试）====================
    
    AUTH_FAILED = ErrorType(
        code="AUTH_FAILED",
        message="认证失败",
        retryable=False
    )
    
    PERMISSION_DENIED = ErrorType(
        code="PERMISSION_DENIED",
        message="权限不足",
        retryable=False
    )
    
    CREDENTIALS_INVALID = ErrorType(
        code="CREDENTIALS_INVALID",
        message="凭证无效",
        retryable=False
    )
    
    # ==================== 资源限制错误（可重试）====================
    
    RATE_LIMITED = ErrorType(
        code="RATE_LIMITED",
        message="请求频率超限",
        retryable=True
    )
    
    QUOTA_EXCEEDED = ErrorType(
        code="QUOTA_EXCEEDED",
        message="配额耗尽",
        retryable=True
    )
    
    # ==================== 超时错误（可重试）====================
    
    TIMEOUT = ErrorType(
        code="TIMEOUT",
        message="请求超时",
        retryable=True
    )
    
    # ==================== 服务状态错误（可重试）====================
    
    SERVICE_UNAVAILABLE = ErrorType(
        code="SERVICE_UNAVAILABLE",
        message="服务不可用",
        retryable=True
    )
    
    SERVICE_DEGRADED = ErrorType(
        code="SERVICE_DEGRADED",
        message="服务降级，既效果会差些或者部分字段缺失，调用端自己识别结果是否可用",
        retryable=True
    )
    
    def is_retryable(self) -> bool:
        """判断该错误是否可重试
        
        Returns:
            bool: True 表示可以重试，False 表示不应重试
        """
        return self.value.retryable
    
    def get_code(self) -> str:
        """获取错误码字符串
        
        Returns:
            str: 错误码
        """
        return self.value.code
    
    def get_message(self) -> str:
        """获取错误描述
        
        Returns:
            str: 错误描述
        """
        return self.value.message
    
    @classmethod
    def from_code(cls, code: str) -> 'ErrorCode':
        """根据错误码字符串获取枚举值
        
        Args:
            code: 错误码字符串
            
        Returns:
            ErrorCode: 对应的枚举值
            
        Raises:
            ValueError: 如果找不到对应的错误码
        """
        for error in cls:
            if error.value.code == code:
                return error
        raise ValueError(f"Unknown error code: {code}")


# ==================== 分类查询辅助函数 ====================

def get_all_retryable_errors() -> list[ErrorCode]:
    """获取所有可重试的错误码
    
    Returns:
        list[ErrorCode]: 可重试的错误码列表
    """
    return [error for error in ErrorCode if error.is_retryable()]


def get_all_non_retryable_errors() -> list[ErrorCode]:
    """获取所有不可重试的错误码
    
    Returns:
        list[ErrorCode]: 不可重试的错误码列表
    """
    return [error for error in ErrorCode if not error.is_retryable()]


def get_input_errors() -> list[ErrorCode]:
    """获取所有输入错误
    
    Returns:
        list[ErrorCode]: 输入错误列表
    """
    return [
        ErrorCode.INVALID_INPUT,
        ErrorCode.VALIDATION_FAILED,
        ErrorCode.MISSING_REQUIRED,
    ]


def get_auth_errors() -> list[ErrorCode]:
    """获取所有认证授权错误
    
    Returns:
        list[ErrorCode]: 认证授权错误列表
    """
    return [
        ErrorCode.AUTH_FAILED,
        ErrorCode.PERMISSION_DENIED,
        ErrorCode.CREDENTIALS_INVALID,
    ]


def get_resource_errors() -> list[ErrorCode]:
    """获取所有资源限制错误
    
    Returns:
        list[ErrorCode]: 资源限制错误列表
    """
    return [
        ErrorCode.RATE_LIMITED,
        ErrorCode.QUOTA_EXCEEDED,
    ]


def get_timeout_errors() -> list[ErrorCode]:
    """获取所有超时错误
    
    Returns:
        list[ErrorCode]: 超时错误列表
    """
    return [
        ErrorCode.TIMEOUT,
    ]


def get_service_errors() -> list[ErrorCode]:
    """获取所有服务状态错误
    
    Returns:
        list[ErrorCode]: 服务状态错误列表
    """
    return [
        ErrorCode.SERVICE_UNAVAILABLE,
        ErrorCode.SERVICE_DEGRADED,
    ]

