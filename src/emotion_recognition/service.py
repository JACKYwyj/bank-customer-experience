"""
情绪识别服务 - FastAPI服务接口
Emotion Recognition Service - FastAPI Endpoints

基于论文第三章：多模态情绪识别技术架构与网点应用机制
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from fastapi import FastAPI, HTTPException, Query, BackgroundTasks
from pydantic import BaseModel, Field
import uuid

from .models import (
    EmotionType,
    ModalityType,
    EmotionResult,
    MultiModalEmotionResult,
    FacialEmotionResult,
    VocalEmotionResult,
    TextEmotionResult,
    EmotionAlertType,
    EmotionAlert,
    CrossModalFusion,
    EmotionRecognitionEngine
)


# ============== Pydantic Models ==============

class SessionCreateRequest(BaseModel):
    """创建情绪识别会话请求"""
    user_id: str
    session_type: str = Field(default="branch_service", description="会话类型")
    branch_id: Optional[str] = Field(None, description="网点ID")
    channel: str = Field(default="branch", description="渠道")
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SessionCreateResponse(BaseModel):
    """创建情绪识别会话响应"""
    session_id: str
    user_id: str
    session_type: str
    created_at: str
    expires_at: str


class FacialEmotionRequest(BaseModel):
    """面部情绪识别请求"""
    image_data: str = Field(..., description="Base64编码的图像数据")
    quality_threshold: float = Field(default=0.5, ge=0, le=1)


class VocalEmotionRequest(BaseModel):
    """语音情绪识别请求"""
    audio_data: str = Field(..., description="Base64编码的音频数据")
    duration_seconds: float = Field(default=0, ge=0)


class TextEmotionRequest(BaseModel):
    """文本情绪识别请求"""
    text: str = Field(..., min_length=1, max_length=5000)
    language: str = Field(default="zh-CN")


class MultiModalEmotionRequest(BaseModel):
    """多模态情绪识别请求"""
    session_id: str
    facial_data: Optional[str] = Field(None, description="Base64编码的面部图像")
    audio_data: Optional[str] = Field(None, description="Base64编码的音频")
    text: Optional[str] = Field(None, description="文本内容")
    context: Dict[str, Any] = Field(default_factory=dict)


class EmotionRecognitionResponse(BaseModel):
    """情绪识别响应"""
    session_id: str
    timestamp: str
    fused_emotion: Dict[str, Any]
    modalities: List[Dict[str, Any]]
    alert: Optional[Dict[str, Any]] = None
    recommendations: List[str] = []


class EmotionHistoryResponse(BaseModel):
    """情绪历史响应"""
    session_id: str
    user_id: str
    total_records: int
    records: List[Dict[str, Any]]
    emotion_summary: Dict[str, Any]


class SessionEmotionTrend(BaseModel):
    """会话情绪趋势"""
    timestamps: List[str]
    emotions: List[str]
    intensities: List[float]
    valence: List[float]
    arousal: List[float]


class EmotionAlertResponse(BaseModel):
    """情绪告警响应"""
    triggered: bool
    alert_type: Optional[str] = None
    emotion: Optional[str] = None
    intensity: float
    recommendation: Optional[str] = None
    priority: int = 1


class EmotionStatistics(BaseModel):
    """情绪统计数据"""
    total_sessions: int
    avg_positive_rate: float
    avg_intensity: float
    top_emotions: List[Dict[str, Any]]
    alert_count: int


class APIResponse(BaseModel):
    """通用API响应"""
    code: int = 0
    message: str = "success"
    data: Optional[Any] = None
    request_id: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


# ============== FastAPI App ==============

app = FastAPI(
    title="Emotion Recognition Service",
    description="多模态情绪识别服务 - 面部/语音/文本情绪分析",
    version="1.0.0"
)

# 全局实例
_engine = EmotionRecognitionEngine()
_fusion = CrossModalFusion()

# 会话存储 (生产环境应使用Redis)
_sessions: Dict[str, Dict[str, Any]] = {}
_session_histories: Dict[str, List[Dict[str, Any]]] = {}


# ============== Helper Functions ==============

def _create_session_id() -> str:
    """创建会话ID"""
    return f"emo_session_{uuid.uuid4().hex[:16]}"


def _save_recognition_result(session_id: str, result: MultiModalEmotionResult):
    """保存识别结果到历史记录"""
    if session_id not in _session_histories:
        _session_histories[session_id] = []
    
    record = {
        "timestamp": result.timestamp.isoformat(),
        "primary_emotion": result.fused.primary_emotion.value if result.fused else "unknown",
        "confidence": result.fused.primary_confidence if result.fused else 0,
        "valence": result.fused.valence if result.fused else 0,
        "arousal": result.fused.arousal if result.fused else 0,
        "modalities": [m.value for m in result.active_modalities],
        "alert": result.alert
    }
    _session_histories[session_id].append(record)


def _generate_recommendations(result: MultiModalEmotionResult) -> List[str]:
    """基于识别结果生成建议"""
    recommendations = []
    
    if not result.fused:
        return recommendations
    
    emotion = result.fused.primary_emotion
    intensity = result.fused.primary_confidence
    
    # 基于情绪类型生成建议
    if emotion == EmotionType.ANXIETY:
        if intensity > 0.7:
            recommendations.append("建议开启优先服务通道")
            recommendations.append("安排专人接待，减少等待焦虑")
        else:
            recommendations.append("适时提供状态更新，缓解等待焦虑")
    
    elif emotion == EmotionType.ANGER:
        recommendations.append("立即启动服务修复流程")
        recommendations.append("建议人工介入处理")
        if intensity > 0.8:
            recommendations.append("考虑升级至主管处理")
    
    elif emotion == EmotionType.SADNESS:
        recommendations.append("给予更多耐心和关怀")
        recommendations.append("主动询问是否需要帮助")
    
    elif emotion == EmotionType.HAPPINESS or emotion == EmotionType.SATISFACTION:
        recommendations.append("继续保持当前服务水平")
        if intensity > 0.8:
            recommendations.append("可适时邀请客户评价反馈")
    
    elif emotion == EmotionType.NEUTRAL:
        recommendations.append("当前情绪平稳，可正常推进服务")
    
    return recommendations


# ============== API Endpoints ==============

@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy", "service": "emotion-recognition"}


@app.post("/emotion/sessions", response_model=APIResponse)
async def create_emotion_session(request: SessionCreateRequest) -> APIResponse:
    """
    创建情绪识别会话
    
    创建一个新的情绪识别会话，用于跟踪客户在服务过程中的情绪变化。
    
    Args:
        request: 会话创建请求
    
    Returns:
        创建的会话信息
    """
    try:
        session_id = _create_session_id()
        now = datetime.now()
        
        session_data = {
            "session_id": session_id,
            "user_id": request.user_id,
            "session_type": request.session_type,
            "branch_id": request.branch_id,
            "channel": request.channel,
            "metadata": request.metadata,
            "created_at": now,
            "expires_at": now.replace(hour=23, minute=59, second=59),  # 当日有效
            "status": "active"
        }
        
        _sessions[session_id] = session_data
        _session_histories[session_id] = []
        
        return APIResponse(
            code=0,
            message="success",
            data={
                "session_id": session_id,
                "user_id": request.user_id,
                "session_type": request.session_type,
                "created_at": now.isoformat(),
                "expires_at": session_data["expires_at"].isoformat()
            }
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create session: {str(e)}")


@app.post("/emotion/recognize", response_model=APIResponse)
async def recognize_emotion(request: MultiModalEmotionRequest) -> APIResponse:
    """
    多模态情绪识别
    
    融合面部、语音、文本三个模态的识别结果，输出综合情绪判断。
    至少需要提供一种模态数据。
    
    Args:
        request: 多模态情绪识别请求
    
    Returns:
        融合后的情绪识别结果
    """
    try:
        # 验证会话
        if request.session_id not in _sessions:
            raise HTTPException(status_code=404, detail=f"Session {request.session_id} not found")
        
        # 执行识别
        result = _engine.recognize_from_multi_modal(
            session_id=request.session_id,
            facial_data=request.facial_data.encode() if request.facial_data else None,
            audio_data=request.audio_data.encode() if request.audio_data else None,
            text=request.text
        )
        
        # 保存历史
        _save_recognition_result(request.session_id, result)
        
        # 转换响应格式
        fused_data = None
        if result.fused:
            fused_data = {
                "primary_emotion": result.fused.primary_emotion.value,
                "primary_confidence": round(result.fused.primary_confidence, 3),
                "secondary_emotion": result.fused.secondary_emotion.value if result.fused.secondary_emotion else None,
                "secondary_confidence": round(result.fused.secondary_confidence, 3) if result.fused.secondary_confidence else None,
                "valence": round(result.fused.valence, 3),
                "arousal": round(result.fused.arousal, 3),
                "fused_confidence": round(result.fused.fused_confidence, 3)
            }
        
        modalities_data = []
        if result.has_face and result.facial:
            modalities_data.append({
                "type": "facial",
                "emotion": result.facial.emotion.value,
                "confidence": round(result.facial.confidence, 3),
                "quality_score": round(result.facial.quality_score, 3)
            })
        
        if result.has_vocal and result.vocal:
            modalities_data.append({
                "type": "vocal",
                "emotion": result.vocal.emotion.value,
                "confidence": round(result.vocal.confidence, 3),
                "pitch_avg": round(result.vocal.pitch_avg, 1),
                "speech_rate": round(result.vocal.speech_rate, 2)
            })
        
        if result.has_text and result.text:
            modalities_data.append({
                "type": "text",
                "emotion": result.text.emotion.value,
                "confidence": round(result.text.confidence, 3),
                "sentiment_score": round(result.text.sentiment_score, 3)
            })
        
        # 生成建议
        recommendations = _generate_recommendations(result)
        
        return APIResponse(
            code=0,
            message="success",
            data={
                "session_id": request.session_id,
                "timestamp": result.timestamp.isoformat(),
                "fused_emotion": fused_data,
                "modalities": modalities_data,
                "active_modalities": [m.value for m in result.active_modalities],
                "alert": result.alert,
                "recommendations": recommendations
            }
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Recognition failed: {str(e)}")


@app.get("/emotion/sessions/{session_id}/history", response_model=APIResponse)
async def get_emotion_history(
    session_id: str,
    limit: int = Query(50, ge=1, le=200, description="返回记录数")
) -> APIResponse:
    """
    获取会话情绪历史记录
    
    返回指定会话的所有情绪识别历史，用于分析情绪变化趋势。
    
    Args:
        session_id: 会话ID
        limit: 返回记录数限制
    
    Returns:
        情绪历史记录及摘要
    """
    try:
        # 验证会话存在
        if session_id not in _sessions:
            raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
        
        session = _sessions[session_id]
        history = _session_histories.get(session_id, [])[-limit:]
        
        # 生成摘要
        emotion_summary = {}
        if history:
            emotion_counts = {}
            total_intensity = 0
            positive_count = 0
            
            for record in history:
                emo = record["primary_emotion"]
                emotion_counts[emo] = emotion_counts.get(emo, 0) + 1
                total_intensity += record["confidence"]
                
                if emo in ["happiness", "satisfaction"]:
                    positive_count += 1
            
            emotion_summary = {
                "total_records": len(history),
                "emotion_distribution": emotion_counts,
                "avg_intensity": round(total_intensity / len(history), 3),
                "positive_rate": round(positive_count / len(history), 3),
                "dominant_emotion": max(emotion_counts, key=emotion_counts.get) if emotion_counts else "neutral"
            }
        
        return APIResponse(
            code=0,
            message="success",
            data={
                "session_id": session_id,
                "user_id": session["user_id"],
                "total_records": len(history),
                "records": history,
                "emotion_summary": emotion_summary
            }
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get history: {str(e)}")


@app.get("/emotion/sessions/{session_id}/trend", response_model=APIResponse)
async def get_emotion_trend(session_id: str) -> APIResponse:
    """
    获取会话情绪趋势
    
    返回情绪随时间变化的趋势数据，用于可视化。
    
    Args:
        session_id: 会话ID
    
    Returns:
        情绪趋势数据
    """
    try:
        if session_id not in _sessions:
            raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
        
        history = _session_histories.get(session_id, [])
        
        if not history:
            return APIResponse(
                code=0,
                message="success",
                data={
                    "session_id": session_id,
                    "timestamps": [],
                    "emotions": [],
                    "intensities": [],
                    "valence": [],
                    "arousal": []
                }
            )
        
        trend = SessionEmotionTrend(
            timestamps=[r["timestamp"] for r in history],
            emotions=[r["primary_emotion"] for r in history],
            intensities=[r["confidence"] for r in history],
            valence=[r["valence"] for r in history],
            arousal=[r["arousal"] for r in history]
        )
        
        return APIResponse(
            code=0,
            message="success",
            data=trend.model_dump()
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get trend: {str(e)}")


@app.post("/emotion/analyze/text", response_model=APIResponse)
async def analyze_text_emotion(request: TextEmotionRequest) -> APIResponse:
    """
    文本情绪分析
    
    对文本内容进行情绪分析，支持中文和英文。
    
    Args:
        request: 文本情绪分析请求
    
    Returns:
        文本情绪分析结果
    """
    try:
        # 模拟文本情绪分析
        negative_keywords = ["慢", "等", "投诉", "生气", "着急", "不满意", "差", "烂", "垃圾", "退款", "退钱", "投诉"]
        positive_keywords = ["好", "谢谢", "满意", "快", "方便", "不错", "棒", "赞", "优秀", "专业"]
        
        text_lower = request.text.lower()
        neg_count = sum(1 for k in negative_keywords if k in text_lower)
        pos_count = sum(1 for k in positive_keywords if k in text_lower)
        
        if neg_count > pos_count:
            emotion = EmotionType.ANXIETY
            confidence = min(0.95, 0.6 + neg_count * 0.05)
        elif pos_count > neg_count:
            emotion = EmotionType.SATISFACTION
            confidence = min(0.95, 0.6 + pos_count * 0.05)
        else:
            emotion = EmotionType.NEUTRAL
            confidence = 0.6
        
        text_result = TextEmotionResult(
            emotion=emotion,
            confidence=confidence,
            keywords=[k for k in negative_keywords + positive_keywords if k in text_lower],
            sentiment_score=round((pos_count - neg_count) / max(1, pos_count + neg_count), 2)
        )
        
        return APIResponse(
            code=0,
            message="success",
            data={
                "emotion": text_result.emotion.value,
                "confidence": round(text_result.confidence, 3),
                "sentiment_score": round(text_result.sentiment_score, 3),
                "keywords": text_result.keywords,
                "language": request.language
            }
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Text analysis failed: {str(e)}")


@app.post("/emotion/check-alert", response_model=APIResponse)
async def check_emotion_alert(
    emotion: str = Query(..., description="情绪类型"),
    intensity: float = Query(..., ge=0, le=1, description="情绪强度"),
    wait_time_minutes: float = Query(0, description="等待时间(分钟)")
) -> APIResponse:
    """
    检查情绪告警
    
    根据当前情绪状态判断是否需要触发告警。
    
    Args:
        emotion: 情绪类型
        intensity: 情绪强度
        wait_time_minutes: 等待时间
    
    Returns:
        告警信息
    """
    try:
        emotion_enum = EmotionType(emotion)
        
        alert = _fusion.check_alert(
            current_emotion=emotion_enum,
            intensity=intensity,
            emotion_history=[],
            wait_time_minutes=wait_time_minutes
        )
        
        return APIResponse(
            code=0,
            message="success",
            data={
                "triggered": alert.triggered,
                "alert_type": alert.alert_type.value if alert.alert_type else None,
                "emotion": alert.emotion.value if alert.emotion else None,
                "intensity": alert.intensity,
                "recommendation": alert.recommendation,
                "priority": 1 if alert.triggered else 0
            }
        )
    
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid emotion type: {emotion}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Alert check failed: {str(e)}")


@app.get("/emotion/sessions/{session_id}", response_model=APIResponse)
async def get_session_info(session_id: str) -> APIResponse:
    """
    获取会话信息
    
    返回指定会话的基本信息。
    
    Args:
        session_id: 会话ID
    
    Returns:
        会话信息
    """
    try:
        if session_id not in _sessions:
            raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
        
        session = _sessions[session_id]
        history_count = len(_session_histories.get(session_id, []))
        
        return APIResponse(
            code=0,
            message="success",
            data={
                "session_id": session_id,
                "user_id": session["user_id"],
                "session_type": session["session_type"],
                "branch_id": session.get("branch_id"),
                "channel": session["channel"],
                "status": session["status"],
                "created_at": session["created_at"].isoformat(),
                "expires_at": session["expires_at"].isoformat(),
                "record_count": history_count
            }
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get session: {str(e)}")


@app.delete("/emotion/sessions/{session_id}", response_model=APIResponse)
async def close_session(session_id: str) -> APIResponse:
    """
    关闭情绪识别会话
    
    关闭指定会话，释放相关资源。
    
    Args:
        session_id: 会话ID
    
    Returns:
        操作结果
    """
    try:
        if session_id not in _sessions:
            raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
        
        _sessions[session_id]["status"] = "closed"
        record_count = len(_session_histories.get(session_id, []))
        
        return APIResponse(
            code=0,
            message="success",
            data={
                "session_id": session_id,
                "status": "closed",
                "records_preserved": record_count
            }
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to close session: {str(e)}")


@app.get("/emotion/statistics", response_model=APIResponse)
async def get_statistics(
    branch_id: Optional[str] = Query(None, description="网点ID"),
    date: Optional[str] = Query(None, description="日期 YYYY-MM-DD")
) -> APIResponse:
    """
    获取情绪统计数据
    
    返回指定条件下的情绪统计数据。
    
    Args:
        branch_id: 网点ID筛选
        date: 日期筛选
    
    Returns:
        统计数据
    """
    try:
        # 聚合所有会话的历史记录
        all_records = []
        for session_id, session in _sessions.items():
            if branch_id and session.get("branch_id") != branch_id:
                continue
            history = _session_histories.get(session_id, [])
            all_records.extend(history)
        
        if not all_records:
            return APIResponse(
                code=0,
                message="success",
                data={
                    "total_sessions": 0,
                    "avg_positive_rate": 0,
                    "avg_intensity": 0,
                    "top_emotions": [],
                    "alert_count": 0
                }
            )
        
        # 计算统计
        emotion_counts = {}
        total_intensity = 0
        positive_count = 0
        alert_count = 0
        
        for record in all_records:
            emo = record["primary_emotion"]
            emotion_counts[emo] = emotion_counts.get(emo, 0) + 1
            total_intensity += record["confidence"]
            
            if emo in ["happiness", "satisfaction"]:
                positive_count += 1
            
            if record.get("alert", {}).get("triggered"):
                alert_count += 1
        
        top_emotions = sorted(
            [{"emotion": k, "count": v} for k, v in emotion_counts.items()],
            key=lambda x: x["count"],
            reverse=True
        )[:5]
        
        stats = EmotionStatistics(
            total_sessions=len(_sessions),
            avg_positive_rate=round(positive_count / len(all_records), 3),
            avg_intensity=round(total_intensity / len(all_records), 3),
            top_emotions=top_emotions,
            alert_count=alert_count
        )
        
        return APIResponse(
            code=0,
            message="success",
            data=stats.model_dump()
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get statistics: {str(e)}")


# ============== Main ==============

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
