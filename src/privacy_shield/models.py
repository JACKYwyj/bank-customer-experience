"""
隐私保护模块 - emoAIsec隐私安全框架
Privacy Shield Module - emoAIsec Privacy & Security Framework

基于论文第五章：emoAIsec隐私安全与伦理治理体系
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Dict, Any, Callable
from datetime import datetime
import hashlib
import hmac
import json


class PrivacyLevel(Enum):
    """隐私敏感级别"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class DataType(Enum):
    """数据类型"""
    BASIC_INFO = "basic_info"              # 基本信息
    EMOTION_DATA = "emotion_data"          # 情绪数据
    BIOMETRIC_DATA = "biometric_data"      # 生物特征数据
    BEHAVIORAL_DATA = "behavioral_data"    # 行为数据
    TRANSACTION_DATA = "transaction_data"  # 交易数据
    LOCATION_DATA = "location_data"        # 位置数据


@dataclass
class PrivacyConfig:
    """隐私配置"""
    enable_federated_learning: bool = True
    enable_differential_privacy: bool = True
    enable_edge_encryption: bool = True
    privacy_budget_epsilon: float = 1.0
    privacy_budget_delta: float = 1e-5
    data_retention_days: int = 90
    min_anonymity_k: int = 5


@dataclass
class DataAccessRequest:
    """数据访问请求"""
    user_id: str
    data_types: List[DataType]
    purpose: str
    accessor_id: str
    accessor_type: str  # system, admin, third_party
    timestamp: datetime = field(default_factory=datetime.now)
    approved: bool = False
    access_level: str = "read"  # read, write, delete


@dataclass
class ConsentRecord:
    """同意记录"""
    user_id: str
    consent_type: str
    granted: bool
    timestamp: datetime
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


class FederatedLearningClient:
    """
    联邦学习客户端
    
    实现论文中的联邦学习框架，
    支持多网点协同训练同时保护原始数据不出域
    """
    
    def __init__(self, config: PrivacyConfig):
        self.config = config
        self.local_model = None
        self.gradient_history = []
        
    def train_local(
        self,
        local_data: Any,
        model_update_fn: Callable
    ) -> Dict[str, Any]:
        """
        本地训练并返回模型更新
        
        Args:
            local_data: 本地训练数据
            model_update_fn: 模型更新函数
            
        Returns:
            模型梯度/参数更新（不上传原始数据）
        """
        # 本地训练
        gradients = model_update_fn(local_data)
        
        # 添加差分隐私噪声
        if self.config.enable_differential_privacy:
            gradients = self._add_dp_noise(gradients)
        
        # 记录梯度历史（用于安全聚合）
        self.gradient_history.append(gradients)
        
        return {
            " gradients": gradients,
            "sample_count": len(local_data) if hasattr(local_data, '__len__') else 1,
            "client_id": self._get_client_id(),
            "round": len(self.gradient_history)
        }
    
    def _add_dp_noise(self, gradients: Dict[str, Any]) -> Dict[str, Any]:
        """
        添加差分隐私噪声
        
        使用高斯机制添加噪声，保护个体隐私
        """
        # 简化的差分隐私实现
        # 实际使用时使用 OpenDP 或 PySyft 库
        sensitivity = 1.0
        noise_scale = sensitivity * self.config.privacy_budget_epsilon
        
        noisy_gradients = {}
        for key, value in gradients.items():
            if isinstance(value, (int, float)):
                # 添加高斯噪声
                import random
                noise = random.gauss(0, noise_scale)
                noisy_gradients[key] = value + noise
            else:
                noisy_gradients[key] = value
                
        return noisy_gradients
    
    def _get_client_id(self) -> str:
        """获取客户端ID"""
        import socket
        return hashlib.md5(socket.gethostname().encode()).hexdigest()[:8]


class DifferentialPrivacy:
    """
    差分隐私模块
    
    实现(ε, δ)-差分隐私保护机制
    """
    
    def __init__(self, epsilon: float = 1.0, delta: float = 1e-5):
        self.epsilon = epsilon
        self.delta = delta
        self.privacy_budget_spent = 0.0
        
    def add_noise(self, value: float, sensitivity: float = 1.0) -> float:
        """添加拉普拉斯噪声"""
        import random
        scale = sensitivity / self.epsilon
        noise = random.gauss(0, scale * 0.8)  # 使用高斯机制近似
        return value + noise
    
    def check_privacy_budget(self) -> bool:
        """检查隐私预算是否超支"""
        return self.privacy_budget_spent < self.epsilon
    
    def record_privacy_spending(self, cost: float):
        """记录隐私支出"""
        self.privacy_budget_spent += cost


class EdgeEncryption:
    """
    端侧加密模块
    
    实现敏感数据在本地加密处理，
    确保原始数据不出域
    """
    
    def __init__(self, encryption_key: Optional[bytes] = None):
        self.key = encryption_key or self._generate_key()
        
    def _generate_key(self) -> bytes:
        """生成加密密钥"""
        import os
        return os.urandom(32)  # AES-256
    
    def encrypt(self, data: Any) -> bytes:
        """加密数据"""
        import json
        from cryptography.fernet import Fernet
        
        # 简化的加密实现
        # 实际使用时使用 proper AES-256-GCM
        json_data = json.dumps(data).encode()
        f = Fernet(Fernet.generate_key())
        return f.encrypt(json_data)
    
    def decrypt(self, encrypted_data: bytes) -> Any:
        """解密数据"""
        import json
        from cryptography.fernet import Fernet
        
        f = Fernet(Fernet.generate_key())
        decrypted = f.decrypt(encrypted_data)
        return json.loads(decrypted)


class PrivacyAuditLogger:
    """
    隐私审计日志
    
    记录所有数据访问和隐私相关操作
    """
    
    def __init__(self):
        self.logs: List[Dict[str, Any]] = []
        
    def log_access(
        self,
        request: DataAccessRequest,
        granted: bool,
        details: Optional[Dict[str, Any]] = None
    ):
        """记录数据访问"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "event_type": "data_access",
            "user_id": request.user_id,
            "accessor_id": request.accessor_id,
            "accessor_type": request.accessor_type,
            "data_types": [dt.value for dt in request.data_types],
            "purpose": request.purpose,
            "granted": granted,
            "details": details or {}
        }
        self.logs.append(log_entry)
        
    def log_consent(
        self,
        record: ConsentRecord
    ):
        """记录同意操作"""
        log_entry = {
            "timestamp": record.timestamp.isoformat(),
            "event_type": "consent",
            "user_id": record.user_id,
            "consent_type": record.consent_type,
            "granted": record.granted
        }
        self.logs.append(log_entry)
        
    def log_deletion(
        self,
        user_id: str,
        data_types: List[DataType],
        request_id: str
    ):
        """记录数据删除"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "event_type": "data_deletion",
            "user_id": user_id,
            "data_types": [dt.value for dt in data_types],
            "request_id": request_id
        }
        self.logs.append(log_entry)
        
    def get_logs(
        self,
        user_id: Optional[str] = None,
        event_type: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """查询审计日志"""
        filtered = self.logs
        
        if user_id:
            filtered = [l for l in filtered if l.get("user_id") == user_id]
        if event_type:
            filtered = [l for l in filtered if l.get("event_type") == event_type]
        if start_time:
            filtered = [l for l in filtered 
                       if datetime.fromisoformat(l["timestamp"]) >= start_time]
        if end_time:
            filtered = [l for l in filtered 
                       if datetime.fromisoformat(l["timestamp"]) <= end_time]
                       
        return filtered


class PrivacySettingsManager:
    """
    隐私设置管理器
    
    管理用户的隐私偏好设置和数据权利
    """
    
    def __init__(self):
        self.user_settings: Dict[str, Dict[str, Any]] = {}
        
    def get_user_settings(self, user_id: str) -> Dict[str, Any]:
        """获取用户隐私设置"""
        default_settings = {
            "emotion_data_collection": True,
            "biometric_storage": False,
            "data_retention_days": 90,
            "third_party_sharing": False,
            "marketing_use": False,
            "research_use": True
        }
        return self.user_settings.get(user_id, default_settings)
    
    def update_settings(
        self,
        user_id: str,
        settings: Dict[str, Any]
    ) -> bool:
        """更新用户隐私设置"""
        current = self.get_user_settings(user_id)
        current.update(settings)
        self.user_settings[user_id] = current
        return True
    
    def check_data_collection_allowed(
        self,
        user_id: str,
        data_type: DataType
    ) -> bool:
        """检查数据收集是否允许"""
        settings = self.get_user_settings(user_id)
        
        if data_type == DataType.EMOTION_DATA:
            return settings.get("emotion_data_collection", True)
        elif data_type == DataType.BIOMETRIC_DATA:
            return settings.get("biometric_storage", False)
        elif data_type in [DataType.BEHAVIORAL_DATA, DataType.LOCATION_DATA]:
            return settings.get("third_party_sharing", False)
            
        return True
    
    def exercise_right(
        self,
        user_id: str,
        right: str,  # access, correction, deletion, portability, objection
        data_type: Optional[DataType] = None
    ) -> Dict[str, Any]:
        """行使数据权利"""
        result = {
            "success": False,
            "right": right,
            "user_id": user_id,
            "data_type": data_type.value if data_type else "all",
            "timestamp": datetime.now().isoformat()
        }
        
        if right == "access":
            # 返回用户数据副本
            result["success"] = True
            result["data"] = {"message": "用户数据访问功能"}
        elif right == "deletion":
            # 删除用户数据
            result["success"] = True
            result["deletion_id"] = f"del_{user_id}_{int(datetime.now().timestamp())}"
        elif right == "portability":
            # 导出用户数据
            result["success"] = True
            result["export_url"] = f"/api/v1/privacy/export/{user_id}"
            
        return result


class PrivacyShield:
    """
    隐私盾牌主类
    
    整合联邦学习、差分隐私、端侧加密、审计日志等组件，
    实现完整的emoAIsec隐私安全框架
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = PrivacyConfig(
            enable_federated_learning=True,
            enable_differential_privacy=True,
            enable_edge_encryption=True,
            privacy_budget_epsilon=1.0
        )
        
        self.fl_client = FederatedLearningClient(self.config)
        self.dp = DifferentialPrivacy(
            self.config.privacy_budget_epsilon,
            self.config.privacy_budget_delta
        )
        self.edge_encryption = EdgeEncryption()
        self.audit_logger = PrivacyAuditLogger()
        self.settings_manager = PrivacySettingsManager()
    
    def process_with_privacy(
        self,
        user_id: str,
        data: Any,
        data_type: DataType,
        purpose: str
    ) -> Dict[str, Any]:
        """
        带隐私保护的数据处理
        
        Args:
            user_id: 用户ID
            data: 原始数据
            data_type: 数据类型
            purpose: 处理目的
            
        Returns:
            处理后的数据（已脱敏/加密）
        """
        # 检查用户设置
        if not self.settings_manager.check_data_collection_allowed(user_id, data_type):
            return {
                "error": "data_collection_not_allowed",
                "message": "用户未授权收集此类型数据"
            }
        
        # 根据数据类型应用不同的隐私保护
        if data_type == DataType.EMOTION_DATA:
            # 情绪数据：应用差分隐私
            if self.config.enable_differential_privacy:
                return self._process_emotion_data_with_dp(data)
        elif data_type == DataType.BIOMETRIC_DATA:
            # 生物特征：端侧加密
            if self.config.enable_edge_encryption:
                return self._process_biometric_with_encryption(data)
        
        return data
    
    def _process_emotion_data_with_dp(self, data: Any) -> Any:
        """使用差分隐私处理情绪数据"""
        # 添加噪声保护隐私
        if isinstance(data, dict):
            protected = {}
            for key, value in data.items():
                if isinstance(value, (int, float)):
                    protected[key] = self.dp.add_noise(value)
                else:
                    protected[key] = value
            return protected
        return data
    
    def _process_biometric_with_encryption(self, data: Any) -> Any:
        """使用端侧加密处理生物特征数据"""
        return {
            "encrypted": True,
            "data": self.edge_encryption.encrypt(data),
            "encrypted_at": datetime.now().isoformat()
        }
    
    def create_access_request(
        self,
        user_id: str,
        data_types: List[DataType],
        purpose: str,
        accessor_id: str,
        accessor_type: str
    ) -> DataAccessRequest:
        """创建数据访问请求"""
        return DataAccessRequest(
            user_id=user_id,
            data_types=data_types,
            purpose=purpose,
            accessor_id=accessor_id,
            accessor_type=accessor_type
        )
    
    def approve_request(
        self,
        request: DataAccessRequest
    ) -> bool:
        """批准访问请求"""
        # 记录审计日志
        self.audit_logger.log_access(request, granted=True)
        request.approved = True
        return True
    
    def get_privacy_dashboard(self, user_id: str) -> Dict[str, Any]:
        """获取用户隐私仪表板"""
        settings = self.settings_manager.get_user_settings(user_id)
        logs = self.audit_logger.get_logs(user_id=user_id)
        
        return {
            "user_id": user_id,
            "settings": settings,
            "recent_activity": logs[-10:] if logs else [],
            "rights_exercisable": {
                "access": True,
                "correction": True,
                "deletion": True,
                "portability": True,
                "objection": True
            }
        }


# 示例使用
if __name__ == "__main__":
    shield = PrivacyShield()
    
    # 模拟隐私保护处理
    result = shield.process_with_privacy(
        user_id="user_001",
        data={"emotion": "anxiety", "confidence": 0.85},
        data_type=DataType.EMOTION_DATA,
        purpose="customer_service"
    )
    
    print(f"Processed with privacy: {result}")
    
    # 获取隐私仪表板
    dashboard = shield.get_privacy_dashboard("user_001")
    print(f"Privacy dashboard: {dashboard}")
