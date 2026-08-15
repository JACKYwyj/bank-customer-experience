"""
情绪识别模块 - 多模态情绪分析引擎
Emotion Recognition Module - Multi-modal Emotion Analysis Engine

基于论文第三章：多模态情绪识别技术架构与网点应用机制
"""

from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Dict, Any
from datetime import datetime
import numpy as np


class EmotionType(Enum):
    """情绪类型枚举"""
    NEUTRAL = "neutral"
    HAPPINESS = "happiness"
    SADNESS = "sadness"
    ANGER = "anger"
    FEAR = "fear"
    SURPRISE = "surprise"
    DISGUST = "disgust"
    ANXIETY = "anxiety"
    CONFUSION = "confusion"
    SATISFACTION = "satisfaction"


class ModalityType(Enum):
    """模态类型"""
    FACIAL = "facial"
    VOCAL = "vocal"
    TEXT = "text"


@dataclass
class EmotionResult:
    """情绪识别结果"""
    primary_emotion: EmotionType
    primary_confidence: float
    secondary_emotion: Optional[EmotionType] = None
    secondary_confidence: Optional[float] = None
    valence: float = 0.0  # 效价: -1(消极) ~ 1(积极)
    arousal: float = 0.0  # 唤醒度: 0 ~ 1
    fused_confidence: float = 0.0
    modalities: List[ModalityType] = None
    
    def __post_init__(self):
        if self.modalities is None:
            self.modalities = []


@dataclass 
class FacialEmotionResult:
    """面部情绪识别结果"""
    emotion: EmotionType
    confidence: float
    landmarks: List[List[float]] = None
    quality_score: float = 0.0
    face_bbox: List[int] = None


@dataclass
class VocalEmotionResult:
    """语音情绪识别结果"""
    emotion: EmotionType
    confidence: float
    pitch_avg: float = 0.0
    speech_rate: float = 0.0
    energy: float = 0.0


@dataclass
class TextEmotionResult:
    """文本情绪识别结果"""
    emotion: EmotionType
    confidence: float
    keywords: List[str] = None
    sentiment_score: float = 0.0


@dataclass
class MultiModalEmotionResult:
    """多模态融合情绪识别结果"""
    session_id: str
    timestamp: datetime
    facial: Optional[FacialEmotionResult] = None
    vocal: Optional[VocalEmotionResult] = None
    text: Optional[TextEmotionResult] = None
    fused: Optional[EmotionResult] = None
    alert: Optional[Dict[str, Any]] = None
    
    @property
    def has_face(self) -> bool:
        return self.facial is not None and self.facial.confidence > 0.5
    
    @property
    def has_vocal(self) -> bool:
        return self.vocal is not None and self.vocal.confidence > 0.5
    
    @property
    def has_text(self) -> bool:
        return self.text is not None and self.text.confidence > 0.5
    
    @property
    def active_modalities(self) -> List[ModalityType]:
        mods = []
        if self.has_face:
            mods.append(ModalityType.FACIAL)
        if self.has_vocal:
            mods.append(ModalityType.VOCAL)
        if self.has_text:
            mods.append(ModalityType.TEXT)
        return mods


class EmotionAlertType(Enum):
    """情绪告警类型"""
    NEGATIVE_EMOTION_ESCALATION = "negative_emotion_escalation"  # 负面情绪升级
    LONG_TERM_ANXIETY = "long_term_anxiety"  # 持续焦虑
    CONFLICT_RISK = "conflict_risk"  # 冲突风险
    CUSTOMER_LEAVING = "customer_leaving"  # 客户即将离开
    SERVICE_RECOVERY_NEEDED = "service_recovery_needed"  # 需要服务修复


@dataclass
class EmotionAlert:
    """情绪告警"""
    triggered: bool = False
    alert_type: Optional[EmotionAlertType] = None
    emotion: Optional[EmotionType] = None
    intensity: float = 0.0
    recommendation: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "triggered": self.triggered,
            "type": self.alert_type.value if self.alert_type else None,
            "emotion": self.emotion.value if self.emotion else None,
            "intensity": self.intensity,
            "recommendation": self.recommendation
        }


class CrossModalFusion:
    """
    跨模态融合网络
    
    实现论文中的跨模态共享网络与分布约束，
    将面部、语音、文本三个模态的的情绪特征进行融合
    """
    
    # 情绪类别数
    NUM_CLASSES = len(EmotionType)
    
    # 负面情绪列表（用于告警触发）
    NEGATIVE_EMOTIONS = {
        EmotionType.ANGER, 
        EmotionType.ANXIETY, 
        EmotionType.FEAR,
        EmotionType.SADNESS,
        EmotionType.DISGUST
    }
    
    def __init__(self, model_config: Optional[Dict[str, Any]] = None):
        self.config = model_config or {}
        self.weights = self.config.get("fusion_weights", {
            ModalityType.FACIAL: 0.4,
            ModalityType.VOCAL: 0.35,
            ModalityType.TEXT: 0.25
        })
        
    def fuse(
        self,
        facial_result: Optional[FacialEmotionResult],
        vocal_result: Optional[VocalEmotionResult],
        text_result: Optional[TextEmotionResult]
    ) -> MultiModalEmotionResult:
        """
        融合多模态情绪识别结果
        
        Args:
            facial_result: 面部情绪结果
            vocal_result: 语音情绪结果
            text_result: 文本情绪结果
            
        Returns:
            MultiModalEmotionResult: 融合后的多模态结果
        """
        # 统计各模态的置信度
        active_mods = []
        mod_weights = []
        mod_confidences = []
        
        if facial_result and facial_result.confidence > 0.5:
            active_mods.append(ModalityType.FACIAL)
            mod_weights.append(self.weights[ModalityType.FACIAL])
            mod_confidences.append(facial_result.confidence)
            
        if vocal_result and vocal_result.confidence > 0.5:
            active_mods.append(ModalityType.VOCAL)
            mod_weights.append(self.weights[ModalityType.VOCAL])
            mod_confidences.append(vocal_result.confidence)
            
        if text_result and text_result.confidence > 0.5:
            active_mods.append(ModalityType.TEXT)
            mod_weights.append(self.weights[ModalityType.TEXT])
            mod_confidences.append(text_result.confidence)
        
        # 如果没有有效模态，返回默认结果
        if not active_mods:
            return MultiModalEmotionResult(
                session_id="",
                timestamp=datetime.now(),
                fused=EmotionResult(
                    primary_emotion=EmotionType.NEUTRAL,
                    primary_confidence=0.5,
                    fused_confidence=0.5,
                    modalities=[]
                )
            )
        
        # 归一化权重
        total_weight = sum(mod_weights)
        normalized_weights = [w / total_weight for w in mod_weights]
        
        # 加权融合各模态的置信度
        fused_confidence = sum(
            w * c for w, c in zip(normalized_weights, mod_confidences)
        )
        
        # 确定主要情绪（选择置信度最高的模态的主要情绪）
        primary_emotion = EmotionType.NEUTRAL
        if facial_result and facial_result.confidence > 0.5:
            primary_emotion = facial_result.emotion
        elif vocal_result and vocal_result.confidence > 0.5:
            primary_emotion = vocal_result.emotion
        elif text_result and text_result.confidence > 0.5:
            primary_emotion = text_result.emotion
            
        # 构建融合结果
        fused_result = EmotionResult(
            primary_emotion=primary_emotion,
            primary_confidence=fused_confidence,
            fused_confidence=fused_confidence,
            modalities=active_mods
        )
        
        # 估算效价和唤醒度
        fused_result.valence = self._estimate_valence(primary_emotion)
        fused_result.arousal = self._estimate_arousal(primary_emotion, fused_confidence)
        
        # 构建完整结果
        return MultiModalEmotionResult(
            session_id="",
            timestamp=datetime.now(),
            facial=facial_result,
            vocal=vocal_result,
            text=text_result,
            fused=fused_result
        )
    
    def _estimate_valence(self, emotion: EmotionType) -> float:
        """估算情绪效价"""
        valence_map = {
            EmotionType.HAPPINESS: 0.8,
            EmotionType.SATISFACTION: 0.6,
            EmotionType.SURPRISE: 0.2,
            EmotionType.NEUTRAL: 0.0,
            EmotionType.CONFUSION: -0.3,
            EmotionType.ANXIETY: -0.5,
            EmotionType.SADNESS: -0.6,
            EmotionType.FEAR: -0.7,
            EmotionType.DISGUST: -0.7,
            EmotionType.ANGER: -0.8
        }
        return valence_map.get(emotion, 0.0)
    
    def _estimate_arousal(self, emotion: EmotionType, confidence: float) -> float:
        """估算情绪唤醒度"""
        arousal_map = {
            EmotionType.ANGER: 0.9,
            EmotionType.FEAR: 0.85,
            EmotionType.ANXIETY: 0.7,
            EmotionType.SURPRISE: 0.8,
            EmotionType.HAPPINESS: 0.6,
            EmotionType.SATISFACTION: 0.5,
            EmotionType.CONFUSION: 0.5,
            EmotionType.NEUTRAL: 0.3,
            EmotionType.SADNESS: 0.3,
            EmotionType.DISGUST: 0.6
        }
        base = arousal_map.get(emotion, 0.5)
        return min(1.0, base * confidence)
    
    def check_alert(
        self,
        current_emotion: EmotionType,
        intensity: float,
        emotion_history: List[EmotionResult],
        wait_time_minutes: float = 0
    ) -> EmotionAlert:
        """
        检查是否需要触发告警
        
        Args:
            current_emotion: 当前情绪
            intensity: 情绪强度
            emotion_history: 情绪历史记录
            wait_time_minutes: 等待时间（分钟）
            
        Returns:
            EmotionAlert: 告警信息
        """
        # 检查是否是负面情绪且强度较高
        if current_emotion in self.NEGATIVE_EMOTIONS and intensity > 0.7:
            # 检查是否持续时间较长
            if len(emotion_history) >= 3:
                recent_emotions = [r.primary_emotion for r in emotion_history[-3:]]
                if all(e in self.NEGATIVE_EMOTIONS for e in recent_emotions):
                    return EmotionAlert(
                        triggered=True,
                        alert_type=EmotionAlertType.NEGATIVE_EMOTION_ESCALATION,
                        emotion=current_emotion,
                        intensity=intensity,
                        recommendation="建议立即启动服务修复流程"
                    )
            
            # 检查情绪强度是否很高
            if intensity > 0.85:
                return EmotionAlert(
                    triggered=True,
                    alert_type=EmotionAlertType.CONFLICT_RISK,
                    emotion=current_emotion,
                    intensity=intensity,
                    recommendation="建议人工立即介入处理"
                )
        
        # 检查持续焦虑（等待时间较长）
        if current_emotion == EmotionType.ANXIETY and wait_time_minutes > 15:
            return EmotionAlert(
                triggered=True,
                alert_type=EmotionAlertType.LONG_TERM_ANXIETY,
                emotion=current_emotion,
                intensity=intensity,
                recommendation="客户等待时间较长，建议优先服务"
            )
        
        return EmotionAlert(triggered=False)


class EmotionRecognitionEngine:
    """
    情绪识别引擎主类
    
    整合面部、语音、文本三个模态的识别能力，
    提供统一的情绪识别接口
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.fusion = CrossModalFusion(self.config)
        
    def recognize_from_multi_modal(
        self,
        session_id: str,
        facial_data: Optional[bytes] = None,
        audio_data: Optional[bytes] = None,
        text: Optional[str] = None
    ) -> MultiModalEmotionResult:
        """
        从多模态数据识别情绪
        
        Args:
            session_id: 会话ID
            facial_data: 面部图像数据
            audio_data: 音频数据
            text: 文本内容
        """
        # 这里应该调用实际的模型进行推理
        # 为了演示，返回模拟结果
        
        facial_result = None
        vocal_result = None
        text_result = None
        
        # 模拟面部识别
        if facial_data:
            facial_result = FacialEmotionResult(
                emotion=EmotionType.ANXIETY,
                confidence=0.85,
                quality_score=0.9
            )
        
        # 模拟语音识别
        if audio_data:
            vocal_result = VocalEmotionResult(
                emotion=EmotionType.ANXIETY,
                confidence=0.78,
                pitch_avg=220.0,
                speech_rate=2.1
            )
        
        # 模拟文本识别
        if text:
            # 简单的关键词判断
            negative_keywords = ["慢", "等", "投诉", "生气", "着急", "不满意"]
            positive_keywords = ["好", "谢谢", "满意", "快", "方便"]
            
            text_lower = text.lower()
            neg_count = sum(1 for k in negative_keywords if k in text_lower)
            pos_count = sum(1 for k in positive_keywords if k in text_lower)
            
            if neg_count > pos_count:
                text_emotion = EmotionType.ANXIETY
                text_conf = 0.75
            elif pos_count > neg_count:
                text_emotion = EmotionType.SATISFACTION
                text_conf = 0.70
            else:
                text_emotion = EmotionType.NEUTRAL
                text_conf = 0.60
                
            text_result = TextEmotionResult(
                emotion=text_emotion,
                confidence=text_conf,
                keywords=[k for k in negative_keywords + positive_keywords if k in text_lower]
            )
        
        # 融合结果
        result = self.fusion.fuse(facial_result, vocal_result, text_result)
        result.session_id = session_id
        result.timestamp = datetime.now()
        
        # 检查告警
        if result.fused:
            alert = self.fusion.check_alert(
                result.fused.primary_emotion,
                result.fused.primary_confidence,
                [],  # 实际使用时传入历史记录
                0    # 实际使用时传入等待时间
            )
            result.alert = alert.to_dict()
        
        return result


# 示例使用
if __name__ == "__main__":
    engine = EmotionRecognitionEngine()
    
    # 模拟一次情绪识别
    result = engine.recognize_from_multi_modal(
        session_id="test_session_001",
        text="等太久了，我要投诉！"
    )
    
    print(f"Session: {result.session_id}")
    print(f"Fused Emotion: {result.fused.primary_emotion.value if result.fused else 'N/A'}")
    print(f"Confidence: {result.fused.fused_confidence if result.fused else 0:.2f}")
    print(f"Modalities: {[m.value for m in result.fused.modalities] if result.fused else []}")
    print(f"Alert: {result.alert}")
