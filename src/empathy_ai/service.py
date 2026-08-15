"""
同理心AI服务 - FastAPI服务接口
Empathy AI Service - FastAPI Endpoints

基于论文第四章：共情AI驱动的网点服务流程重构
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field
import uuid

from .models import (
    EmpathyLevel,
    ActionType,
    ActionRecommendation,
    EmpathyResponse,
    EmpathyContext,
    ArtificialEmpathyService,
    EmpathyResponseGenerator
)


# ============== Pydantic Models ==============

class ChatMessage(BaseModel):
    """聊天消息"""
    role: str = Field(..., description="角色: user/assistant/system")
    content: str = Field(..., min_length=1, max_length=5000)
    timestamp: Optional[str] = None


class ChatRequest(BaseModel):
    """对话请求"""
    user_id: str
    message: str = Field(..., min_length=1, max_length=5000)
    session_id: Optional[str] = None
    
    # 情绪上下文
    current_emotion: str = Field(default="neutral", description="当前情绪")
    emotion_intensity: float = Field(default=0.5, ge=0, le=1, description="情绪强度")
    emotion_duration_seconds: int = Field(default=0, ge=0, description="情绪持续时间")
    
    # 服务上下文
    service_type: str = Field(default="", description="服务类型")
    queue_position: int = Field(default=0, ge=0, description="排队位置")
    wait_time_minutes: float = Field(default=0, ge=0, description="等待时间(分钟)")
    business_type: str = Field(default="", description="业务类型")
    previous_interactions: int = Field(default=0, ge=0, description="历史交互次数")
    is_returning_customer: bool = Field(default=False, description="是否回头客")
    
    # 客户信息
    customer_tier: str = Field(default="standard", description="客户等级")
    customer_segment: List[str] = Field(default_factory=list, description="客户细分")
    
    # 额外上下文
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ChatResponse(BaseModel):
    """对话响应"""
    message: str
    empathy_level: str
    empathy_score: float
    action_recommendations: List[Dict[str, Any]]
    escalation: Dict[str, Any]
    agent_info: Dict[str, Any]


class AgentInfo(BaseModel):
    """代理信息"""
    agent_id: str
    name: str
    avatar_url: str
    personality: str
    voice_url: Optional[str] = None


class AgentResponse(BaseModel):
    """代理信息响应"""
    agent_id: str
    name: str
    avatar_url: str
    personality: str
    voice_url: Optional[str] = None
    capabilities: List[str]
    languages: List[str]
    specializations: List[str]


class ConversationContextRequest(BaseModel):
    """会话上下文更新请求"""
    session_id: str
    user_id: str
    current_emotion: Optional[str] = None
    emotion_intensity: Optional[float] = None
    wait_time_minutes: Optional[float] = None
    service_type: Optional[str] = None


class ConversationTurn(BaseModel):
    """对话轮次"""
    turn_id: str
    user_message: str
    agent_message: str
    empathy_level: str
    timestamp: str
    emotion_before: Optional[str] = None
    emotion_after: Optional[str] = None


class ConversationHistory(BaseModel):
    """对话历史"""
    session_id: str
    user_id: str
    turns: List[ConversationTurn]
    total_turns: int
    avg_empathy_score: float


class ServiceRecoveryRequest(BaseModel):
    """服务修复请求"""
    emotion: str = Field(..., description="情绪类型")
    intensity: float = Field(..., ge=0, le=1, description="情绪强度")
    context: Dict[str, Any] = Field(default_factory=dict)


class ServiceRecoveryResponse(BaseModel):
    """服务修复响应"""
    scripts: List[str]
    strategies: List[Dict[str, Any]]
    escalation_required: bool


class APIResponse(BaseModel):
    """通用API响应"""
    code: int = 0
    message: str = "success"
    data: Optional[Any] = None
    request_id: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


# ============== FastAPI App ==============

app = FastAPI(
    title="Empathy AI Service",
    description="人工同理心AI服务 - 智能共情交互、服务安抚、情绪疏导",
    version="1.0.0"
)

# 全局实例
_empathy_service = ArtificialEmpathyService()
_response_generator = EmpathyResponseGenerator()

# 会话存储 (生产环境应使用Redis)
_conversations: Dict[str, Dict[str, Any]] = {}
_conversation_histories: Dict[str, List[Dict[str, Any]]] = {}


# ============== Helper Functions ==============

def _create_session_id() -> str:
    """创建会话ID"""
    return f"emp_session_{uuid.uuid4().hex[:16]}"


def _create_turn_id() -> str:
    """创建轮次ID"""
    return f"turn_{uuid.uuid4().hex[:12]}"


def _build_empathy_context(request: ChatRequest) -> EmpathyContext:
    """构建同理心上下文"""
    return EmpathyContext(
        user_id=request.user_id,
        session_id=request.session_id or _create_session_id(),
        current_emotion=request.current_emotion,
        emotion_intensity=request.emotion_intensity,
        emotion_duration_seconds=request.emotion_duration_seconds,
        service_type=request.service_type,
        queue_position=request.queue_position,
        wait_time_minutes=request.wait_time_minutes,
        business_type=request.business_type,
        previous_interactions=request.previous_interactions,
        is_returning_customer=request.is_returning_customer,
        customer_tier=request.customer_tier,
        customer_segment=request.customer_segment
    )


def _convert_action_recommendation(action: ActionRecommendation) -> Dict[str, Any]:
    """转换行动推荐为字典"""
    result = {
        "type": action.type.value,
        "triggered": action.triggered
    }
    
    if action.options:
        result["options"] = action.options
    if action.script:
        result["script"] = action.script
    if action.priority_boost is not None:
        result["priority_boost"] = action.priority_boost
    
    return result


# ============== API Endpoints ==============

@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy", "service": "empathy-ai"}


@app.post("/empathy/chat", response_model=APIResponse)
async def chat(request: ChatRequest) -> APIResponse:
    """
    发送对话消息
    
    基于客户的情绪状态和服务上下文，生成具有同理心的AI回复。
    
    Args:
        request: 对话请求
    
    Returns:
        同理心回复及行动推荐
    """
    try:
        # 构建上下文
        context = _build_empathy_context(request)
        
        # 生成回复
        response = _empathy_service.process(
            user_message=request.message,
            context=context
        )
        
        # 保存对话历史
        session_id = context.session_id
        if session_id not in _conversation_histories:
            _conversation_histories[session_id] = []
            _conversations[session_id] = {
                "session_id": session_id,
                "user_id": request.user_id,
                "created_at": datetime.now().isoformat()
            }
        
        turn = {
            "turn_id": _create_turn_id(),
            "user_message": request.message,
            "agent_message": response.message,
            "empathy_level": response.empathy_level.value,
            "empathy_score": response.empathy_score,
            "timestamp": datetime.now().isoformat(),
            "emotion_before": request.current_emotion,
            "emotion_after": None  # 假设处理后情绪有所改善
        }
        _conversation_histories[session_id].append(turn)
        
        return APIResponse(
            code=0,
            message="success",
            data={
                "session_id": session_id,
                "message": response.message,
                "empathy_level": response.empathy_level.value,
                "empathy_score": round(response.empathy_score, 3),
                "action_recommendations": [
                    _convert_action_recommendation(a) 
                    for a in response.action_recommendations
                ],
                "escalation": response.escalation,
                "agent_info": response.agent_info
            }
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat processing failed: {str(e)}")


@app.get("/empathy/agents/{agent_id}", response_model=APIResponse)
async def get_agent_info(agent_id: str) -> APIResponse:
    """
    获取代理信息
    
    返回虚拟代理的配置和能力信息。
    
    Args:
        agent_id: 代理ID
    
    Returns:
        代理详细信息
    """
    try:
        # 模拟代理数据
        if agent_id not in ["agent_001", "agent_002", "all"]:
            raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
        
        if agent_id == "all":
            agents = [
                {
                    "agent_id": "agent_001",
                    "name": "小e",
                    "avatar_url": "https://xxx/avatar_xiao_e.png",
                    "personality": "warm_professional",
                    "voice_url": "https://xxx/voice_xiao_e.wav",
                    "capabilities": ["emotional_support", "service_recovery", "queue_management"],
                    "languages": ["zh-CN", "en-US"],
                    "specializations": ["complaint_handling", "anxiety_management"]
                },
                {
                    "agent_id": "agent_002",
                    "name": "小智",
                    "avatar_url": "https://xxx/avatar_xiao_zhi.png",
                    "personality": "efficient_knowledgeable",
                    "voice_url": "https://xxx/voice_xiao_zhi.wav",
                    "capabilities": ["information_query", "business_guidance", "product_recommendation"],
                    "languages": ["zh-CN", "en-US", "zh-TW"],
                    "specializations": ["account_services", "product_inquiry"]
                }
            ]
            return APIResponse(code=0, message="success", data={"agents": agents})
        
        agent_info = {
            "agent_id": "agent_001",
            "name": "小e",
            "avatar_url": "https://xxx/avatar_xiao_e.png",
            "personality": "warm_professional",
            "voice_url": "https://xxx/voice_xiao_zhi.wav",
            "capabilities": [
                "emotional_support",
                "service_recovery", 
                "queue_management",
                "complaint_handling"
            ],
            "languages": ["zh-CN", "en-US"],
            "specializations": [
                "complaint_handling",
                "anxiety_management",
                "waiting_comfort"
            ]
        }
        
        return APIResponse(code=0, message="success", data=agent_info)
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get agent info: {str(e)}")


@app.get("/empathy/conversations/{session_id}", response_model=APIResponse)
async def get_conversation_history(
    session_id: str,
    limit: int = Query(50, ge=1, le=200, description="返回轮次数量")
) -> APIResponse:
    """
    获取对话历史
    
    返回指定会话的对话历史记录。
    
    Args:
        session_id: 会话ID
        limit: 返回轮次数量
    
    Returns:
        对话历史
    """
    try:
        if session_id not in _conversations:
            raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
        
        history = _conversation_histories.get(session_id, [])[-limit:]
        
        # 计算平均同理心得分
        total_score = sum(t.get("empathy_score", 0) for t in history)
        avg_score = total_score / len(history) if history else 0
        
        turns = [
            ConversationTurn(
                turn_id=t["turn_id"],
                user_message=t["user_message"],
                agent_message=t["agent_message"],
                empathy_level=t["empathy_level"],
                timestamp=t["timestamp"],
                emotion_before=t.get("emotion_before"),
                emotion_after=t.get("emotion_after")
            )
            for t in history
        ]
        
        conversation_history = ConversationHistory(
            session_id=session_id,
            user_id=_conversations[session_id]["user_id"],
            turns=turns,
            total_turns=len(history),
            avg_empathy_score=round(avg_score, 3)
        )
        
        return APIResponse(
            code=0,
            message="success",
            data=conversation_history.model_dump()
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get conversation: {str(e)}")


@app.post("/empathy/context/update", response_model=APIResponse)
async def update_context(request: ConversationContextRequest) -> APIResponse:
    """
    更新会话上下文
    
    更新客户的情绪和服务上下文，用于持续的情绪跟踪。
    
    Args:
        request: 上下文更新请求
    
    Returns:
        更新结果
    """
    try:
        session_id = request.session_id
        
        # 确保会话存在
        if session_id not in _conversations:
            _conversations[session_id] = {
                "session_id": session_id,
                "user_id": request.user_id,
                "created_at": datetime.now().isoformat()
            }
            _conversation_histories[session_id] = []
        
        # 更新上下文
        context_updates = {}
        if request.current_emotion is not None:
            context_updates["current_emotion"] = request.current_emotion
        if request.emotion_intensity is not None:
            context_updates["emotion_intensity"] = request.emotion_intensity
        if request.wait_time_minutes is not None:
            context_updates["wait_time_minutes"] = request.wait_time_minutes
        if request.service_type is not None:
            context_updates["service_type"] = request.service_type
        
        _conversations[session_id].update(context_updates)
        
        return APIResponse(
            code=0,
            message="success",
            data={
                "session_id": session_id,
                "context_updated": context_updates,
                "timestamp": datetime.now().isoformat()
            }
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update context: {str(e)}")


@app.post("/empathy/recovery/scripts", response_model=APIResponse)
async def get_recovery_scripts(request: ServiceRecoveryRequest) -> APIResponse:
    """
    获取服务修复话术
    
    根据当前情绪状态生成服务修复话术。
    
    Args:
        request: 服务修复请求
    
    Returns:
        修复话术列表
    """
    try:
        scripts = _empathy_service.get_service_recovery_script(
            emotion=request.emotion,
            intensity=request.intensity
        )
        
        # 根据情绪和强度确定策略
        strategies = []
        
        if request.intensity > 0.8:
            strategies.append({
                "strategy": "priority_service",
                "action": "立即开启优先通道",
                "priority": 1
            })
            strategies.append({
                "strategy": "human_escalation",
                "action": "考虑升级人工处理",
                "priority": 2
            })
        elif request.intensity > 0.6:
            strategies.append({
                "strategy": "empathy_response",
                "action": "发送同理心回复",
                "priority": 1
            })
            strategies.append({
                "strategy": "status_update",
                "action": "提供状态更新",
                "priority": 2
            })
        else:
            strategies.append({
                "strategy": "normal_service",
                "action": "保持正常服务流程",
                "priority": 3
            })
        
        escalation_required = request.intensity > 0.85
        
        response = ServiceRecoveryResponse(
            scripts=scripts,
            strategies=strategies,
            escalation_required=escalation_required
        )
        
        return APIResponse(
            code=0,
            message="success",
            data=response.model_dump()
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get recovery scripts: {str(e)}")


@app.get("/empathy/templates", response_model=APIResponse)
async def get_empathy_templates(
    emotion: Optional[str] = Query(None, description="情绪类型筛选"),
    level: Optional[str] = Query(None, description="同理心水平筛选")
) -> APIResponse:
    """
    获取同理心话术模板
    
    返回可用的同理心话术模板列表。
    
    Args:
        emotion: 情绪类型
        level: 同理心水平
    
    Returns:
        模板列表
    """
    try:
        templates = {
            "angry": {
                "high": [
                    "非常抱歉给您带来如此不好的体验，我能完全理解您现在的心情。{specific_issue}确实不应该发生，请您相信我们一定会认真处理您的问题。",
                    "您说得对，遇到这样的情况任何人都会有您这样的反应。我们真诚地向您道歉，并会立即采取行动来解决这个问题。"
                ],
                "medium": [
                    "抱歉让您感到不满，我们会认真对待您的反馈并尽快改进。"
                ],
                "low": [
                    "感谢您的反馈，我们会注意这个问题。"
                ]
            },
            "anxious": {
                "high": [
                    "我完全理解您等待了{wait_time}分钟确实很让人焦急。放心，我现在就帮您处理，请稍等片刻。",
                    "让您等了这么久真是抱歉。我理解时间对您来说很宝贵，我会尽快为您完成办理。"
                ],
                "medium": [
                    "抱歉让您久等了，我会尽快为您处理。"
                ],
                "low": [
                    "感谢您的耐心等待。"
                ]
            },
            "confused": {
                "high": [
                    "完全理解您的困惑，这个问题确实可能让人不知所措。请放心，我会一步一步为您解释清楚。",
                    "您问得很好，这个问题值得详细说明。让我来帮您解答..."
                ],
                "medium": [
                    "我来帮您解释一下这个情况。"
                ],
                "low": [
                    "好的，我来为您说明。"
                ]
            }
        }
        
        # 应用筛选
        result = {}
        for emo, levels in templates.items():
            if emotion and emo != emotion.lower():
                continue
            
            result[emo] = {}
            for lvl, scripts in levels.items():
                if level and lvl != level.lower():
                    continue
                result[emo][lvl] = scripts
        
        return APIResponse(
            code=0,
            message="success",
            data={
                "templates": result,
                "total_emotions": len(result)
            }
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get templates: {str(e)}")


@app.post("/empathy/escalation/check", response_model=APIResponse)
async def check_escalation(
    emotion: str = Query(..., description="情绪类型"),
    intensity: float = Query(..., ge=0, le=1, description="情绪强度"),
    duration_seconds: int = Query(0, ge=0, description="持续时间"),
    customer_tier: str = Query("standard", description="客户等级"),
    wait_time_minutes: float = Query(0, description="等待时间")
) -> APIResponse:
    """
    检查是否需要升级
    
    判断当前情况是否需要升级人工处理。
    
    Args:
        emotion: 情绪类型
        intensity: 情绪强度
        duration_seconds: 持续时间
        customer_tier: 客户等级
        wait_time_minutes: 等待时间
    
    Returns:
        升级建议
    """
    try:
        # 构建上下文用于检查
        context = EmpathyContext(
            user_id="temp",
            session_id="temp",
            current_emotion=emotion,
            emotion_intensity=intensity,
            emotion_duration_seconds=duration_seconds,
            wait_time_minutes=wait_time_minutes,
            customer_tier=customer_tier
        )
        
        # 使用response_generator检查升级
        escalation = _response_generator._check_escalation(emotion, context)
        
        return APIResponse(
            code=0,
            message="success",
            data={
                "escalation_required": escalation.get("required", False),
                "reason": escalation.get("reason"),
                "priority": escalation.get("priority"),
                "recommended_actions": [
                    "立即响应客户情绪",
                    "提供同理心回复",
                    "尽快解决问题"
                ] if escalation.get("required") else [
                    "继续当前服务流程",
                    "保持情绪监控"
                ]
            }
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Escalation check failed: {str(e)}")


@app.get("/empathy/sessions/{user_id}", response_model=APIResponse)
async def get_user_sessions(
    user_id: str,
    limit: int = Query(20, ge=1, le=100)
) -> APIResponse:
    """
    获取用户的所有会话
    
    返回指定用户的历史会话列表。
    
    Args:
        user_id: 用户ID
        limit: 返回数量
    
    Returns:
        会话列表
    """
    try:
        user_sessions = [
            {
                "session_id": sid,
                "user_id": conv["user_id"],
                "created_at": conv["created_at"],
                "turn_count": len(_conversation_histories.get(sid, []))
            }
            for sid, conv in _conversations.items()
            if conv["user_id"] == user_id
        ]
        
        # 按创建时间倒序
        user_sessions.sort(key=lambda x: x["created_at"], reverse=True)
        user_sessions = user_sessions[:limit]
        
        return APIResponse(
            code=0,
            message="success",
            data={
                "user_id": user_id,
                "total_sessions": len(user_sessions),
                "sessions": user_sessions
            }
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get sessions: {str(e)}")


@app.get("/empathy/statistics", response_model=APIResponse)
async def get_statistics(
    branch_id: Optional[str] = Query(None, description="网点ID")
) -> APIResponse:
    """
    获取同理心AI服务统计
    
    返回服务统计信息。
    
    Args:
        branch_id: 网点ID筛选
    
    Returns:
        统计数据
    """
    try:
        total_conversations = len(_conversations)
        total_turns = sum(len(h) for h in _conversation_histories.values())
        
        # 计算各情绪水平分布
        empathy_dist = {"high": 0, "medium": 0, "low": 0}
        for history in _conversation_histories.values():
            for turn in history:
                lvl = turn.get("empathy_level", "low")
                empathy_dist[lvl] = empathy_dist.get(lvl, 0) + 1
        
        # 计算平均得分
        all_scores = [
            turn.get("empathy_score", 0) 
            for history in _conversation_histories.values() 
            for turn in history
        ]
        avg_score = sum(all_scores) / len(all_scores) if all_scores else 0
        
        stats = {
            "total_conversations": total_conversations,
            "total_turns": total_turns,
            "avg_empathy_score": round(avg_score, 3),
            "empathy_level_distribution": empathy_dist,
            "active_sessions": sum(
                1 for conv in _conversations.values() 
                if conv.get("status") != "closed"
            )
        }
        
        return APIResponse(code=0, message="success", data=stats)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get statistics: {str(e)}")


# ============== Main ==============

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
