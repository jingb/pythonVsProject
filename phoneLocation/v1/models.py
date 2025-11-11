"""数据模型定义"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class CarrierType(Enum):
    """运营商类型"""
    CHINA_MOBILE = "中国移动"
    CHINA_UNICOM = "中国联通"
    CHINA_TELECOM = "中国电信"
    UNKNOWN = "未知"


@dataclass
class PhoneQueryRequest:
    """手机号查询请求参数
    
    Attributes:
        phone_number: 手机号码，11位数字字符串（必填）
        timeout: 请求超时时间（秒），默认10秒
    """
    phone_number: str
    timeout: int = 10
    
    def __post_init__(self):
        """参数基本校验"""
        if not self.phone_number:
            raise ValueError("phone_number不能为空")
        if self.timeout <= 0:
            raise ValueError("timeout必须大于0")


@dataclass
class PhoneLocation:
    """手机号归属地信息
    
    Attributes:
        phone_number: 查询的手机号码
        province: 省份，如"北京市"、"广东省"
        city: 城市，如"北京市"、"深圳市"
        carrier: 运营商类型
        is_valid: 号码是否有效（是否为已启用的号段）
    """
    phone_number: str
    province: str
    city: str
    carrier: CarrierType
    is_valid: bool = True
    
    def __str__(self):
        return f"{self.phone_number} - {self.province} {self.city} {self.carrier.value}"

