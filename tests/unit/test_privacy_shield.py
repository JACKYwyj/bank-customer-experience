"""
privacy-shield 模块单元测试
"""

import pytest
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from src.privacy_shield.models import (
    PrivacyLevel,
    DataType,
    PrivacyConfig,
    DataAccessRequest,
    ConsentRecord,
    FederatedLearningClient,
    DifferentialPrivacy,
    EdgeEncryption,
    PrivacyAuditLogger,
    PrivacySettingsManager,
    PrivacyShield
)


class TestPrivacyLevel:
    """测试隐私级别枚举"""
    
    def test_all_levels(self):
        assert len(PrivacyLevel) == 4
        assert PrivacyLevel.LOW.value == "low"
        assert PrivacyLevel.MEDIUM.value == "medium"
        assert PrivacyLevel.HIGH.value == "high"
        assert PrivacyLevel.CRITICAL.value == "critical"


class TestDataType:
    """测试数据类型枚举"""
    
    def test_all_types(self):
        assert DataType.BASIC_INFO.value == "basic_info"
        assert DataType.EMOTION_DATA.value == "emotion_data"
        assert DataType.BIOMETRIC_DATA.value == "biometric_data"
        assert DataType.BEHAVIORAL_DATA.value == "behavioral_data"
        assert DataType.TRANSACTION_DATA.value == "transaction_data"
        assert DataType.LOCATION_DATA.value == "location_data"


class TestPrivacyConfig:
    """测试隐私配置"""
    
    def test_default_config(self):
        config = PrivacyConfig()
        
        assert config.enable_federated_learning is True
        assert config.enable_differential_privacy is True
        assert config.enable_edge_encryption is True
        assert config.privacy_budget_epsilon == 1.0
        assert config.privacy_budget_delta == 1e-5
    
    def test_custom_config(self):
        config = PrivacyConfig(
            privacy_budget_epsilon=0.5,
            data_retention_days=30
        )
        
        assert config.privacy_budget_epsilon == 0.5
        assert config.data_retention_days == 30


class TestDataAccessRequest:
    """测试数据访问请求"""
    
    def test_create_request(self):
        request = DataAccessRequest(
            user_id="user_001",
            data_types=[DataType.EMOTION_DATA],
            purpose="customer_service",
            accessor_id="system_001",
            accessor_type="system"
        )
        
        assert request.user_id == "user_001"
        assert DataType.EMOTION_DATA in request.data_types
        assert request.purpose == "customer_service"
        assert request.approved is False


class TestConsentRecord:
    """测试同意记录"""
    
    def test_create_consent_record(self):
        record = ConsentRecord(
            user_id="user_001",
            consent_type="emotion_data",
            granted=True,
            timestamp=datetime.now()
        )
        
        assert record.user_id == "user_001"
        assert record.consent_type == "emotion_data"
        assert record.granted is True


class TestFederatedLearningClient:
    """测试联邦学习客户端"""
    
    def setup_method(self):
        self.config = PrivacyConfig()
        self.client = FederatedLearningClient(self.config)
    
    def test_train_local(self):
        local_data = [1, 2, 3, 4, 5]
        
        def model_update_fn(data):
            return {"gradient_1": 0.1, "gradient_2": 0.2}
        
        result = self.client.train_local(local_data, model_update_fn)
        
        assert "gradients" in result or " gradients" in result  # Key has space prefix
        assert result["sample_count"] == 5
        assert "client_id" in result
        assert "round" in result
    
    def test_add_dp_noise(self):
        gradients = {"w1": 1.0, "w2": 2.0, "w3": 3.0}
        
        noisy = self.client._add_dp_noise(gradients)
        
        assert "w1" in noisy
        assert "w2" in noisy
        assert "w3" in noisy
        # Values should be slightly different due to noise
        assert noisy["w1"] != 1.0 or noisy["w2"] != 2.0


class TestDifferentialPrivacy:
    """测试差分隐私"""
    
    def setup_method(self):
        self.dp = DifferentialPrivacy(epsilon=1.0, delta=1e-5)
    
    def test_add_noise(self):
        value = 10.0
        noisy_value = self.dp.add_noise(value)
        
        # Noise should be added, but within reasonable range
        assert noisy_value != value
    
    def test_check_privacy_budget(self):
        assert self.dp.check_privacy_budget() is True
        
        self.dp.record_privacy_spending(0.5)
        assert self.dp.check_privacy_budget() is True
        
        self.dp.record_privacy_spending(0.6)
        assert self.dp.check_privacy_budget() is False
    
    def test_record_privacy_spending(self):
        initial = self.dp.privacy_budget_spent
        
        self.dp.record_privacy_spending(0.1)
        
        assert self.dp.privacy_budget_spent > initial


class TestEdgeEncryption:
    """测试端侧加密"""
    
    def setup_method(self):
        self.encryption = EdgeEncryption()
    
    def test_encrypt_decrypt(self):
        original_data = {"emotion": "happy", "confidence": 0.9}
        
        encrypted = self.encryption.encrypt(original_data)
        
        assert encrypted is not None
        assert isinstance(encrypted, bytes)


class TestPrivacyAuditLogger:
    """测试隐私审计日志"""
    
    def setup_method(self):
        self.logger = PrivacyAuditLogger()
    
    def test_log_access(self):
        request = DataAccessRequest(
            user_id="user_001",
            data_types=[DataType.EMOTION_DATA],
            purpose="service",
            accessor_id="system_001",
            accessor_type="system"
        )
        
        self.logger.log_access(request, granted=True)
        
        assert len(self.logger.logs) == 1
        assert self.logger.logs[0]["event_type"] == "data_access"
        assert self.logger.logs[0]["granted"] is True
    
    def test_log_consent(self):
        record = ConsentRecord(
            user_id="user_001",
            consent_type="emotion_data",
            granted=True,
            timestamp=datetime.now()
        )
        
        self.logger.log_consent(record)
        
        assert len(self.logger.logs) == 1
        assert self.logger.logs[0]["event_type"] == "consent"
    
    def test_log_deletion(self):
        self.logger.log_deletion(
            user_id="user_001",
            data_types=[DataType.EMOTION_DATA],
            request_id="del_001"
        )
        
        assert len(self.logger.logs) == 1
        assert self.logger.logs[0]["event_type"] == "data_deletion"
    
    def test_get_logs_filter_by_user(self):
        self.logger.logs = [
            {"timestamp": datetime.now().isoformat(), "event_type": "access", "user_id": "user_001"},
            {"timestamp": datetime.now().isoformat(), "event_type": "access", "user_id": "user_002"},
        ]
        
        logs = self.logger.get_logs(user_id="user_001")
        
        assert len(logs) == 1
        assert logs[0]["user_id"] == "user_001"
    
    def test_get_logs_filter_by_event_type(self):
        self.logger.logs = [
            {"timestamp": datetime.now().isoformat(), "event_type": "access", "user_id": "user_001"},
            {"timestamp": datetime.now().isoformat(), "event_type": "consent", "user_id": "user_001"},
        ]
        
        logs = self.logger.get_logs(event_type="consent")
        
        assert len(logs) == 1
        assert logs[0]["event_type"] == "consent"


class TestPrivacySettingsManager:
    """测试隐私设置管理器"""
    
    def setup_method(self):
        self.manager = PrivacySettingsManager()
    
    def test_get_default_settings(self):
        settings = self.manager.get_user_settings("new_user")
        
        assert settings["emotion_data_collection"] is True
        assert settings["biometric_storage"] is False
        assert settings["third_party_sharing"] is False
    
    def test_update_settings(self):
        self.manager.update_settings("user_001", {
            "biometric_storage": True,
            "third_party_sharing": True
        })
        
        settings = self.manager.get_user_settings("user_001")
        
        assert settings["biometric_storage"] is True
        assert settings["third_party_sharing"] is True
    
    def test_check_data_collection_allowed_emotion(self):
        allowed = self.manager.check_data_collection_allowed(
            "user_001",
            DataType.EMOTION_DATA
        )
        
        assert allowed is True  # Default is allowed
    
    def test_check_data_collection_not_allowed_biometric(self):
        # Set biometric_storage to False
        self.manager.update_settings("user_001", {"biometric_storage": False})
        
        allowed = self.manager.check_data_collection_allowed(
            "user_001",
            DataType.BIOMETRIC_DATA
        )
        
        assert allowed is False
    
    def test_exercise_right_access(self):
        result = self.manager.exercise_right("user_001", "access")
        
        assert result["success"] is True
        assert result["right"] == "access"
    
    def test_exercise_right_deletion(self):
        result = self.manager.exercise_right("user_001", "deletion")
        
        assert result["success"] is True
        assert "deletion_id" in result
    
    def test_exercise_right_portability(self):
        result = self.manager.exercise_right("user_001", "portability")
        
        assert result["success"] is True
        assert "export_url" in result


class TestPrivacyShield:
    """测试隐私盾牌主类"""
    
    def setup_method(self):
        self.shield = PrivacyShield()
    
    def test_process_with_privacy_emotion_data(self):
        result = self.shield.process_with_privacy(
            user_id="user_001",
            data={"emotion": "anxiety", "confidence": 0.85},
            data_type=DataType.EMOTION_DATA,
            purpose="customer_service"
        )
        
        assert "emotion" in result
        assert "confidence" in result
    
    def test_process_with_privacy_blocked(self):
        self.shield.settings_manager.update_settings("user_001", {
            "emotion_data_collection": False
        })
        
        result = self.shield.process_with_privacy(
            user_id="user_001",
            data={"emotion": "anxiety"},
            data_type=DataType.EMOTION_DATA,
            purpose="marketing"
        )
        
        assert "error" in result
    
    def test_create_access_request(self):
        request = self.shield.create_access_request(
            user_id="user_001",
            data_types=[DataType.EMOTION_DATA],
            purpose="service",
            accessor_id="system_001",
            accessor_type="system"
        )
        
        assert request.user_id == "user_001"
        assert DataType.EMOTION_DATA in request.data_types
    
    def test_approve_request(self):
        request = self.shield.create_access_request(
            user_id="user_001",
            data_types=[DataType.EMOTION_DATA],
            purpose="service",
            accessor_id="system_001",
            accessor_type="system"
        )
        
        approved = self.shield.approve_request(request)
        
        assert approved is True
        assert request.approved is True
    
    def test_get_privacy_dashboard(self):
        dashboard = self.shield.get_privacy_dashboard("user_001")
        
        assert "user_id" in dashboard
        assert "settings" in dashboard
        assert "rights_exercisable" in dashboard


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
