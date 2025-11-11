"""
手机号归属地查询服务 - 生产环境最佳实践

本文件展示了作为调用方如何直接使用 PhoneLocationService。
展示了完整的错误处理、重试策略等最佳实践。

运行方式：
1. 使用 pytest（推荐）：
   cd /home/service/app/pythonVsProject
   pytest phoneLocation/v1/test_service.py -v -s

2. 作为模块运行：
   python -m phoneLocation.v1.test_service
"""

import sys
import time
from pathlib import Path

# 支持直接运行：添加项目根目录到 sys.path
if __name__ == "__main__":
    project_root = Path(__file__).parent.parent.parent
    sys.path.insert(0, str(project_root))

import pytest
from unittest.mock import patch

# 尝试相对导入（用于 pytest），失败则使用绝对导入（用于直接运行）
try:
    from .service import PhoneLocationService
    from .models import PhoneLocation, CarrierType
    from .exceptions import (
        PhoneAPIException,
        ClientError,
        RetryableError,
        InvalidPhoneNumberError,
        RateLimitExceededError,
        TimeoutError,
        ServiceUnavailableError,
    )
except ImportError:
    from phoneLocation.v1.service import PhoneLocationService
    from phoneLocation.v1.models import PhoneLocation, CarrierType
    from phoneLocation.v1.exceptions import (
        PhoneAPIException,
        ClientError,
        RetryableError,
        InvalidPhoneNumberError,
        RateLimitExceededError,
        TimeoutError,
        ServiceUnavailableError,
    )


class TestPhoneLocationServiceBestPractice:
    """
    生产环境最佳实践测试
    
    这个测试展示了在真实业务场景下如何直接使用 PhoneLocationService。
    不做任何封装，PhoneLocationService 的 API 已经足够清晰和易用。
    """
    
    @patch.object(PhoneLocationService, 'query')
    def test_production_usage_scenarios(self, mock_query):
        """
        生产环境使用场景（完整最佳实践）
        
        本测试展示了5个真实场景，说明如何正确使用 PhoneLocationService：
        
        1. 基本查询 - 最简单的使用方式
        2. 客户端错误处理 - 不应重试的错误
        3. 智能重试 - 根据 is_retryable() 判断
        4. 尊重限流 - 使用 retry_after 建议
        5. 指数退避 - 处理超时
        """
        
        print("\n========== 生产环境使用场景 ==========\n")
        
        # ===== 场景1：基本查询 =====
        print("=== 场景1：基本查询 ===")
        mock_query.return_value = PhoneLocation(
            phone_number="13800138000",
            province="北京市",
            city="北京市",
            carrier=CarrierType.CHINA_MOBILE,
            is_valid=True
        )
        
        # 直接使用 PhoneLocationService
        service = PhoneLocationService(api_key="test_key", timeout=10)
        
        try:
            location = service.query("13800138000")
            print(f"✅ 查询成功: {location.city}")
            assert location.city == "北京市"
        except PhoneAPIException as e:
            print(f"❌ 查询失败: {e.message}")
            raise
        
        print()
        
        # ===== 场景2：客户端错误处理（不应重试）=====
        print("=== 场景2：客户端错误处理 ===")
        mock_query.side_effect = InvalidPhoneNumberError("手机号格式不正确")
        
        try:
            location = service.query("invalid")
            print("❌ 不应该执行到这里")
            assert False
        except ClientError as e:
            # ClientError 表示这是调用方的问题，不应该重试
            print(f"✅ 正确捕获客户端错误: {e.message}")
            print(f"   is_retryable: {e.is_retryable()}")  # False
            assert not e.is_retryable()
        
        print()
        
        # ===== 场景3：智能重试（根据 is_retryable() 判断）=====
        print("=== 场景3：智能重试 ===")
        
        # 第一次超时，第二次成功
        mock_query.side_effect = [
            TimeoutError("第一次超时"),
            PhoneLocation("13800138000", "北京市", "北京市", CarrierType.CHINA_MOBILE, True)
        ]
        
        max_retries = 3
        retry_count = 0
        
        for attempt in range(max_retries):
            try:
                location = service.query("13800138000")
                print(f"✅ 重试 {retry_count} 次后成功")
                assert location.city == "北京市"
                break
            except PhoneAPIException as e:
                # 根据 is_retryable() 判断是否重试
                if e.is_retryable() and attempt < max_retries - 1:
                    print(f"   第 {attempt + 1} 次失败: {e.message}，准备重试")
                    retry_count += 1
                    time.sleep(0.1)  # 实际使用时应该用指数退避
                    continue
                else:
                    print(f"❌ 不可重试或达到最大重试次数")
                    raise
        
        print()
        
        # ===== 场景4：尊重限流建议（使用 retry_after）=====
        print("=== 场景4：尊重限流建议 ===")
        
        # 第一次被限流，第二次成功
        mock_query.side_effect = [
            RateLimitExceededError("请求过于频繁", retry_after=1),
            PhoneLocation("13800138000", "北京市", "北京市", CarrierType.CHINA_MOBILE, True)
        ]
        
        try:
            location = service.query("13800138000")
        except RateLimitExceededError as e:
            # 获取服务方建议的等待时间
            wait_time = e.retry_after
            print(f"   被限流，建议等待 {wait_time} 秒")
            
            # 实际使用时应该等待
            # time.sleep(wait_time)
            time.sleep(0.1)  # 测试时缩短
            
            # 重试
            location = service.query("13800138000")
            print(f"✅ 等待后重试成功")
            assert location.city == "北京市"
        
        print()
        
        # ===== 场景5：指数退避策略（处理超时）=====
        print("=== 场景5：指数退避策略 ===")
        
        # 模拟3次超时后成功
        mock_query.side_effect = [
            TimeoutError("超时1"),
            TimeoutError("超时2"),
            TimeoutError("超时3"),
            PhoneLocation("13800138000", "北京市", "北京市", CarrierType.CHINA_MOBILE, True)
        ]
        
        max_retries = 5
        for attempt in range(max_retries):
            try:
                location = service.query("13800138000")
                print(f"✅ 第 {attempt + 1} 次尝试成功")
                break
            except TimeoutError:
                if attempt < max_retries - 1:
                    # 指数退避：等待时间翻倍
                    wait_time = 2 ** attempt  # 1秒、2秒、4秒...
                    print(f"   第 {attempt + 1} 次超时，等待 {wait_time} 秒后重试")
                    time.sleep(0.1)  # 测试时缩短
                    continue
                else:
                    print(f"❌ 达到最大重试次数")
                    raise
        
        print()
        print("========== 所有场景测试通过 ==========\n")
    
    @patch.object(PhoneLocationService, 'query')
    def test_exception_classification(self, mock_query):
        """
        异常分类处理最佳实践
        
        PhoneLocationService 的异常体系非常清晰：
        - ClientError：调用方的问题，不应重试
        - RetryableError：临时问题，可以重试
        """
        print("\n========== 异常分类处理 ==========\n")
        
        service = PhoneLocationService(api_key="test_key")
        
        # 方式1：详细处理每种异常
        print("=== 方式1：详细处理 ===")
        mock_query.side_effect = InvalidPhoneNumberError("格式错误")
        
        try:
            service.query("invalid")
        except InvalidPhoneNumberError as e:
            print(f"✅ 捕获 InvalidPhoneNumberError: {e.message}")
        except RateLimitExceededError as e:
            print(f"   捕获 RateLimitExceededError")
        except TimeoutError as e:
            print(f"   捕获 TimeoutError")
        
        # 方式2：按类别处理
        print("\n=== 方式2：按类别处理 ===")
        mock_query.side_effect = TimeoutError("超时")
        
        try:
            service.query("13800138000")
        except ClientError:
            print(f"   这是客户端错误，不重试")
        except RetryableError as e:
            print(f"✅ 捕获可重试错误: {e.message}")
        
        # 方式3：使用 is_retryable() 判断
        print("\n=== 方式3：使用 is_retryable() ===")
        mock_query.side_effect = ServiceUnavailableError("服务不可用")
        
        try:
            service.query("13800138000")
        except PhoneAPIException as e:
            if e.is_retryable():
                print(f"✅ 可重试错误: {e.message}")
            else:
                print(f"   不可重试错误: {e.message}")
        
        print("\n========== 异常处理测试完成 ==========\n")


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v", "-s"])
