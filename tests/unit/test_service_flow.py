"""
service-flow 模块单元测试
"""

import pytest
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../src"))

from src.service-flow.models import (
    ProcessStatus,
    StageStatus,
    ProcessCategory,
    TriggerType,
    EmotionState,
    ServiceRepairStrategy,
    ProcessStage,
    ProcessDefinition,
    StageInstance,
    ProcessInstance,
    EmotionDrivenOrchestrator,
    HumanMachineCollaborator,
    ServiceFlowStateMachine
)


class TestProcessDefinition:
    """测试流程定义"""
    
    def test_create_process_definition(self):
        stages = [
            ProcessStage(
                name="接待",
                description="接待客户",
                actions=["greet", "identify"],
                emotion_adaptive=True
            ),
            ProcessStage(
                name="处理",
                description="处理业务",
                actions=["process", "verify"],
                emotion_adaptive=True,
                human_handoff_allowed=True
            )
        ]
        
        process = ProcessDefinition(
            id="test_proc_001",
            name="测试流程",
            category=ProcessCategory.COMPLAINT,
            version="1.0",
            status=ProcessStatus.ACTIVE,
            description="测试流程定义",
            stages=stages
        )
        
        assert process.id == "test_proc_001"
        assert process.category == ProcessCategory.COMPLAINT
        assert len(process.stages) == 2
    
    def test_default_processes(self):
        sm = ServiceFlowStateMachine()
        
        processes = sm.get_processes()
        
        assert len(processes) >= 2
        process_ids = [p.id for p in processes]
        assert "proc_001" in process_ids  # 投诉处理流程
        assert "proc_002" in process_ids  # 业务咨询流程


class TestServiceFlowStateMachine:
    """测试服务流程状态机"""
    
    def setup_method(self):
        self.sm = ServiceFlowStateMachine()
    
    def test_create_instance(self):
        instance = self.sm.create_instance(
            process_id="proc_001",
            user_id="user_001",
            trigger_type=TriggerType.MANUAL,
            context={"reason": "test"},
            session_id="sess_001"
        )
        
        assert instance is not None
        assert instance.process_id == "proc_001"
        assert instance.user_id == "user_001"
        assert instance.status == "pending"
        assert instance.instance_id is not None
    
    def test_transition_pending_to_in_progress(self):
        instance = self.sm.create_instance(
            process_id="proc_001",
            user_id="user_001",
            trigger_type=TriggerType.MANUAL
        )
        
        updated = self.sm.transition(
            instance_id=instance.instance_id,
            new_status="in_progress"
        )
        
        assert updated.status == "in_progress"
        assert updated.stages[0].status == StageStatus.IN_PROGRESS
    
    def test_invalid_transition(self):
        instance = self.sm.create_instance(
            process_id="proc_001",
            user_id="user_001",
            trigger_type=TriggerType.MANUAL
        )
        
        # pending -> completed 是无效的
        with pytest.raises(ValueError):
            self.sm.transition(
                instance_id=instance.instance_id,
                new_status="completed"
            )
    
    def test_advance_stage(self):
        instance = self.sm.create_instance(
            process_id="proc_002",
            user_id="user_001",
            trigger_type=TriggerType.MANUAL
        )
        
        # 先启动
        self.sm.transition(instance.instance_id, "in_progress")
        
        # 推进阶段
        updated = self.sm.advance_stage(
            instance_id=instance.instance_id,
            emotion_state={"emotion": "neutral", "intensity": 0.3}
        )
        
        assert updated.stages[0].status == StageStatus.COMPLETED
        assert updated.current_stage == "查询"
    
    def test_get_instance(self):
        instance = self.sm.create_instance(
            process_id="proc_001",
            user_id="user_001",
            trigger_type=TriggerType.MANUAL
        )
        
        retrieved = self.sm.get_instance(instance.instance_id)
        
        assert retrieved is not None
        assert retrieved.instance_id == instance.instance_id
    
    def test_get_processes_filter(self):
        processes = self.sm.get_processes(
            category=ProcessCategory.COMPLAINT
        )
        
        assert all(p.category == ProcessCategory.COMPLAINT for p in processes)


class TestEmotionDrivenOrchestrator:
    """测试情绪驱动编排器"""
    
    def setup_method(self):
        self.orchestrator = EmotionDrivenOrchestrator()
    
    def test_determine_flow_adjustment_neutral(self):
        result = self.orchestrator.determine_flow_adjustment(
            current_emotion="neutral",
            intensity=0.2,
            duration_seconds=30
        )
        
        assert result["action"] == "continue"
        assert result.get("triggered") is None or result.get("triggered") is False
    
    def test_determine_flow_adjustment_anxiety(self):
        result = self.orchestrator.determine_flow_adjustment(
            current_emotion="anxiety",
            intensity=0.6,
            duration_seconds=90
        )
        
        assert result.get("triggered") is True
        assert result["action"] == "intervene"
        assert "recovery_strategy" in result
    
    def test_determine_flow_adjustment_anger(self):
        result = self.orchestrator.determine_flow_adjustment(
            current_emotion="anger",
            intensity=0.9,
            duration_seconds=30
        )
        
        assert result.get("triggered") is True
        assert result.get("escalation_required") is True
        assert result.get("priority_boost") == 5
    
    def test_generate_empathy_script(self):
        script = self.orchestrator.generate_empathy_script(
            emotion="anxiety",
            intensity=0.7,
            context={"wait_time": 20}
        )
        
        assert "焦急" in script or "20" in script
        assert len(script) > 0


class TestHumanMachineCollaborator:
    """测试人机协同"""
    
    def setup_method(self):
        self.collaborator = HumanMachineCollaborator()
    
    def test_should_escalate_intensity(self):
        assert self.collaborator.should_escalate(
            emotion="anger",
            intensity=0.95,
            repair_attempts=0,
            context={}
        ) is True
    
    def test_should_escalate_repair_attempts(self):
        assert self.collaborator.should_escalate(
            emotion="frustration",
            intensity=0.6,
            repair_attempts=4,
            context={}
        ) is True
    
    def test_should_escalate_customer_request(self):
        assert self.collaborator.should_escalate(
            emotion="neutral",
            intensity=0.3,
            repair_attempts=0,
            context={"customer_requested_human": True}
        ) is True
    
    def test_should_not_escalate(self):
        assert self.collaborator.should_escalate(
            emotion="neutral",
            intensity=0.3,
            repair_attempts=0,
            context={}
        ) is False
    
    def test_create_collaboration_session(self):
        session = self.collaborator.create_collaboration_session(
            instance_id="inst_001",
            customer_info={"name": "张三", "tier": "gold"},
            ai_context={"current_stage": "处理", "emotion": "anxious"}
        )
        
        assert session["instance_id"] == "inst_001"
        assert session["status"] == "ai_in_progress"
        assert session["human_ready"] is False
    
    def test_request_human_intervention(self):
        request = self.collaborator.request_human_intervention(
            instance_id="inst_001",
            reason="客户情绪激动",
            priority=2
        )
        
        assert request["instance_id"] == "inst_001"
        assert request["priority"] == 2
        assert request["status"] == "pending"
    
    def test_get_resolution_action_empathy(self):
        action = self.collaborator.get_resolution_action(
            strategy=ServiceRepairStrategy.EMPATHY_RESPONSE,
            context={}
        )
        
        assert action["type"] == "message"
        assert "template" in action
    
    def test_get_resolution_action_priority(self):
        action = self.collaborator.get_resolution_action(
            strategy=ServiceRepairStrategy.PRIORITY_SERVICE,
            context={"available_window": 3}
        )
        
        assert action["type"] == "action"
        assert action["action"] == "priority_queue"
    
    def test_complete_collaboration(self):
        # 先创建协作会话
        self.collaborator.create_collaboration_session(
            instance_id="inst_001",
            customer_info={},
            ai_context={}
        )
        
        result = self.collaborator.complete_collaboration(
            instance_id="inst_001",
            resolution="问题已解决",
            customer_satisfied=True
        )
        
        assert result["resolved"] is True
        assert result["satisfaction"] is True


class TestEnums:
    """测试枚举类型"""
    
    def test_process_status(self):
        assert ProcessStatus.ACTIVE.value == "active"
        assert ProcessStatus.DEPRECATED.value == "deprecated"
    
    def test_stage_status(self):
        assert StageStatus.PENDING.value == "pending"
        assert StageStatus.COMPLETED.value == "completed"
    
    def test_trigger_type(self):
        assert TriggerType.EMOTION_ALERT.value == "emotion_alert"
        assert TriggerType.MANUAL.value == "manual"
    
    def test_service_repair_strategy(self):
        assert ServiceRepairStrategy.EMPATHY_RESPONSE.value == "empathy_response"
        assert ServiceRepairStrategy.ESCALATION.value == "escalation"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
