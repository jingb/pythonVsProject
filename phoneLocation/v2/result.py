"""
通用返回值类

这个模块定义了通用的返回值类 Result，设计原则：
1. 通用性：不绑定具体业务
2. 类型安全：使用泛型支持任意数据类型
3. 易用性：提供便捷的工厂方法
4. 完整性：包含所有必要的错误信息
"""

from typing import TypeVar, Generic, Optional, Any, Dict
from dataclasses import dataclass, field, asdict
from .error_types import ErrorCode


# 定义泛型变量，用于表示成功时返回的数据类型
T = TypeVar('T')


@dataclass
class Result(Generic[T]):
    """通用返回值类
    
    用于封装接口调用的结果，包含成功或失败的所有信息。
    
    Attributes:
        success: 是否成功
        data: 成功时的返回数据（泛型）
        error_code: 失败时的错误码
        error_message: 失败时的详细错误信息
        metadata: 扩展字段，用于存放额外信息（如 request_id、timestamp 等）
    
    Examples:
        成功的结果：
        >>> result = Result.success(data={"city": "北京"})
        >>> if result.success:
        ...     print(result.data)
        
        失败的结果：
        >>> result = Result.error(
        ...     error_code=ErrorCode.INVALID_INPUT,
        ...     error_message="手机号格式不正确"
        ... )
        >>> if not result.success:
        ...     print(result.error_message)
        
    """
    
    # 必需字段
    success: bool
    
    # 成功时有值
    data: Optional[T] = None
    
    # 失败时有值
    error_code: Optional[ErrorCode] = None
    error_message: Optional[str] = None
    
    # 扩展字段
    metadata: Dict[str, Any] = field(default_factory=dict)  # 用于存放额外信息（如 request_id 等）
    
    @classmethod
    def success(
        cls,
        data: T,
        metadata: Optional[Dict[str, Any]] = None
    ) -> 'Result[T]':
        """创建成功的结果
        
        Args:
            data: 返回的数据
            metadata: 可选的元数据
            
        Returns:
            Result[T]: 成功的结果对象
        """
        return cls(
            success=True,
            data=data,
            metadata=metadata or {}
        )
    
    @classmethod
    def error(
        cls,
        error_code: ErrorCode,
        error_message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> 'Result[T]':
        """创建失败的结果
        
        Args:
            error_code: 错误码
            error_message: 详细错误信息（可选，不提供则使用错误码的默认描述）
            metadata: 可选的元数据（可包含 request_id 等信息）
            
        Returns:
            Result[T]: 失败的结果对象
        """
        # 如果没有提供详细错误信息，使用错误码的默认描述
        if error_message is None:
            error_message = error_code.desc
        
        return cls(
            success=False,
            error_code=error_code,
            error_message=error_message,
            metadata=metadata or {}
        )
    
    def is_retryable(self) -> bool:
        """判断该错误是否可重试
        
        Returns:
            bool: True 表示可以重试，False 表示不应重试
                  如果是成功的结果，返回 False
        """
        if self.success:
            return False
        
        if self.error_code is None:
            return False
        
        return self.error_code.retryable
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典（用于序列化）
        
        Returns:
            Dict[str, Any]: 字典表示，可以直接序列化为 JSON
        """
        result_dict = {
            "success": self.success,
        }
        
        # 成功时的字段
        if self.success:
            result_dict["data"] = self.data
        # 失败时的字段
        else:
            if self.error_code:
                result_dict["error_code"] = self.error_code.code
            result_dict["error_message"] = self.error_message
            result_dict["retryable"] = self.is_retryable()
        
        # 元数据（如果有）
        if self.metadata:
            result_dict["metadata"] = self.metadata
        
        return result_dict
    
    def to_http_status(self) -> int:
        """转换为 HTTP 状态码（可选，用于 HTTP 接口）
        
        Returns:
            int: HTTP 状态码
        """
        if self.success:
            return 200
        
        if self.error_code is None:
            return 500
        
        # 委托给错误码的 to_http_status() 方法
        return self.error_code.to_http_status()
    
    def __bool__(self) -> bool:
        """支持布尔判断
        
        Returns:
            bool: success 字段的值
            
        Examples:
            >>> result = Result.success(data="ok")
            >>> if result:  # 等价于 if result.success:
            ...     print("成功")
        """
        return self.success
    
    def __repr__(self) -> str:
        """返回对象的字符串表示
        
        Returns:
            str: 人类可读的字符串表示
        """
        if self.success:
            return f"Result(success=True, data={self.data})"
        else:
            return (
                f"Result(success=False, "
                f"error_code={self.error_code.code if self.error_code else None}, "
                f"error_message={self.error_message})"
            )

