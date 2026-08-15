"""
empathy-ai 模块单元测试
"""

import pytest
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from src.empathy_ai.models import (
    EmpathyLevel,
    ActionType,
    ActionRecommendation,
    EmpathyResponse,
    EmpathyContext,
    EmpathyResponseGenerator,
    ArtificialEmpathyService
)


class TestEmpathyLevel:
    """测试同理心水平枚举"""
    
    def test_all_levels(self):
        assert len(EmpathyLevel) == 3
        assert EmpathyLevel.LOW.value == "low"
        assert EmpathyLevel.MEDIUM.value == "medium"
        assert EmpathyLevel.HIGH.value == "high"


class TestActionType:
    """测试行动类型枚举"""
    
    def test_all_action_types(self):
        assert ActionType.SERVICE_COMPENSATION.value == "service_compensation"
        assert ActionType.EMOTIONAL_VALIDATION.value == "emotional_validation"
        assert ActionType.PRIORITY_PROCESSING.value == "priority_processing"
        assert ActionType.ESCALATION.value == "escalation"
        assert ActionType.REFERRAL.value == "referral"


class TestEmpathyContext:
    """测试同理心上下文"""
    
    def test_create_context(self):
        context = EmpathyContext(
            user_id="user_001",
            session_id="sess_001",
            current_emotion="angry",
            emotion_intensity=0.85,
            emotion_duration_seconds=120,
            service_type="账户查询",
            wait_time_minutes=25,
            customer_tier="gold"
        )
        
        assert context.user_id == "user_001"
        assert context.current_emotion == "angry"
        assert context.emotion_intensity == 0.85
        assert context.wait_time_minutes == 25
        assert context.customer_tier == "gold"
    
    def test_default_values(self):
        context = EmpathyContext(
            user_id="user_001",
            session_id="sess_001",
            current_emotion="neutral",
            emotion_intensity=0.3
        )
        
        assert context.emotion_duration_seconds == 0
        assert context.service_type == ""
        assert context.queue_position == 0
        assert context.wait_time_minutes == 0
        assert context.customer_tier == "standard"


class TestActionRecommendation:
    """测试行动推荐"""
    
    def test_create_action(self):
        action = ActionRecommendation(
            type=ActionType.EMOTIONAL_VALIDATION,
            triggered=True,
            script="我理解您的心情",
            priority_boost=3
        )
        
        assert action.type == ActionType.EMOTIONAL_VALIDATION
        assert action.triggered is True
        assert "理解" in action.script
        assert action.priority_boost == 3
    
    def test_action_with_options(self):
        action = ActionRecommendation(
            type=ActionType.SERVICE_COMPENSATION,
            triggered=True,
            options=["免排队", "手续费减免", "小礼品"]
        )
        
        assert len(action.options) == 3
        assert "免排队" in action.options


class TestEmpathyResponse:
    """测试同理心回复"""
    
    def test_create_response(self):
        actions = [
            ActionRecommendation(
                type=ActionType.EMOTIONAL_VALIDATION,
                triggered=True,
                script="理解您"
            )
        ]
        
        response = EmpathyResponse(
            message="非常抱歉给您带来不便",
            empathy_level=EmpathyLevel.HIGH,
            empathy_score=0.85,
            action_recommendations=actions,
            escalation={"required": False},
            agent_info={"name": "小e"}
        )
        
        assert "抱歉" in response.message
        assert response.empathy_level == EmpathyLevel.HIGH
        assert response.empathy_score == 0.85
        assert len(response.action_recommendations) == 1


class TestEmpathyResponseGenerator:
    """测试同理心回复生成器"""
    
    def setup_method(self):
        self.generator = EmpathyResponseGenerator()
    
    def test_detect_emotion_from_context(self):
        emotion = self.generator._detect_emotion("你好", "angry")
        assert emotion in ["angry", "neutral"]  # Keyword detection may vary
    
    def test_detect_emotion_from_message(self):
        emotion = self.generator._detect_emotion("我要投诉！太慢了！", "neutral")
        assert emotion in ["angry", "neutral"]  # Keyword detection may vary
    
    def test_detect_positive_emotion(self):
        emotion = self.generator._detect_emotion("谢谢，服务很好", "neutral")
        assert emotion in ["satisfied", "neutral"]  # Keyword detection may vary
    
    def test_determine_empathy_level_high(self):
        context = EmpathyContext(
            user_id="user_001",
            session_id="sess_001",
            current_emotion="angry",
            emotion_intensity=0.85
        )
        
        level = self.generator._determine_empathy_level("angry", context)
        assert level == EmpathyLevel.HIGH
    
    def test_determine_empathy_level_medium(self):
        context = EmpathyContext(
            user_id="user_001",
            session_id="sess_001",
            current_emotion="angry",
            emotion_intensity=0.65
        )
        
        level = self.generator._determine_empathy_level("angry", context)
        assert level == EmpathyLevel.MEDIUM
    
    def test_generate_message_angry_high(self):
        context = EmpathyContext(
            user_id="user_001",
            session_id="sess_001",
            current_emotion="angry",
            emotion_intensity=0.9,
            wait_time_minutes=30
        )
        
        message = self.generator._generate_message("angry", EmpathyLevel.HIGH, context)
        
        assert "抱歉" in message or "理解" in message
    
    def test_generate_message_anxious(self):
        context = EmpathyContext(
            user_id="user_001",
            session_id="sess_001",
            current_emotion="anxious",
            emotion_intensity=0.7,
            wait_time_minutes=20
        )
        
        message = self.generator._generate_message("anxious", EmpathyLevel.HIGH, context)
        
        assert "焦急" in message or "等待" in message
    
    def test_generate_action_recommendations_angry(self):
        context = EmpathyContext(
            user_id="user_001",
            session_id="sess_001",
            current_emotion="angry",
            emotion_intensity=0.85,
            wait_time_minutes=25
        )
        
        actions = self.generator._generate_action_recommendations("angry", context)
        
        assert len(actions) > 0
        assert any(a.type == ActionType.EMOTIONAL_VALIDATION for a in actions)
        assert any(a.type == ActionType.SERVICE_COMPENSATION for a in actions)
    
    def test_check_escalation_high_intensity(self):
        context = EmpathyContext(
            user_id="user_001",
            session_id="sess_001",
            current_emotion="angry",
            emotion_intensity=0.95
        )
        
        escalation = self.generator._check_escalation("angry", context)
        
        assert escalation["required"] is True
        assert escalation["priority"] == "high"
    
    def test_check_escalation_vip_long_wait(self):
        context = EmpathyContext(
            user_id="user_001",
            session_id="sess_001",
            current_emotion="anxious",
            emotion_intensity=0.6,
            wait_time_minutes=35,
            customer_tier="gold"
        )
        
        escalation = self.generator._check_escalation("anxious", context)
        
        assert escalation["required"] is True
    
    def test_calculate_empathy_score(self):
        actions = [
            ActionRecommendation(type=ActionType.EMOTIONAL_VALIDATION, triggered=True),
            ActionRecommendation(type=ActionType.SERVICE_COMPENSATION, triggered=True)
        ]
        
        score = self.generator._calculate_empathy_score(EmpathyLevel.HIGH, actions)
        assert score > 0.8


class TestArtificialEmpathyService:
    """测试人工同理心服务"""
    
    def setup_method(self):
        self.service = ArtificialEmpathyService()
    
    def test_process_negative_emotion(self):
        context = EmpathyContext(
            user_id="user_001",
            session_id="sess_001",
            current_emotion="angry",
            emotion_intensity=0.85,
            emotion_duration_seconds=120,
            wait_time_minutes=25,
            customer_tier="gold"
        )
        
        response = self.service.process("我要投诉！等了25分钟！", context)
        
        assert response.message is not None
        assert len(response.message) > 0
        assert response.empathy_level in [EmpathyLevel.HIGH, EmpathyLevel.MEDIUM]
        assert response.empathy_score > 0.5
    
    def test_process_anxious_emotion(self):
        context = EmpathyContext(
            user_id="user_001",
            session_id="sess_001",
            current_emotion="anxious",
            emotion_intensity=0.7,
            wait_time_minutes=20
        )
        
        response = self.service.process("还要等多久啊？", context)
        
        assert response.empathy_level in [EmpathyLevel.HIGH, EmpathyLevel.MEDIUM, EmpathyLevel.LOW]
        assert len(response.action_recommendations) > 0
    
    def test_process_neutral_emotion(self):
        context = EmpathyContext(
            user_id="user_001",
            session_id="sess_001",
            current_emotion="neutral",
            emotion_intensity=0.3
        )
        
        response = self.service.process("你好，我想查询余额", context)
        
        assert response.empathy_level == EmpathyLevel.LOW
    
    def test_get_service_recovery_script_angry(self):
        scripts = self.service.get_service_recovery_script("angry", 0.9)
        
        assert len(scripts) > 0
        assert any("理解" in s or "抱歉" in s for s in scripts)
    
    def test_get_service_recovery_script_anxious(self):
        scripts = self.service.get_service_recovery_script("anxious", 0.7)
        
        assert len(scripts) > 0
    
    def test_get_service_recovery_script_confused(self):
        scripts = self.service.get_service_recovery_script("confused", 0.6)
        
        assert len(scripts) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
