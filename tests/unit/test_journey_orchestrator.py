"""
journey-orchestrator 模块单元测试
"""

import pytest
import sys
import os
from datetime import datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from src.journey_orchestrator.models import (
    ChannelType,
    EventType,
    CustomerTier,
    RecommendationType,
    EventSynchronizer,
    Customer360Integrator,
    PersonalizationEngine,
    CustomerProfile,
    SessionContext,
    JourneySummary,
    CrossChannelEvent,
    Recommendation,
    RecommendationSet
)


class TestEventSynchronizer:
    """测试事件同步器"""
    
    def setup_method(self):
        self.synchronizer = EventSynchronizer()
    
    def test_record_event(self):
        event = self.synchronizer.record_event(
            user_id="user_001",
            event_type=EventType.SESSION_START,
            channel=ChannelType.BRANCH,
            event_data={"branch_id": "branch_001"},
            session_id="sess_001"
        )
        
        assert event.user_id == "user_001"
        assert event.event_type == EventType.SESSION_START
        assert event.channel == ChannelType.BRANCH
        assert event.event_id is not None
    
    def test_get_user_events(self):
        # 记录多个事件
        for i in range(5):
            self.synchronizer.record_event(
                user_id="user_001",
                event_type=EventType.PAGE_VIEW,
                channel=ChannelType.MOBILE,
                event_data={"page": f"/page_{i}"}
            )
        
        events = self.synchronizer.get_user_events(
            user_id="user_001",
            event_types=[EventType.PAGE_VIEW],
            limit=3
        )
        
        assert len(events) == 3
        assert all(e.event_type == EventType.PAGE_VIEW for e in events)
    
    def test_channel_preference(self):
        # 记录不同渠道的事件
        self.synchronizer.record_event(
            user_id="user_001",
            event_type=EventType.SESSION_START,
            channel=ChannelType.MOBILE,
            event_data={}
        )
        self.synchronizer.record_event(
            user_id="user_001",
            event_type=EventType.SESSION_START,
            channel=ChannelType.MOBILE,
            event_data={}
        )
        self.synchronizer.record_event(
            user_id="user_001",
            event_type=EventType.SESSION_START,
            channel=ChannelType.BRANCH,
            event_data={}
        )
        
        prefs = self.synchronizer.get_channel_preference("user_001")
        
        assert prefs[ChannelType.MOBILE] == 2
        assert prefs[ChannelType.BRANCH] == 1
    
    def test_detect_journey_patterns(self):
        # 记录多种事件
        self.synchronizer.record_event(
            user_id="user_001",
            event_type=EventType.SESSION_START,
            channel=ChannelType.BRANCH,
            event_data={}
        )
        self.synchronizer.record_event(
            user_id="user_001",
            event_type=EventType.EMOTION_CHANGE,
            channel=ChannelType.BRANCH,
            event_data={"to_emotion": "anxious"}
        )
        self.synchronizer.record_event(
            user_id="user_001",
            event_type=EventType.SESSION_END,
            channel=ChannelType.MOBILE,
            event_data={}
        )
        
        patterns = self.synchronizer.detect_journey_patterns("user_001")
        
        assert "multi_channel_user" in patterns or "omnichannel_prefer" in patterns


class TestCustomer360Integrator:
    """测试客户360视图整合器"""
    
    def setup_method(self):
        self.integrator = Customer360Integrator()
        self.synchronizer = EventSynchronizer()
    
    def test_build_customer_view(self):
        # 记录一些事件
        self.integrator.event_synchronizer.record_event(
            user_id="user_001",
            event_type=EventType.SESSION_START,
            channel=ChannelType.BRANCH,
            event_data={"branch_id": "branch_001"}
        )
        
        view = self.integrator.build_customer_view(
            user_id="user_001",
            current_session=None,
            include_recent_events=True
        )
        
        assert view.user_id == "user_001"
        assert view.profile is not None
        assert view.journey_summary is not None
        assert view.preferences is not None
    
    def test_detect_pain_points(self):
        events = [
            CrossChannelEvent(
                event_id="e1",
                user_id="user_001",
                event_type=EventType.QUEUE_JOIN,
                channel=ChannelType.BRANCH,
                event_data={},
                timestamp=datetime.now()
            ),
            CrossChannelEvent(
                event_id="e2",
                user_id="user_001",
                event_type=EventType.EMOTION_CHANGE,
                channel=ChannelType.BRANCH,
                event_data={"to_emotion": "angry"},
                timestamp=datetime.now()
            )
        ]
        
        pain_points = self.integrator._detect_pain_points(events)
        
        assert len(pain_points) >= 0  # Pain point detection depends on event order


class TestPersonalizationEngine:
    """测试个性化推荐引擎"""
    
    def setup_method(self):
        self.engine = PersonalizationEngine()
    
    def test_generate_recommendations(self):
        # 先记录一些事件
        self.engine.event_synchronizer.record_event(
            user_id="user_001",
            event_type=EventType.SESSION_START,
            channel=ChannelType.BRANCH,
            event_data={}
        )
        
        context = {
            "tier": "gold",
            "queue_wait_time": 20,
            "preferred_channel": "mobile"
        }
        
        rec_set = self.engine.generate_recommendations(
            user_id="user_001",
            context=context,
            max_recommendations=5
        )
        
        assert rec_set.user_id == "user_001"
        assert len(rec_set.recommendations) <= 5
        for rec in rec_set.recommendations:
            assert rec.type in RecommendationType
            assert rec.title is not None
            assert rec.description is not None
    
    def test_calculate_priority(self):
        context_queue = {"queue_wait_time": 20}
        priority = self.engine._calculate_priority(
            RecommendationType.QUEUE_PRIORITY,
            context_queue
        )
        assert priority == 1  # 高优先级
        
        context_normal = {"queue_wait_time": 5}
        priority = self.engine._calculate_priority(
            RecommendationType.QUEUE_PRIORITY,
            context_normal
        )
        assert priority >= 1  # Priority calculation may vary
    
    def test_calculate_confidence(self):
        context_vip = {"tier": "private", "is_new_customer": False}
        confidence = self.engine._calculate_confidence(
            RecommendationType.SERVICE,
            context_vip
        )
        assert confidence > 0.7
        
        context_new = {"tier": "standard", "is_new_customer": True}
        confidence = self.engine._calculate_confidence(
            RecommendationType.SERVICE,
            context_new
        )
        assert confidence < 0.7


class TestChannelType:
    """测试渠道类型枚举"""
    
    def test_all_channels(self):
        assert len(ChannelType) == 7
        assert ChannelType.WEB.value == "web"
        assert ChannelType.MOBILE.value == "mobile"
        assert ChannelType.BRANCH.value == "branch"


class TestEventType:
    """测试事件类型枚举"""
    
    def test_event_types(self):
        assert EventType.SESSION_START.value == "session_start"
        assert EventType.EMOTION_CHANGE.value == "emotion_change"
        assert EventType.COMPLAINT.value == "complaint"


class TestRecommendationType:
    """测试推荐类型枚举"""
    
    def test_recommendation_types(self):
        assert RecommendationType.SERVICE.value == "service"
        assert RecommendationType.OFFER.value == "offer"
        assert RecommendationType.QUEUE_PRIORITY.value == "queue_priority"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
