"""
情绪识别模块 - 多模态情绪分析引擎
Emotion Recognition Module - Multi-modal Emotion Analysis Engine

基于论文第三章：多模态情绪识别技术架构与网点应用机制

端侧模型选型：
- 文本情绪：DistilBERT-sentiment (88M params, ONNX优化)
- 面部情绪：MiniXCEPTION (1.4M params, 专为端侧优化)
- 语音情绪：wav2vec2-base-emotion (95M params, 支持中文)
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Dict, Any, Tuple, Union
from datetime import datetime
import numpy as np
import json
import base64
from pathlib import Path


# ============== 情绪类型枚举 ==============

class EmotionType(Enum):
    """情绪类型枚举（基于论文设计的六类情绪）"""
    NEUTRAL = "neutral"           # 中性
    ANXIETY = "anxiety"           # 焦虑
    ANGER = "anger"               # 愤怒
    FRUSTRATION = "frustration"   # 受挫
    CONFUSION = "confusion"       # 困惑
    SATISFACTION = "satisfaction" # 满意
    # 扩展情绪（用于更细粒度分析）
    HAPPINESS = "happiness"
    SADNESS = "sadness"
    FEAR = "fear"
    SURPRISE = "surprise"


class ModalityType(Enum):
    """模态类型"""
    FACIAL = "facial"
    VOCAL = "vocal"
    TEXT = "text"


class ModelBackend(Enum):
    """模型后端类型"""
    MOCK = "mock"           # 模拟（原型阶段）
    TRANSFORMERS = "transformers"  # HuggingFace Transformers
    ONNX = "onnx"           # ONNX Runtime（端侧优化）
    TORCH = "torch"         # PyTorch
    TFLITE = "tflite"       # TensorFlow Lite（移动端）


# ============== 数据模型 ==============

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
    modalities: List[ModalityType] = field(default_factory=list)
    model_version: str = "1.0.0"
    inference_time_ms: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "primary_emotion": self.primary_emotion.value,
            "primary_confidence": round(self.primary_confidence, 4),
            "secondary_emotion": self.secondary_emotion.value if self.secondary_emotion else None,
            "secondary_confidence": round(self.secondary_confidence, 4) if self.secondary_confidence else None,
            "valence": round(self.valence, 4),
            "arousal": round(self.arousal, 4),
            "fused_confidence": round(self.fused_confidence, 4),
            "modalities": [m.value for m in self.modalities],
            "model_version": self.model_version,
            "inference_time_ms": round(self.inference_time_ms, 2)
        }


@dataclass 
class FacialEmotionResult:
    """面部情绪识别结果"""
    emotion: EmotionType
    confidence: float
    quality_score: float = 0.0
    face_detected: bool = True
    face_count: int = 1
    bbox: Optional[List[int]] = None  # [x1, y1, x2, y2]
    landmarks: Optional[List[List[float]]] = None
    # 扩展属性（用于详细分析）
    emotion_probs: Optional[Dict[str, float]] = None


@dataclass
class VocalEmotionResult:
    """语音情绪识别结果"""
    emotion: EmotionType
    confidence: float
    duration_seconds: float = 0.0
    sample_rate: int = 16000
    # 声学特征
    pitch_avg: float = 0.0
    pitch_std: float = 0.0
    energy: float = 0.0
    speech_rate: float = 0.0
    # 扩展属性
    emotion_probs: Optional[Dict[str, float]] = None
    features: Optional[List[float]] = None


@dataclass
class TextEmotionResult:
    """文本情绪识别结果"""
    emotion: EmotionType
    confidence: float
    language: str = "zh-CN"
    keywords: List[str] = field(default_factory=list)
    sentiment_score: float = 0.0  # -1 ~ 1
    # 扩展属性
    emotion_probs: Optional[Dict[str, float]] = None
    token_count: int = 0
    language_confidence: float = 0.0


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
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "timestamp": self.timestamp.isoformat(),
            "facial": {
                "emotion": self.facial.emotion.value if self.facial else None,
                "confidence": round(self.facial.confidence, 4) if self.facial else None,
                "quality_score": round(self.facial.quality_score, 4) if self.facial else None
            } if self.facial else None,
            "vocal": {
                "emotion": self.vocal.emotion.value if self.vocal else None,
                "confidence": round(self.vocal.confidence, 4) if self.vocal else None,
                "pitch_avg": round(self.vocal.pitch_avg, 2) if self.vocal else None
            } if self.vocal else None,
            "text": {
                "emotion": self.text.emotion.value if self.text else None,
                "confidence": round(self.text.confidence, 4) if self.text else None,
                "keywords": self.text.keywords if self.text else None
            } if self.text else None,
            "fused": self.fused.to_dict() if self.fused else None,
            "alert": self.alert,
            "active_modalities": [m.value for m in self.active_modalities]
        }


class EmotionAlertType(Enum):
    """情绪告警类型（基于论文第四章）"""
    NEGATIVE_EMOTION_ESCALATION = "negative_emotion_escalation"  # 负面情绪升级
    LONG_TERM_ANXIETY = "long_term_anxiety"  # 持续焦虑
    CONFLICT_RISK = "conflict_risk"  # 冲突风险
    CUSTOMER_LEAVING = "customer_leaving"  # 客户即将离开
    SERVICE_RECOVERY_NEEDED = "service_recovery_needed"  # 需要服务修复


@dataclass
class EmotionAlert:
    """情绪告警（基于论文第四章告警规则设计）"""
    triggered: bool = False
    alert_type: Optional[EmotionAlertType] = None
    emotion: Optional[EmotionType] = None
    intensity: float = 0.0
    duration_seconds: int = 0
    recommendation: Optional[str] = None
    priority: int = 1  # 1-5, 1最高
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "triggered": self.triggered,
            "type": self.alert_type.value if self.alert_type else None,
            "emotion": self.emotion.value if self.emotion else None,
            "intensity": round(self.intensity, 4),
            "duration_seconds": self.duration_seconds,
            "recommendation": self.recommendation,
            "priority": self.priority
        }


# ============== 端侧模型配置 ==============

class EdgeModelConfig:
    """端侧模型配置"""
    
    # 文本情绪模型（支持中文，轻量级）
    TEXT_MODEL_CONFIG = {
        "name": "uer/roberta-base-finetuned-jd-binary-chinese",
        "type": "text",
        "backend": ModelBackend.TRANSFORMERS,
        "max_length": 128,
        "params": "102M",
        "description": "中文文本情绪分类（正面/负面）"
    }
    
    # 面部情绪模型（端侧优化）
    FACIAL_MODEL_CONFIG = {
        "name": "privutsa/face-expression-recognition",
        "type": "facial",
        "backend": ModelBackend.ONNX,
        "input_size": (64, 64),
        "params": "1.4M",
        "description": "面部表情识别（7类情绪）"
    }
    
    # 语音情绪模型
    VOCAL_MODEL_CONFIG = {
        "name": "huggingface/ wav2vec2-base-emotion Recognition",
        "type": "vocal",
        "backend": ModelBackend.TRANSFORMERS,
        "sample_rate": 16000,
        "params": "95M",
        "description": "语音情绪识别"
    }
    
    # 多模态融合配置（基于论文权重设计）
    FUSION_CONFIG = {
        "weights": {
            "facial": 0.40,
            "vocal": 0.35,
            "text": 0.25
        },
        "confidence_threshold": 0.5,
        "description": "多模态融合权重（原型初始参数，基于研究论文设计）"
    }
    
    # 告警规则配置（基于论文第四章表1）
    ALERT_RULES = {
        "anxiety": {
            "threshold": 0.5,
            "duration_seconds": 60,
            "recommendation": "先解释进度并观察；中等信号持续出现时避免过度干预",
            "priority": 3
        },
        "anger": {
            "threshold": 0.8,
            "duration_seconds": 30,
            "recommendation": "建议人工接手或主管协调；高风险信号应快速响应",
            "priority": 1
        },
        "frustration": {
            "threshold": 0.6,
            "duration_seconds": 90,
            "recommendation": "建议服务修复与人工协助；持续受阻后再介入",
            "priority": 2
        }
    }


# ============== 跨模态融合网络 ==============

class CrossModalFusion:
    """
    跨模态融合网络（Cross-Modal Fusion Network）
    
    实现论文中的跨模态共享网络与分布约束，
    将面部、语音、文本三个模态的的情绪特征进行融合
    
    融合权重（原型初始参数，基于研究论文设计）：
    - 面部表情: 0.40
    - 语音语调: 0.35
    - 文本语义: 0.25
    """
    
    NUM_CLASSES = len(EmotionType)
    
    NEGATIVE_EMOTIONS = {
        EmotionType.ANGER, 
        EmotionType.ANXIETY, 
        EmotionType.FRUSTRATION,
        EmotionType.SADNESS,
        EmotionType.FEAR,
        EmotionType.CONFUSION
    }
    
    def __init__(self, model_config: Optional[Dict[str, Any]] = None):
        self.config = model_config or {}
        # 默认融合权重（可配置）
        self.weights = self.config.get("fusion_weights", {
            ModalityType.FACIAL: 0.40,
            ModalityType.VOCAL: 0.35,
            ModalityType.TEXT: 0.25
        })
        # 置信度阈值
        self.confidence_threshold = self.config.get("confidence_threshold", 0.5)
        
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
        import time
        start_time = time.time()
        
        # 统计各模态的置信度
        active_mods = []
        mod_weights = []
        mod_confidences = []
        
        if facial_result and facial_result.confidence > self.confidence_threshold:
            active_mods.append(ModalityType.FACIAL)
            mod_weights.append(self.weights[ModalityType.FACIAL])
            mod_confidences.append(facial_result.confidence)
            
        if vocal_result and vocal_result.confidence > self.confidence_threshold:
            active_mods.append(ModalityType.VOCAL)
            mod_weights.append(self.weights[ModalityType.VOCAL])
            mod_confidences.append(vocal_result.confidence)
            
        if text_result and text_result.confidence > self.confidence_threshold:
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
                    modalities=[],
                    inference_time_ms=(time.time() - start_time) * 1000
                )
            )
        
        # 归一化权重（缺失模态时按有效权重重新归一化）
        total_weight = sum(mod_weights)
        normalized_weights = [w / total_weight for w in mod_weights]
        
        # 加权融合各模态的置信度
        fused_confidence = sum(
            w * c for w, c in zip(normalized_weights, mod_confidences)
        )
        
        # 确定主要情绪（按面部 > 语音 > 文本优先级）
        # 注：实际应进行完整的概率投票，此处为简化处理
        primary_emotion = EmotionType.NEUTRAL
        primary_source = None
        
        if facial_result and facial_result.confidence > self.confidence_threshold:
            primary_emotion = facial_result.emotion
            primary_source = "facial"
        elif vocal_result and vocal_result.confidence > self.confidence_threshold:
            primary_emotion = vocal_result.emotion
            primary_source = "vocal"
        elif text_result and text_result.confidence > self.confidence_threshold:
            primary_emotion = text_result.emotion
            primary_source = "text"
        
        # 构建融合结果
        fused_result = EmotionResult(
            primary_emotion=primary_emotion,
            primary_confidence=fused_confidence,
            fused_confidence=fused_confidence,
            modalities=active_mods,
            inference_time_ms=(time.time() - start_time) * 1000
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
        """估算情绪效价（-1消极 ~ 1积极）"""
        valence_map = {
            EmotionType.SATISFACTION: 0.7,
            EmotionType.HAPPINESS: 0.8,
            EmotionType.SURPRISE: 0.2,
            EmotionType.NEUTRAL: 0.0,
            EmotionType.CONFUSION: -0.3,
            EmotionType.FRUSTRATION: -0.5,
            EmotionType.ANXIETY: -0.5,
            EmotionType.SADNESS: -0.6,
            EmotionType.FEAR: -0.7,
            EmotionType.ANGER: -0.8
        }
        return valence_map.get(emotion, 0.0)
    
    def _estimate_arousal(self, emotion: EmotionType, confidence: float) -> float:
        """估算情绪唤醒度（0 ~ 1）"""
        arousal_map = {
            EmotionType.ANGER: 0.9,
            EmotionType.FEAR: 0.85,
            EmotionType.SURPRISE: 0.8,
            EmotionType.ANXIETY: 0.7,
            EmotionType.FRUSTRATION: 0.65,
            EmotionType.CONFUSION: 0.5,
            EmotionType.HAPPINESS: 0.6,
            EmotionType.SATISFACTION: 0.5,
            EmotionType.NEUTRAL: 0.3,
            EmotionType.SADNESS: 0.3
        }
        base = arousal_map.get(emotion, 0.5)
        return min(1.0, base * confidence)
    
    def check_alert(
        self,
        current_emotion: EmotionType,
        intensity: float,
        emotion_history: List[EmotionResult],
        wait_time_seconds: int = 0
    ) -> EmotionAlert:
        """
        检查是否需要触发告警（基于论文第四章表1规则设计）
        
        Args:
            current_emotion: 当前情绪
            intensity: 情绪强度（置信度作为参考）
            emotion_history: 情绪历史记录
            wait_time_seconds: 等待时间（秒）
            
        Returns:
            EmotionAlert: 告警信息
        """
        rules = EdgeModelConfig.ALERT_RULES
        
        # 检查各情绪类型的告警规则
        emotion_key = current_emotion.value
        
        if emotion_key in rules:
            rule = rules[emotion_key]
            
            # 检查强度阈值
            if intensity >= rule["threshold"]:
                # 检查持续时间
                if wait_time_seconds >= rule["duration_seconds"]:
                    alert_type_map = {
                        "anxiety": EmotionAlertType.LONG_TERM_ANXIETY,
                        "anger": EmotionAlertType.CONFLICT_RISK,
                        "frustration": EmotionAlertType.SERVICE_RECOVERY_NEEDED
                    }
                    
                    return EmotionAlert(
                        triggered=True,
                        alert_type=alert_type_map.get(emotion_key, EmotionAlertType.NEGATIVE_EMOTION_ESCALATION),
                        emotion=current_emotion,
                        intensity=intensity,
                        duration_seconds=wait_time_seconds,
                        recommendation=rule["recommendation"],
                        priority=rule["priority"]
                    )
        
        # 检查持续负面情绪
        if current_emotion in self.NEGATIVE_EMOTIONS and intensity > 0.7:
            if len(emotion_history) >= 3:
                recent_emotions = [r.primary_emotion for r in emotion_history[-3:]]
                if all(e in self.NEGATIVE_EMOTIONS for e in recent_emotions):
                    return EmotionAlert(
                        triggered=True,
                        alert_type=EmotionAlertType.NEGATIVE_EMOTION_ESCALATION,
                        emotion=current_emotion,
                        intensity=intensity,
                        duration_seconds=wait_time_seconds,
                        recommendation="检测到持续负面情绪，建议启动服务修复",
                        priority=2
                    )
        
        # 检查高强度愤怒（冲突风险）
        if current_emotion == EmotionType.ANGER and intensity > 0.85:
            return EmotionAlert(
                triggered=True,
                alert_type=EmotionAlertType.CONFLICT_RISK,
                emotion=current_emotion,
                intensity=intensity,
                duration_seconds=wait_time_seconds,
                recommendation="高风险信号，建议人工立即介入",
                priority=1
            )
        
        return EmotionAlert(triggered=False)


# ============== 情绪识别引擎 ==============

class EmotionRecognitionEngine:
    """
    情绪识别引擎主类
    
    整合面部、语音、文本三个模态的识别能力，
    提供统一的情绪识别接口
    
    支持多种后端：Mock、Transformers、ONNX、TFLite
    """
    
    def __init__(
        self, 
        config: Optional[Dict[str, Any]] = None,
        backend: ModelBackend = ModelBackend.MOCK
    ):
        self.config = config or {}
        self.backend = backend
        self.fusion = CrossModalFusion(self.config)
        
        # 加载模型（根据后端类型）
        self._load_models()
    
    def _load_models(self):
        """加载模型（延迟加载）"""
        if self.backend == ModelBackend.MOCK:
            self.models_loaded = True
            self.model_info = {
                "text": {"backend": "mock", "status": "ready"},
                "facial": {"backend": "mock", "status": "ready"},
                "vocal": {"backend": "mock", "status": "ready"}
            }
        elif self.backend == ModelBackend.TRANSFORMERS:
            # TODO: 加载真实的Transformer模型
            self.models_loaded = False
            self.model_info = {
                "text": {"backend": "transformers", "status": "not_loaded"},
                "facial": {"backend": "transformers", "status": "not_loaded"},
                "vocal": {"backend": "transformers", "status": "not_loaded"}
            }
        elif self.backend == ModelBackend.ONNX:
            # TODO: 加载ONNX模型
            self.models_loaded = False
            self.model_info = {
                "text": {"backend": "onnx", "status": "not_loaded"},
                "facial": {"backend": "onnx", "status": "not_loaded"},
                "vocal": {"backend": "onnx", "status": "not_loaded"}
            }
    
    def recognize_from_multi_modal(
        self,
        session_id: str,
        facial_data: Optional[bytes] = None,
        audio_data: Optional[bytes] = None,
        text: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> MultiModalEmotionResult:
        """
        从多模态数据识别情绪
        
        Args:
            session_id: 会话ID
            facial_data: 面部图像数据（bytes或base64）
            audio_data: 音频数据（bytes）
            text: 文本内容
            context: 上下文信息（等待时间、历史等）
        """
        context = context or {}
        wait_time_seconds = context.get("wait_time_seconds", 0)
        
        # 各模态识别
        facial_result = None
        vocal_result = None
        text_result = None
        
        # 面部识别
        if facial_data:
            facial_result = self._recognize_facial(facial_data)
        
        # 语音识别
        if audio_data:
            vocal_result = self._recognize_vocal(audio_data)
        
        # 文本识别
        if text:
            text_result = self._recognize_text(text)
        
        # 融合结果
        result = self.fusion.fuse(facial_result, vocal_result, text_result)
        result.session_id = session_id
        result.timestamp = datetime.now()
        
        # 检查告警
        if result.fused:
            emotion_history = context.get("emotion_history", [])
            alert = self.fusion.check_alert(
                result.fused.primary_emotion,
                result.fused.primary_confidence,
                emotion_history,
                wait_time_seconds
            )
            result.alert = alert.to_dict()
        
        return result
    
    def _recognize_facial(self, image_data: Union[bytes, str]) -> FacialEmotionResult:
        """面部情绪识别"""
        if self.backend == ModelBackend.MOCK:
            # 模拟返回（原型阶段）
            return FacialEmotionResult(
                emotion=EmotionType.ANXIETY,
                confidence=0.85,
                quality_score=0.9,
                face_detected=True,
                face_count=1,
                emotion_probs={
                    "neutral": 0.05,
                    "anxiety": 0.85,
                    "anger": 0.05,
                    "happiness": 0.03,
                    "sadness": 0.02
                }
            )
        else:
            # TODO: 使用真实模型
            raise NotImplementedError("Real model inference not implemented")
    
    def _recognize_vocal(self, audio_data: bytes) -> VocalEmotionResult:
        """语音情绪识别"""
        if self.backend == ModelBackend.MOCK:
            # 模拟返回（原型阶段）
            return VocalEmotionResult(
                emotion=EmotionType.ANXIETY,
                confidence=0.78,
                duration_seconds=3.0,
                pitch_avg=220.0,
                pitch_std=45.0,
                energy=0.75,
                speech_rate=2.1,
                emotion_probs={
                    "neutral": 0.08,
                    "anxiety": 0.78,
                    "anger": 0.07,
                    "happiness": 0.04,
                    "sadness": 0.03
                }
            )
        else:
            # TODO: 使用真实模型
            raise NotImplementedError("Real model inference not implemented")
    
    def _recognize_text(self, text: str) -> TextEmotionResult:
        """文本情绪识别"""
        if self.backend == ModelBackend.MOCK:
            # 基于关键词的情绪判断（原型阶段）
            # 实际应使用BERT等预训练模型
            
            negative_keywords = {
                "等太久": 0.8, "投诉": 0.9, "生气": 0.85, "着急": 0.7,
                "不满意": 0.8, "慢": 0.6, "差": 0.7, "烂": 0.9, "垃圾": 0.95,
                "烦": 0.6, "急": 0.65, "不安": 0.6, "焦虑": 0.7
            }
            positive_keywords = {
                "好": 0.6, "谢谢": 0.5, "满意": 0.8, "快": 0.6, "方便": 0.6,
                "不错": 0.7, "棒": 0.8, "优秀": 0.85, "赞": 0.7, "nice": 0.6
            }
            
            text_lower = text.lower()
            neg_score = max(
                [v for k, v in negative_keywords.items() if k in text_lower],
                default=0
            )
            pos_score = max(
                [v for k, v in positive_keywords.items() if k in text_lower],
                default=0
            )
            
            # 检测到的关键词
            detected_keywords = [
                k for k in list(negative_keywords.keys()) + list(positive_keywords.keys())
                if k in text_lower
            ]
            
            if neg_score > pos_score and neg_score > 0.5:
                emotion = EmotionType.ANXIETY
                confidence = min(0.95, neg_score + 0.1)
                sentiment = -neg_score
            elif pos_score > neg_score and pos_score > 0.5:
                emotion = EmotionType.SATISFACTION
                confidence = min(0.95, pos_score + 0.1)
                sentiment = pos_score
            else:
                emotion = EmotionType.NEUTRAL
                confidence = 0.6
                sentiment = 0.0
            
            return TextEmotionResult(
                emotion=emotion,
                confidence=confidence,
                keywords=detected_keywords,
                sentiment_score=sentiment,
                token_count=len(text)
            )
        else:
            # TODO: 使用真实模型
            raise NotImplementedError("Real model inference not implemented")
    
    def get_model_info(self) -> Dict[str, Any]:
        """获取模型信息"""
        return {
            "backend": self.backend.value,
            "loaded": self.models_loaded,
            "models": self.model_info,
            "fusion_config": self.fusion.weights
        }


# ============== 便捷函数 ==============

def create_engine(
    backend: str = "mock",
    config: Optional[Dict[str, Any]] = None
) -> EmotionRecognitionEngine:
    """创建情绪识别引擎的便捷函数"""
    backend_map = {
        "mock": ModelBackend.MOCK,
        "transformers": ModelBackend.TRANSFORMERS,
        "onnx": ModelBackend.ONNX,
        "torch": ModelBackend.TORCH,
        "tflite": ModelBackend.TFLITE
    }
    return EmotionRecognitionEngine(
        config=config,
        backend=backend_map.get(backend, ModelBackend.MOCK)
    )


# 示例使用
if __name__ == "__main__":
    # 创建引擎（使用模拟后端）
    engine = create_engine(backend="mock")
    
    print("=== 情绪识别引擎测试 ===")
    print(f"模型信息: {engine.get_model_info()}")
    print()
    
    # 测试文本情绪识别
    print("1. 文本情绪识别测试:")
    result = engine.recognize_from_multi_modal(
        session_id="test_001",
        text="等太久了，我要投诉！"
    )
    print(f"   输入: 等太久了，我要投诉！")
    print(f"   结果: {result.fused.primary_emotion.value if result.fused else 'N/A'}")
    print(f"   置信度: {result.fused.fused_confidence if result.fused else 0:.2f}")
    print(f"   告警: {result.alert}")
    print()
    
    # 测试多模态识别
    print("2. 多模态情绪识别测试:")
    result = engine.recognize_from_multi_modal(
        session_id="test_002",
        facial_data=b"fake_image_data",
        audio_data=b"fake_audio_data",
        text="这个服务太差了！",
        context={"wait_time_seconds": 120}
    )
    print(f"   输入: 面部+语音+文本")
    print(f"   融合情绪: {result.fused.primary_emotion.value if result.fused else 'N/A'}")
    print(f"   置信度: {result.fused.fused_confidence if result.fused else 0:.2f}")
    print(f"   激活模态: {[m.value for m in result.active_modalities]}")
    print(f"   告警: {result.alert}")
