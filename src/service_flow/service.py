"""
服务流程引擎服务 - FastAPI服务接口
Service Flow Engine Service - FastAPI Endpoints
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from fastapi import FastAPI, HTTPException, Query, Depends
from pydantic import BaseModel, Field

from .models import (
    ServiceFlowStateMachine,
    EmotionDrivenOrchestrator,
    HumanMachineCollaborator,
    ProcessCategory,
    ProcessStatus,
    StageStatus,
    TriggerType,
    EmotionState,
    ServiceRepairStrategy,
    ProcessDefinition,
    ProcessInstance
)


# ============== Pydantic Models ==============

class ProcessListItem(BaseModel):
    """流程列表项"""
    id: str
    name: str
    category: str
    version: str
    status: str
    description: str
    stages: List[str]
    avg_duration_minutes: int
    satisfaction_rate: float


class ProcessListResponse(BaseModel):
    """流程列表响应"""
    items: List[ProcessListItem]
    total: int
    page: int
    page_size: int


class TriggerRequest(BaseModel):
    """触发流程请求"""
    session_id: Optional[str] = None
    user_id: str
    trigger_type: str = "manual"
    trigger_data: Dict[str, Any] = Field(default_factory=dict)
    initial_context: Dict[str, Any] = Field(default_factory=dict)


class TriggerResponse(BaseModel):
    """触发流程响应"""
    instance_id: str
    process_id: str
    current_stage: str
    started_at: str
    recommended_actions: List[Dict[str, Any]]


class StageInfo(BaseModel):
    """阶段信息"""
    name: str
    status: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    emotion_at_entry: Optional[str] = None
    emotion_at_exit: Optional[str] = None


class InstanceResponse(BaseModel):
    """流程实例响应"""
    instance_id: str
    process_id: str
    process_name: str
    status: str
    current_stage: str
    stages: List[StageInfo]
    context: Dict[str, Any]
    started_at: str
    updated_at: str
    completed_at: Optional[str] = None
    emotion_trend: List[Dict[str, Any]]
    repair_attempts: int


class EmotionInput(BaseModel):
    """情绪输入"""
    emotion: str
    intensity: float = Field(..., ge=0, le=1)
    duration_seconds: int = Field(default=0, ge=0)


class FlowAdjustmentRequest(BaseModel):
    """流程调整请求"""
    instance_id: str
    emotion: EmotionInput
    context: Dict[str, Any] = Field(default_factory=dict)


class FlowAdjustmentResponse(BaseModel):
    """流程调整响应"""
    action: str
    message: str
    triggered: bool = False
    recovery_strategy: Optional[str] = None
    escalation_required: bool = False
    priority_boost: int = 0


class RepairRequest(BaseModel):
    """服务修复请求"""
    instance_id: str
    strategy: str
    context: Dict[str, Any] = Field(default_factory=dict)


class RepairResponse(BaseModel):
    """服务修复响应"""
    action_type: str
    action_details: Dict[str, Any]
    collaboration_session_id: Optional[str] = None


class EscalationRequest(BaseModel):
    """升级人工请求"""
    instance_id: str
    reason: str
    priority: int = Field(default=3, ge=1, le=5)


class EscalationResponse(BaseModel):
    """升级人工响应"""
    request_id: str
    instance_id: str
    status: str
    message: str


class APIResponse(BaseModel):
    """通用API响应"""
    code: int = 0
    message: str = "success"
    data: Optional[Any] = None
    request_id: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


# ============== FastAPI App ==============

app = FastAPI(
    title="Service Flow Engine",
    description="服务流程引擎 - 情绪驱动编排、人机协同、服务修复",
    version="1.0.0"
)

# 全局实例
_state_machine = ServiceFlowStateMachine()
_orchestrator = EmotionDrivenOrchestrator()
_collaborator = HumanMachineCollaborator()


@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy", "service": "service-flow"}


@app.get("/flow/processes", response_model=APIResponse)
async def get_processes(
    category: Optional[str] = Query(None, description="流程类别"),
    status: Optional[str] = Query(None, description="状态"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页数量")
) -> APIResponse:
    """
    获取服务流程列表
    
    返回系统中定义的所有服务流程，支持按类别和状态筛选。
    
    Args:
        category: 流程类别 (complaint, inquiry, transaction, recovery, vip_service)
        status: 状态 (active, deprecated, draft, archived)
        page: 页码
        page_size: 每页数量
    
    Returns:
        流程列表
    """
    try:
        # 转换筛选条件
        cat_filter = ProcessCategory(category) if category else None
        status_filter = ProcessStatus(status) if status else None
        
        # 获取流程列表
        processes = _state_machine.get_processes(
            category=cat_filter,
            status=status_filter
        )
        
        # 分页
        total = len(processes)
        start = (page - 1) * page_size
        end = start + page_size
        paginated = processes[start:end]
        
        # 转换响应格式
        items = [
            ProcessListItem(
                id=p.id,
                name=p.name,
                category=p.category.value,
                version=p.version,
                status=p.status.value,
                description=p.description,
                stages=[s.name for s in p.stages],
                avg_duration_minutes=p.avg_duration_minutes,
                satisfaction_rate=p.satisfaction_rate
            )
            for p in paginated
        ]
        
        return APIResponse(
            code=0,
            message="success",
            data={
                "items": [item.model_dump() for item in items],
                "total": total,
                "page": page,
                "page_size": page_size
            }
        )
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid filter value: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get processes: {str(e)}")


@app.post("/flow/processes/{process_id}/trigger", response_model=APIResponse)
async def trigger_process(
    process_id: str,
    request: TriggerRequest
) -> APIResponse:
    """
    触发服务流程
    
    根据触发类型和上下文创建流程实例并启动执行。
    
    Args:
        process_id: 流程ID
        request: 触发请求
    
    Returns:
        创建的流程实例信息
    """
    try:
        # 转换触发类型
        trigger_type = TriggerType(request.trigger_type)
        
        # 构建上下文
        context = request.initial_context.copy()
        context["trigger_data"] = request.trigger_data
        
        # 创建实例
        instance = _state_machine.create_instance(
            process_id=process_id,
            user_id=request.user_id,
            trigger_type=trigger_type,
            context=context,
            session_id=request.session_id
        )
        
        # 启动流程
        instance = _state_machine.transition(
            instance_id=instance.instance_id,
            new_status="in_progress"
        )
        
        # 生成推荐动作
        recommended_actions = []
        
        # 如果是情绪告警触发，生成相应建议
        if trigger_type == TriggerType.EMOTION_ALERT:
            emotion_data = request.trigger_data.get("emotion", "neutral")
            intensity = request.trigger_data.get("intensity", 0.5)
            
            adjustment = _orchestrator.determine_flow_adjustment(
                current_emotion=emotion_data,
                intensity=intensity,
                duration_seconds=0
            )
            
            if adjustment.get("triggered"):
                recommended_actions.append({
                    "action": "priority_service",
                    "description": "优先处理此客户",
                    "priority_boost": adjustment.get("priority_boost", 0)
                })
                recommended_actions.append({
                    "action": "empathy_response",
                    "description": "发送同理心回复",
                    "template_id": "empathy_001"
                })
        
        return APIResponse(
            code=0,
            message="success",
            data={
                "instance_id": instance.instance_id,
                "process_id": instance.process_id,
                "current_stage": instance.current_stage,
                "started_at": instance.started_at.isoformat(),
                "recommended_actions": recommended_actions
            }
        )
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to trigger process: {str(e)}")


@app.get("/flow/instances/{instance_id}", response_model=APIResponse)
async def get_instance_status(instance_id: str) -> APIResponse:
    """
    获取流程实例状态
    
    返回指定流程实例的当前状态、阶段进度和上下文。
    
    Args:
        instance_id: 实例ID
    
    Returns:
        流程实例详情
    """
    try:
        instance = _state_machine.get_instance(instance_id)
        
        if not instance:
            raise HTTPException(status_code=404, detail=f"Instance {instance_id} not found")
        
        # 转换阶段信息
        stages_info = [
            StageInfo(
                name=s.name,
                status=s.status.value,
                started_at=s.started_at.isoformat() if s.started_at else None,
                completed_at=s.completed_at.isoformat() if s.completed_at else None,
                emotion_at_entry=s.emotion_at_entry,
                emotion_at_exit=s.emotion_at_exit
            )
            for s in instance.stages
        ]
        
        # 计算情绪改善度
        emotion_improvement = 0.0
        if len(instance.emotion_trend) >= 2:
            first_emotion = instance.emotion_trend[0].get("intensity", 0)
            last_emotion = instance.emotion_trend[-1].get("intensity", 0)
            emotion_improvement = first_emotion - last_emotion
        
        # 添加到上下文
        context_with_stats = instance.context.copy()
        context_with_stats["emotion_at_entry"] = instance.emotion_trend[0].get("emotion") if instance.emotion_trend else None
        context_with_stats["emotion_current"] = instance.emotion_trend[-1].get("emotion") if instance.emotion_trend else None
        context_with_stats["emotion_improvement"] = round(emotion_improvement, 2)
        context_with_stats["interactions_count"] = len(instance.emotion_trend)
        
        return APIResponse(
            code=0,
            message="success",
            data={
                "instance_id": instance.instance_id,
                "process_id": instance.process_id,
                "process_name": instance.process_name,
                "status": instance.status,
                "current_stage": instance.current_stage,
                "stages": [s.model_dump() for s in stages_info],
                "context": context_with_stats,
                "started_at": instance.started_at.isoformat(),
                "updated_at": instance.updated_at.isoformat(),
                "completed_at": instance.completed_at.isoformat() if instance.completed_at else None,
                "emotion_trend": instance.emotion_trend,
                "repair_attempts": instance.repair_attempts
            }
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get instance: {str(e)}")


@app.post("/flow/instances/{instance_id}/advance", response_model=APIResponse)
async def advance_stage(
    instance_id: str,
    emotion_state: Optional[EmotionInput] = None
) -> APIResponse:
    """
    推进流程阶段
    
    将流程实例从当前阶段推进到下一阶段。
    
    Args:
        instance_id: 实例ID
        emotion_state: 当前情绪状态
    
    Returns:
        更新后的实例状态
    """
    try:
        emotion_data = None
        if emotion_state:
            emotion_data = {
                "emotion": emotion_state.emotion,
                "intensity": emotion_state.intensity
            }
        
        instance = _state_machine.advance_stage(
            instance_id=instance_id,
            emotion_state=emotion_data
        )
        
        return APIResponse(
            code=0,
            message="success",
            data={
                "instance_id": instance.instance_id,
                "status": instance.status,
                "current_stage": instance.current_stage,
                "updated_at": instance.updated_at.isoformat()
            }
        )
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to advance stage: {str(e)}")


@app.post("/flow/adjust", response_model=APIResponse)
async def adjust_flow_based_on_emotion(request: FlowAdjustmentRequest) -> APIResponse:
    """
    基于情绪调整流程
    
    根据客户当前情绪状态，动态调整服务流程。
    
    Args:
        request: 流程调整请求
    
    Returns:
        调整策略
    """
    try:
        adjustment = _orchestrator.determine_flow_adjustment(
            current_emotion=request.emotion.emotion,
            intensity=request.emotion.intensity,
            duration_seconds=request.emotion.duration_seconds
        )
        
        return APIResponse(
            code=0,
            message="success",
            data={
                "action": adjustment.get("action"),
                "message": adjustment.get("message"),
                "triggered": adjustment.get("triggered", False),
                "recovery_strategy": adjustment.get("recovery_strategy"),
                "escalation_required": adjustment.get("escalation_required", False),
                "priority_boost": adjustment.get("priority_boost", 0)
            }
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to adjust flow: {str(e)}")


@app.post("/flow/repair", response_model=APIResponse)
async def trigger_service_repair(request: RepairRequest) -> APIResponse:
    """
    触发服务修复
    
    根据指定策略执行服务修复动作。
    
    Args:
        request: 修复请求
    
    Returns:
        修复动作结果
    """
    try:
        strategy = ServiceRepairStrategy(request.strategy)
        
        # 获取解决动作
        action = _collaborator.get_resolution_action(strategy, request.context)
        
        # 如果需要升级人工
        if action["type"] == "escalation":
            escalation_req = _collaborator.request_human_intervention(
                instance_id=request.instance_id,
                reason=f"Service repair strategy: {strategy.value}",
                priority=3
            )
            action["escalation_request_id"] = escalation_req["request_id"]
        
        return APIResponse(
            code=0,
            message="success",
            data={
                "action_type": action["type"],
                "action_details": action,
                "collaboration_session_id": None
            }
        )
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid strategy: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to trigger repair: {str(e)}")


@app.post("/flow/escalate", response_model=APIResponse)
async def escalate_to_human(request: EscalationRequest) -> APIResponse:
    """
    升级人工处理
    
    将当前流程实例升级为人工处理。
    
    Args:
        request: 升级请求
    
    Returns:
        升级请求状态
    """
    try:
        escalation_req = _collaborator.request_human_intervention(
            instance_id=request.instance_id,
            reason=request.reason,
            priority=request.priority
        )
        
        return APIResponse(
            code=0,
            message="success",
            data={
                "request_id": escalation_req["request_id"],
                "instance_id": escalation_req["instance_id"],
                "status": escalation_req["status"],
                "message": f"已提交人工介入请求，优先级: {request.priority}"
            }
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to escalate: {str(e)}")


@app.get("/flow/empathy-script", response_model=APIResponse)
async def get_empathy_script(
    emotion: str = Query(..., description="情绪类型"),
    intensity: float = Query(..., ge=0, le=1, description="情绪强度"),
    wait_time: int = Query(0, ge=0, description="等待时间(分钟)")
) -> APIResponse:
    """
    获取同理心话术
    
    根据当前情绪状态生成适当的同理心回复话术。
    
    Args:
        emotion: 情绪类型
        intensity: 情绪强度
        wait_time: 等待时间
    
    Returns:
        生成的同理心话术
    """
    try:
        script = _orchestrator.generate_empathy_script(
            emotion=emotion,
            intensity=intensity,
            context={"wait_time": wait_time}
        )
        
        return APIResponse(
            code=0,
            message="success",
            data={
                "emotion": emotion,
                "intensity": intensity,
                "script": script
            }
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate script: {str(e)}")


@app.get("/flow/instances", response_model=APIResponse)
async def list_instances(
    process_id: Optional[str] = Query(None, description="流程ID"),
    status: Optional[str] = Query(None, description="状态"),
    user_id: Optional[str] = Query(None, description="用户ID"),
    limit: int = Query(50, ge=1, le=200, description="返回数量")
) -> APIResponse:
    """
    获取流程实例列表
    
    查询符合条件的流程实例。
    
    Args:
        process_id: 流程ID筛选
        status: 状态筛选
        user_id: 用户ID筛选
        limit: 返回数量
    
    Returns:
        实例列表
    """
    try:
        instances = list(_state_machine.instances.values())
        
        # 应用筛选
        if process_id:
            instances = [i for i in instances if i.process_id == process_id]
        if status:
            instances = [i for i in instances if i.status == status]
        if user_id:
            instances = [i for i in instances if i.user_id == user_id]
        
        # 限制数量
        instances = instances[:limit]
        
        return APIResponse(
            code=0,
            message="success",
            data={
                "total": len(instances),
                "instances": [
                    {
                        "instance_id": i.instance_id,
                        "process_id": i.process_id,
                        "process_name": i.process_name,
                        "status": i.status,
                        "current_stage": i.current_stage,
                        "user_id": i.user_id,
                        "started_at": i.started_at.isoformat()
                    }
                    for i in instances
                ]
            }
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list instances: {str(e)}")


# ============== Main ==============

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004)
