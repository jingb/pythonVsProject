"""手机号归属地查询服务（V2 - 使用 Result 返回值）

这是对外暴露的服务层，调用方应该使用此层的类进行调用。
内部实现细节（如具体使用哪个供应商、如何调用等）对调用方透明。

V2 改进：
- 不抛异常，使用 Result[PhoneLocation] 作为返回值
- 适合本地调用和远程调用（HTTP/gRPC）
- 错误信息完整，易于序列化

注意：此文件当前为接口声明，具体实现待填充。
"""

from typing import Optional
from .models import PhoneLocation, CarrierType
from .result import Result
from .error_types import ErrorCode


class PhoneLocationService:
    """手机号归属地查询服务（V2 版本）
    
    V2 改进：
    - 返回 Result[PhoneLocation] 而不是抛异常
    - 统一的返回值处理，适合本地和远程调用
    - 所有错误信息通过 Result.error() 返回
    
    示例：
        >>> service = PhoneLocationService(api_key="your_key")
        >>> result = service.query("13800138000")
        >>> if result.success:
        ...     print(f"查询成功: {result.data.city}")
        ... else:
        ...     print(f"查询失败: {result.error_message}")
        ...     if result.is_retryable():
        ...         # 可以重试
        ...         pass
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
        if not api_key:
            raise ValueError("api_key 不能为空")
        
        if timeout <= 0:
            raise ValueError("timeout 必须大于 0")
        
        self.api_key = api_key
        self.timeout = timeout
        
        # TODO: 实现初始化逻辑（如创建 HTTP 客户端等）
    
    def query(
        self, 
        phone_number: str, 
        timeout: Optional[int] = None
    ) -> Result[PhoneLocation]:
        """查询手机号归属地
        
        Args:
            phone_number: 手机号码（11位数字字符串）
            timeout: 超时时间（秒），不指定则使用初始化时的默认值
            
        Returns:
            Result[PhoneLocation]: 查询结果，包含以下情况：
            
            成功时 (result.success == True):
                - result.data: PhoneLocation 对象，包含：
                    - phone_number: 查询的手机号
                    - province: 省份
                    - city: 城市
                    - carrier: 运营商（CarrierType枚举）
                    - is_valid: 号码是否有效
                    
            失败时 (result.success == False):
                - result.error_code: ErrorCode 枚举
                - result.error_message: 详细错误信息
                - result.is_retryable(): 是否可重试
                
        错误码说明：
            MISSING_REQUIRED: 手机号为空
                - 场景：phone_number 参数为空或 None
                - 处理：检查并提供手机号，不要重试
                - 可重试：False
                
            VALIDATION_FAILED: 手机号格式不合法
                - 场景：格式错误、号段不存在、长度不对等
                - 处理：检查并修正手机号，不要重试
                - 可重试：False
                
            INVALID_INPUT: 参数不合法
                - 场景：timeout 等参数不合理
                - 处理：检查并修正参数，不要重试
                - 可重试：False
                
            CREDENTIALS_INVALID: API密钥无效
                - 场景：API密钥错误或过期
                - 处理：检查API密钥配置
                - 可重试：False
                
            PERMISSION_DENIED: 权限不足
                - 场景：账户欠费、权限不足
                - 处理：联系服务商，充值或升级权限
                - 可重试：False
                
            RATE_LIMITED: 请求频率超限
                - 场景：请求过于频繁
                - 处理：等待一段时间后重试，或实施客户端限流
                - 可重试：True
                - 建议：可以在 result.metadata 中查看 retry_after
                
            TIMEOUT: 请求超时
                - 场景：指定时间内未收到响应
                - 处理：可以重试，考虑增加timeout值
                - 可重试：True
                
            SERVICE_UNAVAILABLE: 服务暂时不可用
                - 场景：服务临时故障或维护
                - 处理：使用指数退避策略重试
                - 可重试：True
                
            SERVICE_DEGRADED: 服务降级
                - 场景：服务部分功能不可用
                - 处理：检查返回数据是否满足需求，可以重试
                - 可重试：True
                
        示例：
            基本使用：
            >>> result = service.query("13800138000")
            >>> if result.success:
            ...     print(f"城市: {result.data.city}")
            ... else:
            ...     print(f"错误: {result.error_message}")
            
            错误处理：
            >>> result = service.query("invalid")
            >>> if not result.success:
            ...     if result.error_code == ErrorCode.VALIDATION_FAILED:
            ...         print("手机号格式错误")
            ...     elif result.is_retryable():
            ...         print("可以重试")
            ...     else:
            ...         print("不应重试")
        """
        # 参数校验
        if not phone_number:
            return Result.error(
                error_code=ErrorCode.MISSING_REQUIRED,
                error_message="phone_number 参数为空"
            )
        
        # 使用指定的 timeout 或默认值
        actual_timeout = timeout if timeout is not None else self.timeout
        
        if actual_timeout <= 0:
            return Result.error(
                error_code=ErrorCode.INVALID_INPUT,
                error_message=f"timeout 必须大于 0，当前值: {actual_timeout}"
            )
        
        # TODO: 实现查询逻辑
        # 这里是示例代码，实际应该调用远程 API
        
        # 示例：手机号格式校验
        if not self._validate_phone_format(phone_number):
            return Result.error(
                error_code=ErrorCode.VALIDATION_FAILED,
                error_message=f"手机号格式不正确: {phone_number}"
            )
        
        # 示例：调用远程 API（待实现）
        try:
            # location = self._call_remote_api(phone_number, actual_timeout)
            # return Result.success(data=location)
            
            # 临时返回（实际应该调用 API）
            pass
            
        except Exception as e:
            # 根据异常类型返回不同的错误
            # 示例代码，实际应该根据具体的异常类型判断
            return Result.error(
                error_code=ErrorCode.SERVICE_UNAVAILABLE,
                error_message=f"调用远程服务失败: {str(e)}"
            )
    
    def _validate_phone_format(self, phone_number: str) -> bool:
        """校验手机号格式（基本校验）
        
        Args:
            phone_number: 手机号
            
        Returns:
            bool: 格式是否合法
        """
        # 基本校验：11位数字
        if not phone_number.isdigit():
            return False
        
        if len(phone_number) != 11:
            return False
        
        # 第一位必须是1
        if not phone_number.startswith('1'):
            return False
        
        return True

