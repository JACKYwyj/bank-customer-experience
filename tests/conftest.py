"""
pytest配置文件
"""

import pytest
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


@pytest.fixture
def sample_branch_data():
    """样本网点数据"""
    return {
        "branch_id": "branch_001",
        "branch_name": "北京朝阳支行",
        "indicator_data": {
            "service_efficiency": {
                "avg_wait_time": 10,
                "avg_service_time": 8,
                "success_rate": 0.95
            },
            "customer_experience": {
                "satisfaction_score": 4.2,
                "emotion_positive_rate": 0.8,
                "complaint_rate": 0.02
            },
            "space_utilization": {
                "area_efficiency": 0.75,
                "functional_layout_score": 0.8,
                "flow_line_score": 0.7
            }
        }
    }


@pytest.fixture
def sample_user_data():
    """样例用户数据"""
    return {
        "user_id": "user_001",
        "name": "张三",
        "tier": "gold",
        "segments": ["high_value", "digital_prefer"],
        "risk_level": "low"
    }


@pytest.fixture
def sample_event_data():
    """样例事件数据"""
    return {
        "user_id": "user_001",
        "event_type": "session_start",
        "channel": "branch",
        "event_data": {
            "branch_id": "branch_001",
            "window_id": "window_01"
        }
    }


@pytest.fixture
def sample_emotion_data():
    """样例情绪数据"""
    return {
        "emotion": "anxious",
        "intensity": 0.7,
        "duration_seconds": 60
    }
