"""
隐私保护服务 - FastAPI服务接口
Privacy Shield Service - FastAPI Endpoints

基于论文第五章：emoAIsec隐私安全与伦理治理体系
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field
import uuid

from .models import (
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


# ============== Pydantic Models ==============

class PrivacySettingsRequest(BaseModel):
    """隐私设置请求"""
    emotion_data_collection: Optional[bool] = None
    biometric_storage: Optional[bool] = None
    data_retention_days: Optional[int] = None
    third_party_sharing: Optional[bool] = None
    marketing_use: Optional[bool] = None
    research_use: Optional[bool] = None


class PrivacySettingsResponse(BaseModel):
    """隐私设置响应"""
    user_id: str
    settings: Dict[str, Any]
    last_updated: str


class DataDeletionRequest(BaseModel):
    """数据删除请求"""
    user_id: str
    data_types: List[str] = Field(..., description="要删除的数据类型")
    reason: Optional[str] = Field(None, description="删除原因")
    request_id: Optional[str] = None


class DataDeletionResponse(BaseModel):
    """数据删除响应"""
    request_id: str
    user_id: str
    data_types: List[str]
    status: str
    scheduled_completion: str
    estimated_time_hours: int


class DataAccessRequestCreate(BaseModel):
    """数据访问请求创建"""
    user_id: str
    data_types: List[str]
    purpose: str
    accessor_id: str
    accessor_type: str = "system"


class DataAccessRequestResponse(BaseModel):
    """数据访问请求响应"""
    request_id: str
    user_id: str
    data_types: List[str]
    purpose: str
    accessor_id: str
    accessor_type: str
    status: str
    created_at: str
    processed_at: Optional[str] = None


class FederatedLearningRequest(BaseModel):
    """联邦学习请求"""
    client_id: str
    round: int
    model_type: str = Field(default="emotion_model", description="模型类型")
    gradient_data: Dict[str, float] = Field(..., description="梯度数据")
    sample_count: int = Field(..., description="样本数量")


class FederatedLearningResponse(BaseModel):
    """联邦学习响应"""
    round: int
    status: str
    aggregated_model: Optional[Dict[str, float]] = None
    next_round_available: bool


class DifferentialPrivacyRequest(BaseModel):
    """差分隐私请求"""
    user_id: str
    data_type: str
    values: Dict[str, float] = Field(..., description="要添加噪声的数值")


class DifferentialPrivacyResponse(BaseModel):
    """差分隐私响应"""
    original_values: Dict[str, float]
    protected_values: Dict[str, float]
    privacy_budget_spent: float
    epsilon: float
    delta: float


class PrivacyAuditLogEntry(BaseModel):
    """隐私审计日志条目"""
    timestamp: str
    event_type: str
    user_id: str
    accessor_id: Optional[str] = None
    data_types: List[str]
    purpose: Optional[str] = None
    granted: Optional[bool] = None
    details: Dict[str, Any] = Field(default_factory=dict)


class PrivacyAuditLogsResponse(BaseModel):
    """隐私审计日志响应"""
    user_id: Optional[str]
    total_logs: int
    logs: List[PrivacyAuditLogEntry]


class PrivacyDashboardResponse(BaseModel):
    """隐私仪表板响应"""
    user_id: str
    settings: Dict[str, Any]
    recent_activity: List[Dict[str, Any]]
    rights_exercisable: Dict[str, bool]
    privacy_score: float


class ConsentRequest(BaseModel):
    """同意请求"""
    user_id: str
    consent_type: str
    granted: bool
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


class ConsentResponse(BaseModel):
    """同意响应"""
    consent_id: str
    user_id: str
    consent_type: str
    granted: bool
    timestamp: str


class DataRightsRequest(BaseModel):
    """数据权利请求"""
    user_id: str
    right: str = Field(..., description="权利类型: access, correction, deletion, portability, objection")
    data_type: Optional[str] = None
    details: Dict[str, Any] = Field(default_factory=dict)


class DataRightsResponse(BaseModel):
    """数据权利响应"""
    success: bool
    right: str
    user_id: str
    data_type: Optional[str] = None
    result: Dict[str, Any]
    timestamp: str


class PrivacyConfigResponse(BaseModel):
    """隐私配置响应"""
    enable_federated_learning: bool
    enable_differential_privacy: bool
    enable_edge_encryption: bool
    privacy_budget_epsilon: float
    privacy_budget_delta: float
    data_retention_days: int
    min_anonymity_k: int


class APIResponse(BaseModel):
    """通用API响应"""
    code: int = 0
    message: str = "success"
    data: Optional[Any] = None
    request_id: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


# ============== FastAPI App ==============

app = FastAPI(
    title="Privacy Shield Service",
    description="emoAIsec隐私安全服务 - 联邦学习、差分隐私、端侧加密、审计日志",
    version="1.0.0"
)

# 全局实例
_privacy_shield = PrivacyShield()
_audit_logger = PrivacyAuditLogger()
_settings_manager = PrivacySettingsManager()

# 联邦学习相关存储
_fl_clients: Dict[str, Dict] = {}
_fl_global_model: Dict[str, float] = {}
_fl_current_round: int = 0


# ============== Helper Functions ==============

def _create_request_id(prefix: str = "req") -> str:
    """创建请求ID"""
    return f"{prefix}_{uuid.uuid4().hex[:16]}"


def _parse_data_types(data_types: List[str]) -> List[DataType]:
    """解析数据类型"""
    result = []
    for dt in data_types:
        try:
            result.append(DataType(dt))
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid data type: {dt}")
    return result


# ============== API Endpoints ==============

@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy", "service": "privacy-shield"}


@app.get("/privacy/settings/{user_id}", response_model=APIResponse)
async def get_privacy_settings(user_id: str) -> APIResponse:
    """
    获取用户隐私设置
    
    返回指定用户的当前隐私偏好设置。
    
    Args:
        user_id: 用户ID
    
    Returns:
        用户隐私设置
    """
    try:
        settings = _settings_manager.get_user_settings(user_id)
        
        return APIResponse(
            code=0,
            message="success",
            data={
                "user_id": user_id,
                "settings": settings,
                "last_updated": datetime.now().isoformat()
            }
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get settings: {str(e)}")


@app.put("/privacy/settings/{user_id}", response_model=APIResponse)
async def update_privacy_settings(
    user_id: str,
    request: PrivacySettingsRequest
) -> APIResponse:
    """
    更新用户隐私设置
    
    更新指定用户的隐私偏好设置。
    
    Args:
        user_id: 用户ID
        request: 新的设置值
    
    Returns:
        更新后的设置
    """
    try:
        # 收集要更新的设置
        updates = {}
        if request.emotion_data_collection is not None:
            updates["emotion_data_collection"] = request.emotion_data_collection
        if request.biometric_storage is not None:
            updates["biometric_storage"] = request.biometric_storage
        if request.data_retention_days is not None:
            updates["data_retention_days"] = request.data_retention_days
        if request.third_party_sharing is not None:
            updates["third_party_sharing"] = request.third_party_sharing
        if request.marketing_use is not None:
            updates["marketing_use"] = request.marketing_use
        if request.research_use is not None:
            updates["research_use"] = request.research_use
        
        # 更新设置
        _settings_manager.update_settings(user_id, updates)
        
        # 记录审计日志
        consent_record = ConsentRecord(
            user_id=user_id,
            consent_type="settings_update",
            granted=True,
            timestamp=datetime.now()
        )
        _audit_logger.log_consent(consent_record)
        
        # 获取更新后的完整设置
        updated_settings = _settings_manager.get_user_settings(user_id)
        
        return APIResponse(
            code=0,
            message="success",
            data={
                "user_id": user_id,
                "settings": updated_settings,
                "updated_fields": list(updates.keys()),
                "last_updated": datetime.now().isoformat()
            }
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update settings: {str(e)}")


@app.post("/privacy/requests/delete", response_model=APIResponse)
async def request_data_deletion(request: DataDeletionRequest) -> APIResponse:
    """
    申请数据删除
    
    用户申请删除其个人数据。
    
    Args:
        request: 数据删除请求
    
    Returns:
        删除请求状态
    """
    try:
        # 验证数据类型
        data_types = _parse_data_types(request.data_types)
        
        # 创建删除请求
        request_id = _create_request_id("del")
        
        # 模拟删除调度
        scheduled_time = datetime.now()
        estimated_hours = len(data_types) * 2  # 每个类型约2小时
        
        # 记录审计日志
        _audit_logger.log_deletion(
            user_id=request.user_id,
            data_types=data_types,
            request_id=request_id
        )
        
        response = DataDeletionResponse(
            request_id=request_id,
            user_id=request.user_id,
            data_types=request.data_types,
            status="scheduled",
            scheduled_completion=scheduled_time.isoformat(),
            estimated_time_hours=estimated_hours
        )
        
        return APIResponse(
            code=0,
            message="success",
            data=response.model_dump()
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create deletion request: {str(e)}")


@app.get("/privacy/requests/{request_id}", response_model=APIResponse)
async def get_deletion_request_status(request_id: str) -> APIResponse:
    """
    获取删除请求状态
    
    查询数据删除请求的处理状态。
    
    Args:
        request_id: 请求ID
    
    Returns:
        请求状态
    """
    try:
        # 模拟请求状态查询
        return APIResponse(
            code=0,
            message="success",
            data={
                "request_id": request_id,
                "status": "processing",
                "progress_percent": 50,
                "completed_types": ["emotion_data"],
                "remaining_types": ["behavioral_data", "location_data"],
                "estimated_completion": datetime.now().isoformat()
            }
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get status: {str(e)}")


@app.get("/privacy/dashboard/{user_id}", response_model=APIResponse)
async def get_privacy_dashboard(user_id: str) -> APIResponse:
    """
    获取隐私仪表板
    
    返回用户隐私仪表板，包含设置、审计日志和可行使的权利。
    
    Args:
        user_id: 用户ID
    
    Returns:
        隐私仪表板数据
    """
    try:
        dashboard = _privacy_shield.get_privacy_dashboard(user_id)
        
        # 计算隐私评分 (模拟)
        settings = dashboard["settings"]
        privacy_score = 0
        if settings.get("emotion_data_collection", True):
            privacy_score += 20
        if not settings.get("biometric_storage", False):
            privacy_score += 20
        if not settings.get("third_party_sharing", False):
            privacy_score += 30
        if not settings.get("marketing_use", False):
            privacy_score += 15
        if settings.get("research_use", True):
            privacy_score += 15
        
        dashboard["privacy_score"] = privacy_score
        
        return APIResponse(code=0, message="success", data=dashboard)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get dashboard: {str(e)}")


@app.post("/privacy/consent", response_model=APIResponse)
async def record_consent(request: ConsentRequest) -> APIResponse:
    """
    记录用户同意
    
    记录用户对特定数据处理的同意。
    
    Args:
        request: 同意请求
    
    Returns:
        同意记录
    """
    try:
        consent_id = _create_request_id("consent")
        
        record = ConsentRecord(
            user_id=request.user_id,
            consent_type=request.consent_type,
            granted=request.granted,
            timestamp=datetime.now(),
            ip_address=request.ip_address,
            user_agent=request.user_agent
        )
        
        # 记录到审计日志
        _audit_logger.log_consent(record)
        
        # 如果同意，更新相应设置
        if request.granted:
            updates = {}
            if request.consent_type == "emotion_data":
                updates["emotion_data_collection"] = True
            elif request.consent_type == "biometric":
                updates["biometric_storage"] = True
            elif request.consent_type == "third_party":
                updates["third_party_sharing"] = True
            
            if updates:
                _settings_manager.update_settings(request.user_id, updates)
        
        response = ConsentResponse(
            consent_id=consent_id,
            user_id=request.user_id,
            consent_type=request.consent_type,
            granted=request.granted,
            timestamp=record.timestamp.isoformat()
        )
        
        return APIResponse(code=0, message="success", data=response.model_dump())
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to record consent: {str(e)}")


@app.get("/privacy/audit-logs", response_model=APIResponse)
async def get_audit_logs(
    user_id: Optional[str] = Query(None, description="用户ID筛选"),
    event_type: Optional[str] = Query(None, description="事件类型筛选"),
    start_time: Optional[str] = Query(None, description="开始时间 ISO格式"),
    end_time: Optional[str] = Query(None, description="结束时间 ISO格式"),
    limit: int = Query(100, ge=1, le=500)
) -> APIResponse:
    """
    获取隐私审计日志
    
    返回符合条件的隐私审计日志。
    
    Args:
        user_id: 用户ID
        event_type: 事件类型
        start_time: 开始时间
        end_time: 结束时间
        limit: 返回数量
    
    Returns:
        审计日志列表
    """
    try:
        # 解析时间
        start = datetime.fromisoformat(start_time) if start_time else None
        end = datetime.fromisoformat(end_time) if end_time else None
        
        # 获取日志
        logs = _audit_logger.get_logs(
            user_id=user_id,
            event_type=event_type,
            start_time=start,
            end_time=end
        )
        
        # 限制数量
        logs = logs[:limit]
        
        log_entries = [
            PrivacyAuditLogEntry(
                timestamp=log["timestamp"],
                event_type=log["event_type"],
                user_id=log.get("user_id", ""),
                accessor_id=log.get("accessor_id"),
                data_types=log.get("data_types", []),
                purpose=log.get("purpose"),
                granted=log.get("granted"),
                details=log.get("details", {})
            )
            for log in logs
        ]
        
        response = PrivacyAuditLogsResponse(
            user_id=user_id,
            total_logs=len(logs),
            logs=log_entries
        )
        
        return APIResponse(code=0, message="success", data=response.model_dump())
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get audit logs: {str(e)}")


@app.post("/privacy/federated-learning/submit", response_model=APIResponse)
async def submit_federated_update(request: FederatedLearningRequest) -> APIResponse:
    """
    提交联邦学习更新
    
    客户端提交本地训练得到的模型更新。
    
    Args:
        request: 联邦学习请求
    
    Returns:
        聚合结果
    """
    try:
        global _fl_current_round, _fl_global_model
        
        # 验证轮次
        if request.round < _fl_current_round:
            return APIResponse(
                code=1,
                message="stale_round",
                data={
                    "round": request.round,
                    "current_round": _fl_current_round,
                    "next_round_available": False
                }
            )
        
        # 存储客户端更新
        _fl_clients[request.client_id] = {
            "round": request.round,
            "gradients": request.gradient_data,
            "sample_count": request.sample_count,
            "submitted_at": datetime.now().isoformat()
        }
        
        # 检查是否所有客户端都提交了
        expected_clients = 3  # 模拟3个网点客户端
        submissions_this_round = sum(
            1 for c in _fl_clients.values() if c["round"] == request.round
        )
        
        if submissions_this_round >= expected_clients:
            # 执行安全聚合
            aggregated = _aggregate_gradients(request.round)
            _fl_global_model = aggregated
            _fl_current_round = request.round + 1
            
            return APIResponse(
                code=0,
                message="round_completed",
                data={
                    "round": request.round,
                    "status": "aggregated",
                    "aggregated_model": aggregated,
                    "next_round_available": True
                }
            )
        
        return APIResponse(
            code=0,
            message="update_received",
            data={
                "round": request.round,
                "status": "waiting_for_other_clients",
                "submissions_received": submissions_this_round,
                "submissions_expected": expected_clients
            }
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to submit update: {str(e)}")


def _aggregate_gradients(round_num: int) -> Dict[str, float]:
    """聚合多个客户端的梯度"""
    clients_this_round = [
        c for c in _fl_clients.values() if c["round"] == round_num
    ]
    
    if not clients_this_round:
        return {}
    
    # 加权平均聚合
    total_samples = sum(c["sample_count"] for c in clients_this_round)
    aggregated = {}
    
    # 获取所有梯度键
    all_keys = set()
    for c in clients_this_round:
        all_keys.update(c["gradients"].keys())
    
    for key in all_keys:
        weighted_sum = 0
        for c in clients_this_round:
            weight = c["sample_count"] / total_samples
            weighted_sum += c["gradients"].get(key, 0) * weight
        aggregated[key] = weighted_sum
    
    return aggregated


@app.get("/privacy/federated-learning/model", response_model=APIResponse)
async def get_global_model(
    round_num: Optional[int] = Query(None, description="轮次号")
) -> APIResponse:
    """
    获取全局模型
    
    返回联邦学习的当前全局模型参数。
    
    Args:
        round_num: 指定轮次（可选）
    
    Returns:
        全局模型参数
    """
    try:
        if _fl_current_round == 0:
            return APIResponse(
                code=0,
                message="success",
                data={
                    "round": 0,
                    "model": {},
                    "status": "not_initialized"
                }
            )
        
        return APIResponse(
            code=0,
            message="success",
            data={
                "round": _fl_current_round - 1,
                "model": _fl_global_model,
                "status": "available",
                "client_count": len(_fl_clients)
            }
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get model: {str(e)}")


@app.post("/privacy/differential-privacy/protect", response_model=APIResponse)
async def apply_differential_privacy(request: DifferentialPrivacyRequest) -> APIResponse:
    """
    应用差分隐私
    
    对数值数据添加差分隐私噪声。
    
    Args:
        request: 差分隐私请求
    
    Returns:
        添加噪声后的数据
    """
    try:
        dp = _privacy_shield.dp
        
        protected_values = {}
        for key, value in request.values.items():
            protected_values[key] = dp.add_noise(value)
        
        # 更新隐私预算
        dp.record_privacy_spending(len(request.values) * 0.01)
        
        response = DifferentialPrivacyResponse(
            original_values=request.values,
            protected_values=protected_values,
            privacy_budget_spent=dp.privacy_budget_spent,
            epsilon=dp.epsilon,
            delta=dp.delta
        )
        
        return APIResponse(code=0, message="success", data=response.model_dump())
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to apply DP: {str(e)}")


@app.post("/privacy/rights/exercise", response_model=APIResponse)
async def exercise_data_rights(request: DataRightsRequest) -> APIResponse:
    """
    行使数据权利
    
    用户行使GDPR/个人信息保护法规定的数据权利。
    
    Args:
        request: 数据权利请求
    
    Returns:
        权利行使结果
    """
    try:
        valid_rights = ["access", "correction", "deletion", "portability", "objection"]
        if request.right not in valid_rights:
            raise HTTPException(status_code=400, detail=f"Invalid right: {request.right}")
        
        # 解析数据类型
        data_type = None
        if request.data_type:
            try:
                data_type = DataType(request.data_type)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid data type: {request.data_type}")
        
        # 行使权利
        result = _settings_manager.exercise_right(
            user_id=request.user_id,
            right=request.right,
            data_type=data_type
        )
        
        # 记录审计日志
        _audit_logger.logs.append({
            "timestamp": datetime.now().isoformat(),
            "event_type": "data_right_exercise",
            "user_id": request.user_id,
            "right": request.right,
            "data_type": request.data_type,
            "success": result["success"]
        })
        
        response = DataRightsResponse(
            success=result["success"],
            right=request.right,
            user_id=request.user_id,
            data_type=request.data_type,
            result=result,
            timestamp=datetime.now().isoformat()
        )
        
        return APIResponse(code=0, message="success", data=response.model_dump())
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to exercise right: {str(e)}")


@app.get("/privacy/config", response_model=APIResponse)
async def get_privacy_config() -> APIResponse:
    """
    获取隐私配置
    
    返回系统的隐私保护配置。
    
    Returns:
        隐私配置
    """
    try:
        config = _privacy_shield.config
        
        response = PrivacyConfigResponse(
            enable_federated_learning=config.enable_federated_learning,
            enable_differential_privacy=config.enable_differential_privacy,
            enable_edge_encryption=config.enable_edge_encryption,
            privacy_budget_epsilon=config.privacy_budget_epsilon,
            privacy_budget_delta=config.privacy_budget_delta,
            data_retention_days=config.data_retention_days,
            min_anonymity_k=config.min_anonymity_k
        )
        
        return APIResponse(code=0, message="success", data=response.model_dump())
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get config: {str(e)}")


@app.post("/privacy/data-access/request", response_model=APIResponse)
async def create_access_request(request: DataAccessRequestCreate) -> APIResponse:
    """
    创建数据访问请求
    
    系统或管理员发起数据访问请求。
    
    Args:
        request: 访问请求
    
    Returns:
        请求状态
    """
    try:
        # 解析数据类型
        data_types = _parse_data_types(request.data_types)
        
        # 创建请求
        access_request = _privacy_shield.create_access_request(
            user_id=request.user_id,
            data_types=data_types,
            purpose=request.purpose,
            accessor_id=request.accessor_id,
            accessor_type=request.accessor_type
        )
        
        request_id = _create_request_id("access")
        
        # 记录审计日志
        _audit_logger.log_access(access_request, granted=False)
        
        response = DataAccessRequestResponse(
            request_id=request_id,
            user_id=request.user_id,
            data_types=request.data_types,
            purpose=request.purpose,
            accessor_id=request.accessor_id,
            accessor_type=request.accessor_type,
            status="pending",
            created_at=datetime.now().isoformat()
        )
        
        return APIResponse(code=0, message="success", data=response.model_dump())
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create access request: {str(e)}")


@app.post("/privacy/data-access/{request_id}/approve", response_model=APIResponse)
async def approve_access_request(request_id: str) -> APIResponse:
    """
    批准数据访问请求
    
    批准待处理的数据访问请求。
    
    Args:
        request_id: 请求ID
    
    Returns:
        批准结果
    """
    try:
        # 模拟批准处理
        return APIResponse(
            code=0,
            message="success",
            data={
                "request_id": request_id,
                "status": "approved",
                "approved_at": datetime.now().isoformat(),
                "access_expires_at": datetime.now().isoformat()
            }
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to approve: {str(e)}")


@app.get("/privacy/statistics", response_model=APIResponse)
async def get_privacy_statistics() -> APIResponse:
    """
    获取隐私统计数据
    
    返回系统隐私保护相关的统计信息。
    
    Returns:
        统计数据
    """
    try:
        # 聚合统计数据
        total_users = len(_settings_manager.user_settings)
        total_deletion_requests = len([l for l in _audit_logger.logs if l.get("event_type") == "data_deletion"])
        total_access_requests = len([l for l in _audit_logger.logs if l.get("event_type") == "data_access"])
        
        # 计算同意率
        consent_logs = [l for l in _audit_logger.logs if l.get("event_type") == "consent"]
        consented = sum(1 for l in consent_logs if l.get("granted"))
        consent_rate = consented / len(consent_logs) if consent_logs else 1.0
        
        stats = {
            "total_users": total_users,
            "total_deletion_requests": total_deletion_requests,
            "total_access_requests": total_access_requests,
            "consent_rate": round(consent_rate, 3),
            "privacy_budget_remaining": _privacy_shield.dp.epsilon - _privacy_shield.dp.privacy_budget_spent,
            "federated_learning_rounds": _fl_current_round,
            "audit_logs_total": len(_audit_logger.logs)
        }
        
        return APIResponse(code=0, message="success", data=stats)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get statistics: {str(e)}")


# ============== Main ==============

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8006)
