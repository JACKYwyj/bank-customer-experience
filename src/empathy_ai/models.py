"""
同理心AI模块 - 人工同理心服务引擎
Empathy AI Module - Artificial Empathy Service Engine

基于论文第四章：共情AI驱动的网点服务流程重构
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Dict, Any
from datetime import datetime


class EmpathyLevel(Enum):
    """同理心水平"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ActionType(Enum):
    """行动推荐类型"""
    SERVICE_COMPENSATION = "service_compensation"
    EMOTIONAL_VALIDATION = "emotional_validation"
    PRIORITY_PROCESSING = "priority_processing"
    ESCALATION = "escalation"
    REFERRAL = "referral"


@dataclass
class ActionRecommendation:
    """行动推荐"""
    type: ActionType
    triggered: bool
    options: Optional[List[str]] = None
    script: Optional[str] = None
    priority_boost: Optional[int] = None


@dataclass
class EmpathyResponse:
    """同理心AI回复"""
    message: str
    empathy_level: EmpathyLevel
    empathy_score: float
    action_recommendations: List[ActionRecommendation]
    escalation: Dict[str, Any]
    agent_info: Dict[str, Any]


@dataclass
class EmpathyContext:
    """同理心上下文"""
    user_id: str
    session_id: str
    current_emotion: str
    emotion_intensity: float
    emotion_duration_seconds: int = 0
    
    # 服务上下文
    service_type: str = ""
    queue_position: int = 0
    wait_time_minutes: float = 0
    business_type: str = ""
    previous_interactions: int = 0
    is_returning_customer: bool = False
    
    # 客户信息
    customer_tier: str = "standard"
    customer_segment: List[str] = field(default_factory=list)


class EmpathyResponseGenerator:
    """
    同理心回复生成器
    
    基于客户情绪状态和服务上下文，
    生成具有同理心的回复和行动推荐
    """
    
    # 情绪关键词映射
    EMOTION_KEYWORDS = {
        "angry": ["投诉", "生气", "不满", "太差", "垃圾", "退款"],
        "anxious": ["等", "慢", "着急", "多久", "快点", "急"],
        "confused": ["怎么", "不懂", "哪里", "什么", "不会", "不清楚"],
        "sad": ["失望", "难过", "伤心", "可惜", "遗憾"],
        "satisfied": ["谢谢", "好", "不错", "满意", "方便"]
    }
    
    # 同理心话术模板
    EMPATHY_TEMPLATES = {
        "angry": {
            "high": [
                "非常抱歉给您带来如此不好的体验，我能完全理解您现在的心情。{specific_issue}确实不应该发生，请您相信我们一定会认真处理您的问题。",
                "您说得对，遇到这样的情况任何人都会有您这样的反应。我们真诚地向您道歉，并会立即采取行动来解决这个问题。"
            ],
            "medium": [
                "抱歉让您感到不满，我们会认真对待您的反馈并尽快改进。",
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
                "抱歉让您久等了，我会尽快为您处理。",
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
                "我来帮您解释一下这个情况。",
            ],
            "low": [
                "好的，我来为您说明。"
            ]
        }
    }
    
    # 服务补偿选项
    COMPENSATION_OPTIONS = {
        "long_wait": ["免排队优先办理", "手续费减免", "小礼品赠送", "优先预约服务"],
        "complaint": ["专人跟进处理", "优先处理", "补偿优惠券", "升级服务"],
        "error": ["立即纠正", "专人解释", "补偿措施", "记录改进"]
    }
    
    def generate_response(
        self,
        user_message: str,
        context: EmpathyContext
    ) -> EmpathyResponse:
        """
        生成同理心回复
        
        Args:
            user_message: 用户消息
            context: 同理心上下文
            
        Returns:
            EmpathyResponse: 同理心回复
        """
        # 检测用户情绪
        detected_emotion = self._detect_emotion(user_message, context.current_emotion)
        
        # 确定同理心水平
        empathy_level = self._determine_empathy_level(detected_emotion, context)
        
        # 生成回复消息
        message = self._generate_message(detected_emotion, empathy_level, context)
        
        # 生成行动推荐
        actions = self._generate_action_recommendations(detected_emotion, context)
        
        # 检查是否需要升级
        escalation = self._check_escalation(detected_emotion, context)
        
        return EmpathyResponse(
            message=message,
            empathy_level=empathy_level,
            empathy_score=self._calculate_empathy_score(empathy_level, actions),
            action_recommendations=actions,
            escalation=escalation,
            agent_info=self._get_agent_info()
        )
    
    def _detect_emotion(self, message: str, context_emotion: str) -> str:
        """检测用户情绪"""
        # 优先使用上下文中的情绪
        if context_emotion:
            return context_emotion
        
        # 基于消息关键词检测
        message_lower = message.lower()
        for emotion, keywords in self.EMOTION_KEYWORDS.items():
            if any(k in message_lower for k in keywords):
                return emotion
        
        return "neutral"
    
    def _determine_empathy_level(
        self,
        emotion: str,
        context: EmpathyContext
    ) -> EmpathyLevel:
        """确定同理心水平"""
        # 高强度负面情绪 + 长时间等待/高价值客户 = 高同理心
        if emotion in ["angry", "anxious"]:
            if context.emotion_intensity > 0.8:
                return EmpathyLevel.HIGH
            elif context.emotion_intensity > 0.6:
                return EmpathyLevel.MEDIUM
        
        if emotion == "confused":
            return EmpathyLevel.HIGH
        
        if emotion in ["sad"]:
            return EmpathyLevel.MEDIUM
        
        return EmpathyLevel.LOW
    
    def _generate_message(
        self,
        emotion: str,
        level: EmpathyLevel,
        context: EmpathyContext
    ) -> str:
        """生成同理心回复消息"""
        level_str = level.value
        
        if emotion in self.EMPATHY_TEMPLATES:
            templates = self.EMPATHY_TEMPLATES[emotion].get(level_str, [])
            if templates:
                template = templates[0]
                # 填充变量
                message = template.format(
                    wait_time=context.wait_time_minutes,
                    specific_issue=self._extract_specific_issue(context)
                )
                return message
        
        # 默认回复
        if emotion == "satisfied":
            return "非常感谢您的好评！您的满意是我们最大的动力。"
        
        return "您好，请问有什么可以帮您？"
    
    def _extract_specific_issue(self, context: EmpathyContext) -> str:
        """提取具体问题"""
        if context.wait_time_minutes > 20:
            return "长时间的等待"
        elif context.service_type:
            return f"在{context.service_type}方面的不便"
        return "给您带来的不便"
    
    def _generate_action_recommendations(
        self,
        emotion: str,
        context: EmpathyContext
    ) -> List[ActionRecommendation]:
        """生成行动推荐"""
        actions = []
        
        # 情绪疏导
        if emotion in ["angry", "anxious"]:
            actions.append(ActionRecommendation(
                type=ActionType.EMOTIONAL_VALIDATION,
                triggered=True,
                script=f"您的感受完全可以理解，{'长时间等待确实会影响心情' if context.wait_time_minutes > 10 else '遇到这样的情况确实会让人不舒服'}。"
            ))
        
        # 服务补偿
        if context.wait_time_minutes > 15 or emotion == "angry":
            actions.append(ActionRecommendation(
                type=ActionType.SERVICE_COMPENSATION,
                triggered=True,
                options=self.COMPENSATION_OPTIONS.get("long_wait", [])
            ))
        
        # 优先处理
        if context.emotion_intensity > 0.7 or context.wait_time_minutes > 20:
            actions.append(ActionRecommendation(
                type=ActionType.PRIORITY_PROCESSING,
                triggered=True,
                priority_boost=5
            ))
        
        return actions
    
    def _check_escalation(
        self,
        emotion: str,
        context: EmpathyContext
    ) -> Dict[str, Any]:
        """检查是否需要升级"""
        # 极端愤怒或高强度负面情绪持续较长时间
        if emotion == "angry" and context.emotion_intensity > 0.9:
            return {
                "required": True,
                "reason": "客户情绪极度激动，需要人工介入",
                "priority": "high"
            }
        
        # 长时间等待的高价值客户
        if context.wait_time_minutes > 30 and context.customer_tier in ["gold", "platinum"]:
            return {
                "required": True,
                "reason": "高价值客户等待时间过长，需要优先处理",
                "priority": "medium"
            }
        
        return {
            "required": False,
            "reason": None,
            "priority": None
        }
    
    def _calculate_empathy_score(
        self,
        level: EmpathyLevel,
        actions: List[ActionRecommendation]
    ) -> float:
        """计算同理心得分"""
        base_scores = {
            EmpathyLevel.HIGH: 0.85,
            EmpathyLevel.MEDIUM: 0.70,
            EmpathyLevel.LOW: 0.50
        }
        
        base = base_scores[level]
        
        # 行动推荐加分
        action_bonus = len([a for a in actions if a.triggered]) * 0.03
        
        return min(1.0, base + action_bonus)
    
    def _get_agent_info(self) -> Dict[str, Any]:
        """获取虚拟代理信息"""
        return {
            "id": "agent_001",
            "name": "小e",
            "avatar_url": "https://xxx/avatar.png",
            "personality": "warm_professional",
            "voice_url": "https://xxx/voice.wav"
        }


class ArtificialEmpathyService:
    """
    人工同理心服务主类
    
    提供人机协同的同理心服务，
    实现"增强而非替代"的服务模式
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.response_generator = EmpathyResponseGenerator()
    
    def process(
        self,
        user_message: str,
        context: EmpathyContext
    ) -> EmpathyResponse:
        """
        处理用户消息，生成同理心回复
        
        Args:
            user_message: 用户消息
            context: 同理心上下文
            
        Returns:
            EmpathyResponse: 同理心回复
        """
        return self.response_generator.generate_response(user_message, context)
    
    def get_service_recovery_script(
        self,
        emotion: str,
        intensity: float
    ) -> List[str]:
        """
        获取服务修复话术
        
        用于情绪驱动的服务修复机制
        """
        scripts = {
            "angry": [
                "我非常理解您现在的心情，请先让我真诚地向您道歉。",
                "您反映的问题非常重要，我们会立即处理。",
                "为了弥补您的不愉快体验，我们可以为您提供..."
            ],
            "anxious": [
                "我能感受到您很着急，请您放心，我现在就帮您处理。",
                "让您久等了，您的问题我会最优先处理。",
                "请告诉我您最关心的问题是什么，我会全力帮助您。"
            ],
            "confused": [
                "完全理解您的困惑，让我来帮您梳理一下。",
                "这个问题确实有点复杂，请您不要着急，我会详细为您解释。",
                "让我们一步一步来，我会确保您完全理解。"
            ]
        }
        
        base_scripts = scripts.get(emotion, ["您好，请问有什么可以帮助您的？"])
        
        # 根据强度调整话术长度
        if intensity > 0.8:
            return base_scripts
        elif intensity > 0.6:
            return base_scripts[:2]
        else:
            return base_scripts[:1]


# 示例使用
if __name__ == "__main__":
    service = ArtificialEmpathyService()
    
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
    
    response = service.process("我要投诉！等了25分钟还没轮到！", context)
    
    print(f"Empathy Level: {response.empathy_level.value}")
    print(f"Empathy Score: {response.empathy_score:.2f}")
    print(f"Message: {response.message}")
    print(f"Actions: {[a.type.value for a in response.action_recommendations]}")
    print(f"Escalation: {response.escalation}")
