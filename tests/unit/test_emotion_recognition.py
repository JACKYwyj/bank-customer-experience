"""
emotion-recognition 模块单元测试
"""

import pytest
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from src.emotion_recognition.models import (
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


class TestEmotionType:
    """测试情绪类型枚举"""
    
    def test_all_emotions(self):
        assert len(EmotionType) == 10
        assert EmotionType.NEUTRAL.value == "neutral"
        assert EmotionType.HAPPINESS.value == "happiness"
        assert EmotionType.ANXIETY.value == "anxiety"
        assert EmotionType.ANGER.value == "anger"
    
    def test_emotion_values(self):
        for emotion in EmotionType:
            assert isinstance(emotion.value, str)
            assert len(emotion.value) > 0


class TestModalityType:
    """测试模态类型枚举"""
    
    def test_all_modalities(self):
        assert len(ModalityType) == 3
        assert ModalityType.FACIAL.value == "facial"
        assert ModalityType.VOCAL.value == "vocal"
        assert ModalityType.TEXT.value == "text"


class TestEmotionResult:
    """测试情绪识别结果"""
    
    def test_create_emotion_result(self):
        result = EmotionResult(
            primary_emotion=EmotionType.ANXIETY,
            primary_confidence=0.85,
            valence=-0.5,
            arousal=0.7,
            fused_confidence=0.82
        )
        
        assert result.primary_emotion == EmotionType.ANXIETY
        assert result.primary_confidence == 0.85
        assert result.valence == -0.5
        assert result.arousal == 0.7
        assert result.fused_confidence == 0.82
    
    def test_default_modalities(self):
        result = EmotionResult(
            primary_emotion=EmotionType.NEUTRAL,
            primary_confidence=0.6
        )
        assert result.modalities == []


class TestFacialEmotionResult:
    """测试面部情绪识别结果"""
    
    def test_create_facial_result(self):
        result = FacialEmotionResult(
            emotion=EmotionType.HAPPINESS,
            confidence=0.92,
            quality_score=0.88
        )
        
        assert result.emotion == EmotionType.HAPPINESS
        assert result.confidence == 0.92
        assert result.quality_score == 0.88


class TestVocalEmotionResult:
    """测试语音情绪识别结果"""
    
    def test_create_vocal_result(self):
        result = VocalEmotionResult(
            emotion=EmotionType.ANXIETY,
            confidence=0.78,
            pitch_avg=220.0,
            speech_rate=2.1,
            energy=0.65
        )
        
        assert result.emotion == EmotionType.ANXIETY
        assert result.confidence == 0.78
        assert result.pitch_avg == 220.0
        assert result.speech_rate == 2.1


class TestTextEmotionResult:
    """测试文本情绪识别结果"""
    
    def test_create_text_result(self):
        result = TextEmotionResult(
            emotion=EmotionType.SATISFACTION,
            confidence=0.75,
            keywords=["满意", "好"],
            sentiment_score=0.6
        )
        
        assert result.emotion == EmotionType.SATISFACTION
        assert result.confidence == 0.75
        assert "满意" in result.keywords
        assert result.sentiment_score == 0.6


class TestMultiModalEmotionResult:
    """测试多模态融合结果"""
    
    def test_has_modalities(self):
        facial = FacialEmotionResult(emotion=EmotionType.NEUTRAL, confidence=0.6)
        result = MultiModalEmotionResult(
            session_id="test_session",
            timestamp=datetime.now(),
            facial=facial
        )
        
        assert result.has_face is True
        assert result.has_vocal is False
        assert result.has_text is False
    
    def test_active_modalities(self):
        facial = FacialEmotionResult(emotion=EmotionType.NEUTRAL, confidence=0.6)
        vocal = VocalEmotionResult(emotion=EmotionType.NEUTRAL, confidence=0.55)
        
        result = MultiModalEmotionResult(
            session_id="test_session",
            timestamp=datetime.now(),
            facial=facial,
            vocal=vocal
        )
        
        assert ModalityType.FACIAL in result.active_modalities
        assert ModalityType.VOCAL in result.active_modalities
        assert ModalityType.TEXT not in result.active_modalities


class TestCrossModalFusion:
    """测试跨模态融合"""
    
    def setup_method(self):
        self.fusion = CrossModalFusion()
    
    def test_fuse_single_modality(self):
        facial = FacialEmotionResult(
            emotion=EmotionType.ANXIETY,
            confidence=0.85
        )
        
        result = self.fusion.fuse(facial, None, None)
        
        assert result.fused is not None
        assert result.fused.primary_emotion == EmotionType.ANXIETY
        assert result.has_face is True
        assert len(result.active_modalities) == 1
    
    def test_fuse_multiple_modalities(self):
        facial = FacialEmotionResult(emotion=EmotionType.ANXIETY, confidence=0.85)
        vocal = VocalEmotionResult(emotion=EmotionType.ANXIETY, confidence=0.78)
        text = TextEmotionResult(emotion=EmotionType.ANXIETY, confidence=0.75)
        
        result = self.fusion.fuse(facial, vocal, text)
        
        assert result.fused is not None
        assert len(result.active_modalities) == 3
        assert result.fused.fused_confidence > 0.7
    
    def test_fuse_no_valid_modality(self):
        result = self.fusion.fuse(None, None, None)
        
        assert result.fused is not None
        assert result.fused.primary_emotion == EmotionType.NEUTRAL
        assert result.fused.fused_confidence == 0.5
    
    def test_estimate_valence(self):
        valence_happiness = self.fusion._estimate_valence(EmotionType.HAPPINESS)
        valence_anger = self.fusion._estimate_valence(EmotionType.ANGER)
        
        assert valence_happiness > 0
        assert valence_anger < 0
    
    def test_estimate_arousal(self):
        arousal_anger = self.fusion._estimate_arousal(EmotionType.ANGER, 0.9)
        arousal_neutral = self.fusion._estimate_arousal(EmotionType.NEUTRAL, 0.5)
        
        assert arousal_anger > arousal_neutral
    
    def test_check_alert_negative_escalation(self):
        alert = self.fusion.check_alert(
            current_emotion=EmotionType.ANGER,
            intensity=0.9,
            emotion_history=[
                EmotionResult(EmotionType.ANGER, 0.8),
                EmotionResult(EmotionType.ANGER, 0.85),
                EmotionResult(EmotionType.ANGER, 0.88)
            ],
            wait_time_minutes=0
        )
        
        assert alert.triggered is True
        assert alert.alert_type == EmotionAlertType.NEGATIVE_EMOTION_ESCALATION
    
    def test_check_alert_long_term_anxiety(self):
        alert = self.fusion.check_alert(
            current_emotion=EmotionType.ANXIETY,
            intensity=0.6,
            emotion_history=[],
            wait_time_minutes=20
        )
        
        assert alert.triggered is True
        assert alert.alert_type == EmotionAlertType.LONG_TERM_ANXIETY
    
    def test_check_alert_no_alert(self):
        alert = self.fusion.check_alert(
            current_emotion=EmotionType.NEUTRAL,
            intensity=0.3,
            emotion_history=[],
            wait_time_minutes=0
        )
        
        assert alert.triggered is False


class TestEmotionRecognitionEngine:
    """测试情绪识别引擎"""
    
    def setup_method(self):
        self.engine = EmotionRecognitionEngine()
    
    def test_recognize_from_text_only(self):
        result = self.engine.recognize_from_multi_modal(
            session_id="test_session_001",
            text="等太久了，我要投诉！"
        )
        
        assert result.session_id == "test_session_001"
        assert result.has_text is True
        assert result.fused is not None
    
    def test_recognize_from_facial_only(self):
        result = self.engine.recognize_from_multi_modal(
            session_id="test_session_002",
            facial_data=b"fake_image_data"
        )
        
        assert result.has_face is True
        assert result.fused is not None
    
    def test_recognize_from_vocal_only(self):
        result = self.engine.recognize_from_multi_modal(
            session_id="test_session_003",
            audio_data=b"fake_audio_data"
        )
        
        assert result.has_vocal is True
        assert result.fused is not None
    
    def test_recognize_from_all_modalities(self):
        result = self.engine.recognize_from_multi_modal(
            session_id="test_session_004",
            facial_data=b"fake_image",
            audio_data=b"fake_audio",
            text="我很满意你们的服务"
        )
        
        assert result.has_face is True
        assert result.has_vocal is True
        assert result.has_text is True
        assert len(result.active_modalities) == 3
    
    def test_text_positive_detection(self):
        result = self.engine.recognize_from_multi_modal(
            session_id="test_session_005",
            text="服务很好，谢谢！"
        )
        
        assert result.has_text is True
        assert result.text.emotion == EmotionType.SATISFACTION
    
    def test_text_negative_detection(self):
        result = self.engine.recognize_from_multi_modal(
            session_id="test_session_006",
            text="太慢了，等了30分钟！"
        )
        
        assert result.has_text is True
        assert result.text.emotion == EmotionType.ANXIETY


class TestEmotionAlert:
    """测试情绪告警"""
    
    def test_alert_to_dict(self):
        alert = EmotionAlert(
            triggered=True,
            alert_type=EmotionAlertType.CONFLICT_RISK,
            emotion=EmotionType.ANGER,
            intensity=0.9,
            recommendation="建议人工立即介入"
        )
        
        alert_dict = alert.to_dict()
        
        assert alert_dict["triggered"] is True
        assert alert_dict["type"] == "conflict_risk"
        assert alert_dict["emotion"] == "anger"
        assert alert_dict["intensity"] == 0.9


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
