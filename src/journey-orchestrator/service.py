"""
客户旅程编排服务 - FastAPI服务接口
Journey Orchestrator Service - FastAPI Endpoints
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from fastapi import FastAPI, HTTPException, Query, Depends
from pydantic import BaseModel, Field

from .models import (
    Customer360Integrator,
    PersonalizationEngine,
    EventSynchronizer,
    ChannelType,
    EventType,
    CustomerTier,
    RecommendationType,
    Customer360View,
    CrossChannelEvent,
    RecommendationSet
)


# ============== Pydantic Models ==============

class EventCreateRequest(BaseModel):
    """事件创建请求"""
    user_id: str
    event_type: str
    channel: str
    event_data: Dict[str, Any] = Field(default_factory=dict)
    timestamp: Optional[datetime] = None
    session_id: Optional[str] = None
    emotion_state: Optional[Dict[str, float]] = None
    location: Optional[str] = None


class Customer360Response(BaseModel):
    """客户360视图响应"""
    user_id: str
    profile: Dict[str, Any]
    current_session: Optional[Dict[str, Any]]
    journey_summary: Dict[str, Any]
    preferences: Dict[str, Any]
    recent_events: List[Dict[str, Any]]
    generated_at: str


class RecommendationResponse(BaseModel):
    """推荐响应"""
    type: str
    priority: int
    title: str
    description: str
    action_url: str
    confidence: float
    reason: Optional[str] = None


class RecommendationsListResponse(BaseModel):
    """推荐列表响应"""
    user_id: str
    recommendations: List[RecommendationResponse]
    generated_at: str
    model_version: str


class SessionContextRequest(BaseModel):
    """会话上下文请求"""
    session_id: str
    user_id: str
    channel: str
    location: str
    arrived_at: datetime
    emotion_trend: List[str] = Field(default_factory=list)
    current_emotion: Optional[str] = None
    queue_position: Optional[int] = None
    service_type: Optional[str] = None


class EventResponse(BaseModel):
    """事件响应"""
    event_id: str
    user_id: str
    event_type: str
    channel: str
    timestamp: str
    synced: bool = True


class APIResponse(BaseModel):
    """通用API响应"""
    code: int = 0
    message: str = "success"
    data: Optional[Any] = None
    request_id: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


# ============== FastAPI App ==============

app = FastAPI(
    title="Journey Orchestrator Service",
    description="客户旅程编排服务 - 360视图、全渠道同步、个性化推荐",
    version="1.0.0"
)

# 全局实例
_event_synchronizer = EventSynchronizer()
_integrator = Customer360Integrator()
_personalization_engine = PersonalizationEngine()


@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy", "service": "journey-orchestrator"}


@app.post("/journey/events", response_model=APIResponse)
async def record_event(request: EventCreateRequest) -> APIResponse:
    """
    记录客户交互事件
    
    接收来自各渠道的事件数据，进行标准化处理后存储。
    支持渠道包括：Web、移动App、网点、ATM、呼叫中心等。
    
    Args:
        request: 事件数据
    
    Returns:
        创建的事件信息
    """
    try:
        # 转换枚举
        event_type = EventType(request.event_type)
        channel = ChannelType(request.channel)
        
        # 记录事件
        event = _event_synchronizer.record_event(
            user_id=request.user_id,
            event_type=event_type,
            channel=channel,
            event_data=request.event_data,
            timestamp=request.timestamp,
            session_id=request.session_id,
            emotion_state=request.emotion_state,
            location=request.location
        )
        
        return APIResponse(
            code=0,
            message="success",
            data={
                "event_id": event.event_id,
                "user_id": event.user_id,
                "event_type": event.event_type.value,
                "channel": event.channel.value,
                "timestamp": event.timestamp.isoformat(),
                "synced": True
            }
        )
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid event type or channel: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to record event: {str(e)}")


@app.get("/journey/customer/{user_id}", response_model=APIResponse)
async def get_customer_360_view(
    user_id: str,
    include_session: bool = Query(False, description="是否包含当前会话信息"),
    session_channel: Optional[str] = Query(None, description="当前会话渠道"),
    session_location: Optional[str] = Query(None, description="当前会话位置"),
    session_arrived_at: Optional[datetime] = Query(None, description="到达时间")
) -> APIResponse:
    """
    获取客户360视图
    
    整合客户档案、旅程历史、行为数据，构建完整的客户视图。
    
    Args:
        user_id: 用户ID
        include_session: 是否包含当前会话
        session_channel: 当前会话渠道
        session_location: 当前会话位置
        session_arrived_at: 到达时间
    
    Returns:
        客户360视图数据
    """
    try:
        # 构建当前会话上下文
        current_session = None
        if include_session and session_channel:
            from .models import SessionContext
            current_session = SessionContext(
                session_id=f"session_{user_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                user_id=user_id,
                channel=ChannelType(session_channel),
                location=session_location or "未知",
                arrived_at=session_arrived_at or datetime.now(),
                emotion_trend=[],
                current_emotion=None
            )
        
        # 构建360视图
        view = _integrator.build_customer_view(
            user_id=user_id,
            current_session=current_session
        )
        
        # 转换响应格式
        profile_data = {
            "name": view.profile.name,
            "tier": view.profile.tier.value,
            "segments": view.profile.segments,
            "risk_level": view.profile.risk_level
        }
        
        session_data = None
        if view.current_session:
            session_data = {
                "session_id": view.current_session.session_id,
                "channel": view.current_session.channel.value,
                "location": view.current_session.location,
                "arrived_at": view.current_session.arrived_at.isoformat(),
                "emotion_trend": view.current_session.emotion_trend
            }
        
        journey_summary_data = {
            "total_interactions_30d": view.journey_summary.total_interactions_30d,
            "avg_satisfaction": view.journey_summary.avg_satisfaction,
            "preferred_channel": view.journey_summary.preferred_channel.value,
            "last_contact": view.journey_summary.last_contact.isoformat(),
            "pain_points": view.journey_summary.pain_points,
            "success_moments": view.journey_summary.success_moments
        }
        
        return APIResponse(
            code=0,
            message="success",
            data={
                "user_id": view.user_id,
                "profile": profile_data,
                "current_session": session_data,
                "journey_summary": journey_summary_data,
                "preferences": view.preferences,
                "recent_events": view.recent_events,
                "generated_at": view.generated_at.isoformat()
            }
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get customer view: {str(e)}")


@app.get("/journey/recommendations/{user_id}", response_model=APIResponse)
async def get_recommendations(
    user_id: str,
    max_count: int = Query(5, description="最大推荐数量", ge=1, le=20),
    context_tier: Optional[str] = Query(None, description="客户等级上下文"),
    context_channel: Optional[str] = Query(None, description="渠道上下文"),
    context_queue_time: float = Query(0, description="当前排队时间(分钟)")
) -> APIResponse:
    """
    获取个性化推荐
    
    基于客户的旅程历史、当前上下文和偏好，生成个性化推荐列表。
    
    Args:
        user_id: 用户ID
        max_count: 最大推荐数量
        context_tier: 客户等级
        context_channel: 当前渠道
        context_queue_time: 当前排队时间
    
    Returns:
        个性化推荐列表
    """
    try:
        # 构建上下文
        context = {
            "tier": context_tier or "gold",
            "preferred_channel": context_channel or "mobile",
            "queue_wait_time": context_queue_time
        }
        
        # 生成推荐
        rec_set = _personalization_engine.generate_recommendations(
            user_id=user_id,
            context=context,
            max_recommendations=max_count
        )
        
        return APIResponse(
            code=0,
            message="success",
            data={
                "user_id": rec_set.user_id,
                "recommendations": [
                    {
                        "type": r.type.value,
                        "priority": r.priority,
                        "title": r.title,
                        "description": r.description,
                        "action_url": r.action_url,
                        "confidence": r.confidence,
                        "reason": r.reason
                    }
                    for r in rec_set.recommendations
                ],
                "generated_at": rec_set.generated_at.isoformat(),
                "model_version": rec_set.model_version
            }
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate recommendations: {str(e)}")


@app.get("/journey/events/{user_id}", response_model=APIResponse)
async def get_user_events(
    user_id: str,
    event_types: Optional[str] = Query(None, description="事件类型列表，逗号分隔"),
    channels: Optional[str] = Query(None, description="渠道列表，逗号分隔"),
    limit: int = Query(50, description="返回数量", ge=1, le=200)
) -> APIResponse:
    """
    获取用户事件历史
    
    查询指定用户的历史事件记录，支持按类型和渠道筛选。
    
    Args:
        user_id: 用户ID
        event_types: 事件类型筛选
        channels: 渠道筛选
        limit: 返回数量
    
    Returns:
        事件列表
    """
    try:
        # 解析筛选条件
        type_filters = None
        if event_types:
            type_filters = [EventType(t.strip()) for t in event_types.split(",")]
        
        channel_filters = None
        if channels:
            channel_filters = [ChannelType(c.strip()) for c in channels.split(",")]
        
        # 获取事件
        events = _event_synchronizer.get_user_events(
            user_id=user_id,
            event_types=type_filters,
            channels=channel_filters,
            limit=limit
        )
        
        return APIResponse(
            code=0,
            message="success",
            data={
                "user_id": user_id,
                "total": len(events),
                "events": [
                    {
                        "event_id": e.event_id,
                        "event_type": e.event_type.value,
                        "channel": e.channel.value,
                        "timestamp": e.timestamp.isoformat(),
                        "data": e.event_data,
                        "emotion_state": e.emotion_state
                    }
                    for e in events
                ]
            }
        )
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid filter value: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get events: {str(e)}")


@app.get("/journey/patterns/{user_id}", response_model=APIResponse)
async def get_journey_patterns(user_id: str) -> APIResponse:
    """
    获取用户旅程模式
    
    分析用户的行为模式，返回检测到的模式标签。
    
    Args:
        user_id: 用户ID
    
    Returns:
        旅程模式列表
    """
    try:
        patterns = _event_synchronizer.detect_journey_patterns(user_id)
        
        return APIResponse(
            code=0,
            message="success",
            data={
                "user_id": user_id,
                "patterns": patterns
            }
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to detect patterns: {str(e)}")


@app.get("/journey/channels/{user_id}", response_model=APIResponse)
async def get_channel_preference(user_id: str) -> APIResponse:
    """
    获取用户渠道偏好
    
    分析用户在各渠道的活动频率，返回渠道偏好排名。
    
    Args:
        user_id: 用户ID
    
    Returns:
        渠道偏好数据
    """
    try:
        channel_prefs = _event_synchronizer.get_channel_preference(user_id)
        
        # 转换为列表格式并排序
        pref_list = [
            {"channel": ch.value, "count": count}
            for ch, count in channel_prefs.items()
        ]
        pref_list.sort(key=lambda x: x["count"], reverse=True)
        
        # 确定首选渠道
        preferred = pref_list[0]["channel"] if pref_list else "mobile"
        
        return APIResponse(
            code=0,
            message="success",
            data={
                "user_id": user_id,
                "preferred_channel": preferred,
                "channel_breakdown": pref_list
            }
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get channel preference: {str(e)}")


@app.post("/journey/sync", response_model=APIResponse)
async def sync_cross_channel_events(
    events: List[EventCreateRequest]
) -> APIResponse:
    """
    批量同步跨渠道事件
    
    一次接收多个事件，提高批量数据同步效率。
    
    Args:
        events: 事件列表
    
    Returns:
        同步结果统计
    """
    try:
        synced_count = 0
        failed_count = 0
        event_ids = []
        
        for req in events:
            try:
                event_type = EventType(req.event_type)
                channel = ChannelType(req.channel)
                
                event = _event_synchronizer.record_event(
                    user_id=req.user_id,
                    event_type=event_type,
                    channel=channel,
                    event_data=req.event_data,
                    timestamp=req.timestamp,
                    session_id=req.session_id,
                    emotion_state=req.emotion_state,
                    location=req.location
                )
                
                event_ids.append(event.event_id)
                synced_count += 1
            
            except Exception:
                failed_count += 1
        
        return APIResponse(
            code=0,
            message="success",
            data={
                "total": len(events),
                "synced": synced_count,
                "failed": failed_count,
                "event_ids": event_ids
            }
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to sync events: {str(e)}")


# ============== Main ==============

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
