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


class ErrorCode(Enum):
    """通用错误码枚举
    
    每个错误码包含：
    - code: 错误码字符串
    - desc: 错误描述
    - retryable: 是否可重试
    
    分类：
    - 输入错误（调用方问题，不可重试）
    - 认证授权错误（不可重试）
    - 资源限制错误（可重试）
    - 超时错误（可重试）
    - 服务状态错误（可重试）
    """
    
    def __init__(self, code: str, desc: str, retryable: bool):
        """初始化错误码
        
        Args:
            code: 错误码字符串常量
            desc: 错误描述
            retryable: 是否可重试
        """
        self._code = code
        self._desc = desc
        self._retryable = retryable
    
    # ==================== 输入错误（调用方问题，不可重试）====================
    
    INVALID_PARAMETER = (
        "INVALID_PARAMETER",
        "参数不合法（包括格式错误、类型错误、值不合理等）",
        False
    )
    
    MISSING_PARAMETER = (
        "MISSING_PARAMETER",
        "缺少必需参数",
        False
    )
    
    # ==================== 认证授权错误（不可重试）====================
    
    AUTH_FAILED = (
        "AUTH_FAILED",
        "认证失败",
        False
    )
    
    PERMISSION_DENIED = (
        "PERMISSION_DENIED",
        "权限不足",
        False
    )
    
    CREDENTIALS_INVALID = (
        "CREDENTIALS_INVALID",
        "凭证无效",
        False
    )
    
    # ==================== 资源限制错误（可重试）====================
    
    RATE_LIMITED = (
        "RATE_LIMITED",
        "请求频率超限",
        True
    )
    
    QUOTA_EXCEEDED = (
        "QUOTA_EXCEEDED",
        "配额耗尽",
        True
    )
    
    # ==================== 超时错误（可重试）====================
    
    TIMEOUT = (
        "TIMEOUT",
        "请求超时",
        True
    )
    
    # ==================== 服务状态错误（可重试）====================
    
    SERVICE_UNAVAILABLE = (
        "SERVICE_UNAVAILABLE",
        "服务不可用",
        True
    )
    
    PARTIAL_FAILURE = (
        "PARTIAL_FAILURE",
        "部分功能降级，无法返回完整数据，调用端自己判断结果是否可用",
        True
    )
    
    # ==================== 属性访问 ====================
    
    @property
    def code(self) -> str:
        """错误码字符串"""
        return self._code
    
    @property
    def desc(self) -> str:
        """错误描述"""
        return self._desc
    
    @property
    def retryable(self) -> bool:
        """是否可重试"""
        return self._retryable
    
    # ==================== 方法 ====================
    
    def to_http_status(self) -> int:
        """转换为 HTTP 状态码（仅用于 HTTP 接口）
        
        Returns:
            int: HTTP 状态码
        """
        # HTTP 状态码映射表
        mapping = {
            ErrorCode.INVALID_PARAMETER: 400,
            ErrorCode.MISSING_PARAMETER: 400,
            ErrorCode.AUTH_FAILED: 401,
            ErrorCode.CREDENTIALS_INVALID: 401,
            ErrorCode.PERMISSION_DENIED: 403,
            ErrorCode.RATE_LIMITED: 429,
            ErrorCode.QUOTA_EXCEEDED: 429,
            ErrorCode.TIMEOUT: 504,
            ErrorCode.SERVICE_UNAVAILABLE: 503,
            ErrorCode.PARTIAL_FAILURE: 206,
        }
        return mapping.get(self, 500)
    
    # ==================== 类方法 ====================
    
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
            if error.code == code:
                return error
        raise ValueError(f"Unknown error code: {code}")


# ==================== 分类查询辅助函数 ====================

def get_all_retryable_errors() -> list[ErrorCode]:
    """获取所有可重试的错误码
    
    Returns:
        list[ErrorCode]: 可重试的错误码列表
    """
    return [error for error in ErrorCode if error.retryable]


def get_all_non_retryable_errors() -> list[ErrorCode]:
    """获取所有不可重试的错误码
    
    Returns:
        list[ErrorCode]: 不可重试的错误码列表
    """
    return [error for error in ErrorCode if not error.retryable]


def get_input_errors() -> list[ErrorCode]:
    """获取所有输入错误
    
    Returns:
        list[ErrorCode]: 输入错误列表
    """
    return [
        ErrorCode.INVALID_PARAMETER,
        ErrorCode.MISSING_PARAMETER,
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
        ErrorCode.PARTIAL_FAILURE,
    ]

