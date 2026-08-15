"""
客户旅程编排模块 - 客户360视图、全渠道事件同步、个性化推荐
Journey Orchestrator Module - Customer 360 View, Cross-channel Event Sync, Personalization

基于论文第六章第6.2节：客户旅程编排与服务优化
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Optional, Any, Set
from datetime import datetime, timedelta
from collections import defaultdict
import hashlib
import json


class ChannelType(Enum):
    """渠道类型"""
    WEB = "web"
    MOBILE = "mobile"
    KIOSK = "kiosk"
    BRANCH = "branch"  # 网点
    CALL_CENTER = "call_center"
    WECHAT = "wechat"
    ATM = "atm"


class EventType(Enum):
    """事件类型"""
    SESSION_START = "session_start"
    SESSION_END = "session_end"
    PAGE_VIEW = "page_view"
    CLICK = "click"
    FORM_SUBMIT = "form_submit"
    EMOTION_CHANGE = "emotion_change"
    QUEUE_JOIN = "queue_join"
    QUEUE_LEAVE = "queue_leave"
    SERVICE_START = "service_start"
    SERVICE_END = "service_end"
    PURCHASE = "purchase"
    COMPLAINT = "complaint"
    FEEDBACK = "feedback"


class CustomerTier(Enum):
    """客户等级"""
    STANDARD = "standard"
    SILVER = "silver"
    GOLD = "gold"
    PLATINUM = "platinum"
    PRIVATE = "private"


class RecommendationType(Enum):
    """推荐类型"""
    SERVICE = "service"
    PRODUCT = "product"
    OFFER = "offer"
    CONTENT = "content"
    QUEUE_PRIORITY = "queue_priority"


@dataclass
class CustomerProfile:
    """客户画像"""
    user_id: str
    name: str
    tier: CustomerTier
    segments: List[str]
    risk_level: str
    language: str = "zh-CN"
    accessibility: List[str] = field(default_factory=list)
    contact_method: str = "app_push"
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class SessionContext:
    """会话上下文"""
    session_id: str
    user_id: str
    channel: ChannelType
    location: str
    arrived_at: datetime
    emotion_trend: List[str] = field(default_factory=list)
    current_emotion: Optional[str] = None
    queue_position: Optional[int] = None
    service_type: Optional[str] = None


@dataclass
class JourneySummary:
    """旅程摘要"""
    total_interactions_30d: int
    avg_satisfaction: float
    preferred_channel: ChannelType
    last_contact: datetime
    pain_points: List[str] = field(default_factory=list)
    success_moments: List[str] = field(default_factory=list)


@dataclass
class Customer360View:
    """客户360视图"""
    user_id: str
    profile: CustomerProfile
    current_session: Optional[SessionContext]
    journey_summary: JourneySummary
    preferences: Dict[str, Any]
    recent_events: List[Dict[str, Any]]
    generated_at: datetime = field(default_factory=datetime.now)


@dataclass
class CrossChannelEvent:
    """跨渠道事件"""
    event_id: str
    user_id: str
    event_type: EventType
    channel: ChannelType
    event_data: Dict[str, Any]
    timestamp: datetime
    session_id: Optional[str] = None
    emotion_state: Optional[Dict[str, float]] = None
    location: Optional[str] = None
    
    def __post_init__(self):
        if not self.event_id:
            # 生成唯一事件ID
            content = f"{self.user_id}{self.event_type.value}{self.timestamp.isoformat()}"
            self.event_id = hashlib.md5(content.encode()).hexdigest()[:16]


@dataclass
class Recommendation:
    """推荐结果"""
    type: RecommendationType
    priority: int
    title: str
    description: str
    action_url: str
    confidence: float = 0.5
    reason: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RecommendationSet:
    """推荐集合"""
    user_id: str
    recommendations: List[Recommendation]
    generated_at: datetime = field(default_factory=datetime.now)
    model_version: str = "v1.0"


class EventSynchronizer:
    """
    全渠道事件同步器
    负责收集、标准化和同步各渠道的客户事件
    """
    
    def __init__(self):
        self.event_buffer: List[CrossChannelEvent] = []
        self.user_event_history: Dict[str, List[CrossChannelEvent]] = defaultdict(list)
        self.channel_bindings: Dict[str, Set[str]] = defaultdict(set)  # user_id -> set of channel
    
    def record_event(
        self,
        user_id: str,
        event_type: EventType,
        channel: ChannelType,
        event_data: Dict[str, Any],
        timestamp: Optional[datetime] = None,
        session_id: Optional[str] = None,
        emotion_state: Optional[Dict[str, float]] = None,
        location: Optional[str] = None
    ) -> CrossChannelEvent:
        """
        记录一个跨渠道事件
        
        Args:
            user_id: 用户ID
            event_type: 事件类型
            channel: 渠道类型
            event_data: 事件数据
            timestamp: 时间戳
            session_id: 会话ID
            emotion_state: 情绪状态
            location: 位置
        
        Returns:
            创建的事件对象
        """
        if timestamp is None:
            timestamp = datetime.now()
        
        event = CrossChannelEvent(
            event_id="",  # 会在__post_init__中生成
            user_id=user_id,
            event_type=event_type,
            channel=channel,
            event_data=event_data,
            timestamp=timestamp,
            session_id=session_id,
            emotion_state=emotion_state,
            location=location
        )
        
        # 添加到缓冲区
        self.event_buffer.append(event)
        
        # 更新用户历史
        self.user_event_history[user_id].append(event)
        
        # 更新渠道绑定
        self.channel_bindings[user_id].add(channel.value)
        
        return event
    
    def get_user_events(
        self,
        user_id: str,
        event_types: Optional[List[EventType]] = None,
        channels: Optional[List[ChannelType]] = None,
        since: Optional[datetime] = None,
        limit: int = 100
    ) -> List[CrossChannelEvent]:
        """
        获取用户的事件历史
        
        Args:
            user_id: 用户ID
            event_types: 筛选事件类型
            channels: 筛选渠道
            since: 起始时间
            limit: 返回数量限制
        
        Returns:
            事件列表
        """
        events = self.user_event_history.get(user_id, [])
        
        # 应用筛选
        if event_types:
            events = [e for e in events if e.event_type in event_types]
        
        if channels:
            events = [e for e in events if e.channel in channels]
        
        if since:
            events = [e for e in events if e.timestamp >= since]
        
        # 按时间倒序
        events = sorted(events, key=lambda e: e.timestamp, reverse=True)
        
        return events[:limit]
    
    def get_channel_preference(self, user_id: str) -> Dict[ChannelType, int]:
        """获取用户的渠道偏好"""
        events = self.user_event_history.get(user_id, [])
        channel_counts: Dict[ChannelType, int] = defaultdict(int)
        
        for event in events:
            channel_counts[event.channel] += 1
        
        return dict(channel_counts)
    
    def detect_journey_patterns(self, user_id: str) -> List[str]:
        """检测用户旅程模式"""
        events = self.get_user_events(user_id, limit=50)
        patterns = []
        
        # 检测渠道切换
        channel_sequence = [e.channel for e in events[:10]]
        unique_channels = set(channel_sequence)
        
        if len(unique_channels) >= 3:
            patterns.append("multi_channel_user")
        elif ChannelType.BRANCH in unique_channels and ChannelType.MOBILE in unique_channels:
            patterns.append("omnichannel_prefer")
        
        # 检测情绪波动
        emotion_events = [e for e in events if e.event_type == EventType.EMOTION_CHANGE]
        if len(emotion_events) >= 3:
            patterns.append("emotion_active")
        
        # 检测投诉倾向
        complaint_events = [e for e in events if e.event_type == EventType.COMPLAINT]
        if len(complaint_events) >= 2:
            patterns.append("complaint_prone")
        
        return patterns


class Customer360Integrator:
    """
    客户360视图数据整合器
    整合多源数据构建完整客户视图
    """
    
    def __init__(self):
        self.event_synchronizer = EventSynchronizer()
        self.profile_cache: Dict[str, CustomerProfile] = {}
    
    def build_customer_view(
        self,
        user_id: str,
        current_session: Optional[SessionContext] = None,
        include_recent_events: bool = True
    ) -> Customer360View:
        """
        构建客户360视图
        
        Args:
            user_id: 用户ID
            current_session: 当前会话上下文
            include_recent_events: 是否包含最近事件
        
        Returns:
            客户360视图
        """
        # 获取客户档案
        profile = self._get_or_create_profile(user_id)
        
        # 获取旅程摘要
        journey_summary = self._build_journey_summary(user_id)
        
        # 获取偏好
        preferences = self._extract_preferences(user_id)
        
        # 获取最近事件
        recent_events = []
        if include_recent_events:
            events = self.event_synchronizer.get_user_events(user_id, limit=20)
            recent_events = [
                {
                    "event_type": e.event_type.value,
                    "channel": e.channel.value,
                    "timestamp": e.timestamp.isoformat(),
                    "data": e.event_data
                }
                for e in events
            ]
        
        return Customer360View(
            user_id=user_id,
            profile=profile,
            current_session=current_session,
            journey_summary=journey_summary,
            preferences=preferences,
            recent_events=recent_events
        )
    
    def _get_or_create_profile(self, user_id: str) -> CustomerProfile:
        """获取或创建客户档案"""
        if user_id in self.profile_cache:
            return self.profile_cache[user_id]
        
        # 模拟档案数据
        profile = CustomerProfile(
            user_id=user_id,
            name="客户" + user_id[-4:],
            tier=CustomerTier.GOLD,
            segments=["high_value", "digital_prefer"],
            risk_level="low"
        )
        
        self.profile_cache[user_id] = profile
        return profile
    
    def _build_journey_summary(self, user_id: str) -> JourneySummary:
        """构建旅程摘要"""
        events = self.event_synchronizer.get_user_events(user_id, limit=100)
        
        # 计算30天内的交互次数
        thirty_days_ago = datetime.now() - timedelta(days=30)
        recent_events = [e for e in events if e.timestamp >= thirty_days_ago]
        
        # 获取平均满意度
        feedback_events = [e for e in events if e.event_type == EventType.FEEDBACK]
        avg_satisfaction = 4.0
        if feedback_events:
            scores = [e.event_data.get("score", 4) for e in feedback_events]
            avg_satisfaction = sum(scores) / len(scores)
        
        # 获取首选渠道
        channel_counts = self.event_synchronizer.get_channel_preference(user_id)
        preferred_channel = ChannelType.MOBILE
        if channel_counts:
            preferred_channel = max(channel_counts, key=channel_counts.get)
        
        # 获取最近联系时间
        last_contact = datetime.now() - timedelta(days=1)
        if events:
            last_contact = events[0].timestamp
        
        # 检测痛点和成功时刻
        pain_points = self._detect_pain_points(recent_events)
        success_moments = self._detect_success_moments(recent_events)
        
        return JourneySummary(
            total_interactions_30d=len(recent_events),
            avg_satisfaction=round(avg_satisfaction, 1),
            preferred_channel=preferred_channel,
            last_contact=last_contact,
            pain_points=pain_points,
            success_moments=success_moments
        )
    
    def _detect_pain_points(self, events: List[CrossChannelEvent]) -> List[str]:
        """检测客户痛点"""
        pain_points = []
        
        # 长时间等候
        queue_events = [e for e in events if e.event_type == EventType.QUEUE_JOIN]
        if len(queue_events) >= 3:
            pain_points.append("多次排队等候")
        
        # 投诉
        complaint_events = [e for e in events if e.event_type == EventType.COMPLAINT]
        if complaint_events:
            pain_points.append("曾有投诉记录")
        
        # 情绪负面
        emotion_changes = [e for e in events if e.event_type == EventType.EMOTION_CHANGE]
        negative_changes = [
            e for e in emotion_changes 
            if e.event_data.get("to_emotion") in ["angry", "anxious", "sad"]
        ]
        if len(negative_changes) >= 2:
            pain_points.append("情绪波动较频繁")
        
        return pain_points
    
    def _detect_success_moments(self, events: List[CrossChannelEvent]) -> List[str]:
        """检测成功时刻"""
        success_moments = []
        
        # 高满意度反馈
        feedback_events = [e for e in events if e.event_type == EventType.FEEDBACK]
        high_satisfaction = [e for e in feedback_events if e.event_data.get("score", 0) >= 5]
        if high_satisfaction:
            success_moments.append("多次给出高满意度评价")
        
        # 重复购买/使用
        purchase_events = [e for e in events if e.event_type == EventType.PURCHASE]
        if len(purchase_events) >= 2:
            success_moments.append("持续使用服务")
        
        return success_moments
    
    def _extract_preferences(self, user_id: str) -> Dict[str, Any]:
        """提取客户偏好"""
        events = self.event_synchronizer.get_user_events(user_id, limit=50)
        
        preferences = {
            "language": "zh-CN",
            "accessibility": [],
            "contact_method": "app_push",
            "preferred_times": [],
            "preferred_services": []
        }
        
        # 从事件中学习偏好
        for event in events:
            if event.event_type == EventType.SERVICE_END:
                service_type = event.event_data.get("service_type")
                if service_type and service_type not in preferences["preferred_services"]:
                    preferences["preferred_services"].append(service_type)
        
        return preferences


class PersonalizationEngine:
    """
    个性化推荐引擎
    基于客户旅程和实时上下文生成个性化推荐
    """
    
    def __init__(self):
        self.event_synchronizer = EventSynchronizer()
        self.recommendation_templates = self._load_templates()
    
    def _load_templates(self) -> Dict[str, List[Dict]]:
        """加载推荐模板"""
        return {
            RecommendationType.SERVICE: [
                {
                    "title": "优先办理通道",
                    "description": "已为您开启VIP优先通道，减少等待时间",
                    "action_url": "/redirect/priority-queue",
                    "condition": lambda ctx: ctx.get("tier") in ["gold", "platinum", "private"]
                },
                {
                    "title": "快速业务办理",
                    "description": "推荐使用自助终端，业务办理更快捷",
                    "action_url": "/redirect/self-service",
                    "condition": lambda ctx: ctx.get("preferred_channel") == "mobile"
                }
            ],
            RecommendationType.OFFER: [
                {
                    "title": "专属理财顾问",
                    "description": "您是我们的高净值客户，特提供一对一专属服务",
                    "action_url": "/redirect/advisor-booking",
                    "condition": lambda ctx: ctx.get("tier") == "private"
                },
                {
                    "title": "新客专属优惠",
                    "description": "首次使用AI服务可享手续费减免",
                    "action_url": "/redirect/new-user-offer",
                    "condition": lambda ctx: ctx.get("is_new_customer", False)
                }
            ],
            RecommendationType.QUEUE_PRIORITY: [
                {
                    "title": "智能排队优化",
                    "description": "根据您的情况智能推荐最优排队策略",
                    "action_url": "/redirect/queue-optimization",
                    "condition": lambda ctx: ctx.get("queue_wait_time", 0) > 10
                }
            ]
        }
    
    def generate_recommendations(
        self,
        user_id: str,
        context: Optional[Dict[str, Any]] = None,
        max_recommendations: int = 5
    ) -> RecommendationSet:
        """
        生成个性化推荐
        
        Args:
            user_id: 用户ID
            context: 当前上下文（会话、情绪等）
            max_recommendations: 最大推荐数量
        
        Returns:
            推荐集合
        """
        if context is None:
            context = {}
        
        recommendations = []
        
        # 获取用户档案上下文
        profile_context = self._get_profile_context(user_id)
        context.update(profile_context)
        
        # 获取旅程上下文
        journey_context = self._get_journey_context(user_id)
        context.update(journey_context)
        
        # 生成各类型推荐
        for rec_type, templates in self.recommendation_templates.items():
            for template in templates:
                if template["condition"](context):
                    rec = Recommendation(
                        type=rec_type,
                        priority=self._calculate_priority(rec_type, context),
                        title=template["title"],
                        description=template["description"],
                        action_url=template["action_url"],
                        confidence=self._calculate_confidence(rec_type, context),
                        reason=self._generate_reason(rec_type, context)
                    )
                    recommendations.append(rec)
        
        # 按优先级排序
        recommendations.sort(key=lambda r: (r.priority, r.confidence), reverse=True)
        
        return RecommendationSet(
            user_id=user_id,
            recommendations=recommendations[:max_recommendations]
        )
    
    def _get_profile_context(self, user_id: str) -> Dict[str, Any]:
        """获取档案上下文"""
        events = self.event_synchronizer.get_user_events(user_id, limit=10)
        
        context = {
            "tier": "gold",
            "is_new_customer": len(events) < 3,
            "preferred_channel": "mobile"
        }
        
        # 从事件中推断
        for event in events:
            if event.event_type == EventType.SESSION_START:
                context["preferred_channel"] = event.channel.value
        
        return context
    
    def _get_journey_context(self, user_id: str) -> Dict[str, Any]:
        """获取旅程上下文"""
        events = self.event_synchronizer.get_user_events(user_id, limit=20)
        
        context = {
            "queue_wait_time": 0,
            "current_emotion": "neutral",
            "recent_complaints": 0
        }
        
        # 计算平均等候时间
        queue_join_times = []
        queue_leave_times = []
        
        for event in events:
            if event.event_type == EventType.QUEUE_JOIN:
                queue_join_times.append(event.timestamp)
            elif event.event_type == EventType.QUEUE_LEAVE:
                queue_leave_times.append(event.timestamp)
        
        if queue_join_times and queue_leave_times:
            avg_wait = sum(
                (leave - join).seconds / 60
                for join, leave in zip(queue_join_times[:5], queue_leave_times[:5])
            ) / min(len(queue_join_times), len(queue_leave_times))
            context["queue_wait_time"] = avg_wait
        
        # 检查最近情绪
        emotion_events = [e for e in events if e.event_type == EventType.EMOTION_CHANGE]
        if emotion_events:
            context["current_emotion"] = emotion_events[0].event_data.get("to_emotion", "neutral")
        
        # 统计投诉
        context["recent_complaints"] = len([
            e for e in events 
            if e.event_type == EventType.COMPLAINT
            and e.timestamp >= datetime.now() - timedelta(days=7)
        ])
        
        return context
    
    def _calculate_priority(self, rec_type: RecommendationType, context: Dict) -> int:
        """计算推荐优先级"""
        base_priority = {
            RecommendationType.QUEUE_PRIORITY: 1,
            RecommendationType.SERVICE: 2,
            RecommendationType.OFFER: 3,
            RecommendationType.PRODUCT: 4,
            RecommendationType.CONTENT: 5
        }.get(rec_type, 5)
        
        # 根据上下文调整
        if context.get("queue_wait_time", 0) > 15:
            if rec_type == RecommendationType.QUEUE_PRIORITY:
                return 1
        
        if context.get("recent_complaints", 0) > 0:
            if rec_type == RecommendationType.SERVICE:
                return 1
        
        return base_priority
    
    def _calculate_confidence(self, rec_type: RecommendationType, context: Dict) -> float:
        """计算推荐置信度"""
        base_confidence = 0.7
        
        # 根据用户等级调整
        tier = context.get("tier", "standard")
        if tier in ["platinum", "private"]:
            base_confidence += 0.1
        
        # 根据行为数据充足度调整
        if context.get("is_new_customer", False):
            base_confidence -= 0.2
        
        return min(0.95, max(0.3, base_confidence))
    
    def _generate_reason(self, rec_type: RecommendationType, context: Dict) -> str:
        """生成推荐理由"""
        tier = context.get("tier", "standard")
        
        reasons = {
            RecommendationType.QUEUE_PRIORITY: f"基于您当前排队等待{context.get('queue_wait_time', 0):.0f}分钟的实际情况",
            RecommendationType.SERVICE: f"作为{tier}客户，您享有专属服务通道",
            RecommendationType.OFFER: f"感谢您对我们的信任，为您精选专属优惠",
            RecommendationType.PRODUCT: "根据您的使用习惯推荐",
            RecommendationType.CONTENT: "您可能感兴趣的内容"
        }
        
        return reasons.get(rec_type, "为您个性化推荐")
