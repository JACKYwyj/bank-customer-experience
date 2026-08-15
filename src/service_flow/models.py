"""
服务流程引擎模块 - 情绪驱动流程编排、人机协同服务修复、流程状态机
Service Flow Engine Module - Emotion-driven Orchestration, Human-Machine Collaboration, Process State Machine

基于论文第四章：情绪感知驱动的服务流程与人机协同机制
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Optional, Any, Callable, Set
from datetime import datetime, timedelta
from collections import defaultdict, deque
import uuid
import json


class ProcessStatus(Enum):
    """流程状态"""
    DRAFT = "draft"
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    ARCHIVED = "archived"


class StageStatus(Enum):
    """阶段状态"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    SKIPPED = "skipped"
    FAILED = "failed"


class ProcessCategory(Enum):
    """流程类别"""
    COMPLAINT = "complaint"       # 投诉处理
    INQUIRY = "inquiry"           # 业务咨询
    TRANSACTION = "transaction"   # 业务办理
    RECOVERY = "recovery"         # 服务修复
    VIP_SERVICE = "vip_service"   # VIP服务


class TriggerType(Enum):
    """触发类型"""
    EMOTION_ALERT = "emotion_alert"       # 情绪告警触发
    MANUAL = "manual"                     # 手动触发
    AUTOMATIC = "automatic"               # 自动触发
    SCHEDULED = "scheduled"               # 定时触发
    EVENT_BASED = "event_based"           # 事件触发


class EmotionState(Enum):
    """情绪状态"""
    NEUTRAL = "neutral"
    SLIGHTLY_NEGATIVE = "slightly_negative"
    NEGATIVE = "negative"
    HIGHLY_NEGATIVE = "highly_negative"
    POSITIVE = "positive"


class ServiceRepairStrategy(Enum):
    """服务修复策略"""
    EMPATHY_RESPONSE = "empathy_response"         # 同理心回应
    PRIORITY_SERVICE = "priority_service"         # 优先服务
    COMPENSATION = "compensation"                 # 补偿方案
    ESCALATION = "escalation"                     # 升级人工
    SUPERVISOR_INTERVENTION = "supervisor"        # 主管介入


@dataclass
class ProcessStage:
    """流程阶段"""
    name: str
    description: str
    actions: List[str]
    emotion_adaptive: bool = True
    human_handoff_allowed: bool = True
    min_duration_seconds: int = 30
    max_duration_seconds: int = 300


@dataclass
class ProcessDefinition:
    """流程定义"""
    id: str
    name: str
    category: ProcessCategory
    version: str
    status: ProcessStatus
    description: str
    stages: List[ProcessStage]
    emotion_triggers: Dict[str, List[str]] = field(default_factory=dict)
    recovery_strategies: Dict[str, str] = field(default_factory=dict)
    avg_duration_minutes: int = 30
    satisfaction_rate: float = 0.85


@dataclass
class StageInstance:
    """阶段实例"""
    name: str
    status: StageStatus
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    emotion_at_entry: Optional[str] = None
    emotion_at_exit: Optional[str] = None
    actions_taken: List[str] = field(default_factory=list)
    notes: str = ""


@dataclass
class ProcessInstance:
    """流程实例"""
    instance_id: str
    process_id: str
    process_name: str
    user_id: str
    session_id: Optional[str]
    status: str  # pending, in_progress, completed, cancelled, failed
    current_stage: str
    stages: List[StageInstance]
    context: Dict[str, Any]
    started_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    triggered_by: TriggerType = TriggerType.MANUAL
    emotion_trend: List[Dict[str, Any]] = field(default_factory=list)
    repair_attempts: int = 0
    
    def __post_init__(self):
        if not self.instance_id:
            self.instance_id = f"inst_{uuid.uuid4().hex[:12]}"


@dataclass
class EmotionTrigger:
    """情绪触发器"""
    emotion: EmotionState
    intensity_threshold: float
    duration_threshold_seconds: int
    escalation_required: bool
    recovery_strategy: Optional[ServiceRepairStrategy] = None


class EmotionDrivenOrchestrator:
    """
    情绪驱动流程编排器
    根据客户情绪状态动态调整服务流程
    """
    
    # 情绪阈值配置
    EMOTION_THRESHOLDS = {
        EmotionState.NEUTRAL: {"intensity": 0.3, "action": "continue"},
        EmotionState.SLIGHTLY_NEGATIVE: {"intensity": 0.5, "action": "monitor"},
        EmotionState.NEGATIVE: {"intensity": 0.7, "action": "intervene"},
        EmotionState.HIGHLY_NEGATIVE: {"intensity": 0.85, "action": "escalate"},
        EmotionState.POSITIVE: {"intensity": 0.6, "action": "enhance"}
    }
    
    def __init__(self):
        self.emotion_triggers: Dict[str, EmotionTrigger] = {}
        self._setup_default_triggers()
    
    def _setup_default_triggers(self):
        """设置默认情绪触发器"""
        self.emotion_triggers["anxiety"] = EmotionTrigger(
            emotion=EmotionState.SLIGHTLY_NEGATIVE,
            intensity_threshold=0.5,
            duration_threshold_seconds=60,
            escalation_required=False,
            recovery_strategy=ServiceRepairStrategy.EMPATHY_RESPONSE
        )
        
        self.emotion_triggers["anger"] = EmotionTrigger(
            emotion=EmotionState.HIGHLY_NEGATIVE,
            intensity_threshold=0.8,
            duration_threshold_seconds=30,
            escalation_required=True,
            recovery_strategy=ServiceRepairStrategy.ESCALATION
        )
        
        self.emotion_triggers["frustration"] = EmotionTrigger(
            emotion=EmotionState.NEGATIVE,
            intensity_threshold=0.6,
            duration_threshold_seconds=90,
            escalation_required=False,
            recovery_strategy=ServiceRepairStrategy.PRIORITY_SERVICE
        )
    
    def determine_flow_adjustment(
        self,
        current_emotion: str,
        intensity: float,
        duration_seconds: int
    ) -> Dict[str, Any]:
        """
        确定流程调整策略
        
        Args:
            current_emotion: 当前情绪
            intensity: 情绪强度 0-1
            duration_seconds: 持续时间（秒）
        
        Returns:
            调整策略
        """
        trigger = self.emotion_triggers.get(
            current_emotion,
            EmotionTrigger(
                emotion=EmotionState.NEUTRAL,
                intensity_threshold=0.5,
                duration_threshold_seconds=120,
                escalation_required=False
            )
        )
        
        # 检查是否触发
        triggered = (
            intensity >= trigger.intensity_threshold and
            duration_seconds >= trigger.duration_threshold_seconds
        )
        
        if not triggered:
            return {
                "action": "continue",
                "message": "情绪状态正常，继续当前流程"
            }
        
        # 根据策略确定调整
        adjustment = {
            "action": "intervene",
            "triggered": True,
            "emotion": current_emotion,
            "intensity": intensity,
            "duration": duration_seconds,
            "escalation_required": trigger.escalation_required
        }
        
        if trigger.recovery_strategy:
            adjustment["recovery_strategy"] = trigger.recovery_strategy.value
        
        if trigger.escalation_required:
            adjustment["message"] = f"检测到高度负面情绪({current_emotion})，建议升级人工处理"
            adjustment["priority_boost"] = 5
        else:
            adjustment["message"] = f"检测到负面情绪({current_emotion})，启动服务修复"
            adjustment["priority_boost"] = 2
        
        return adjustment
    
    def generate_empathy_script(
        self,
        emotion: str,
        intensity: float,
        context: Dict[str, Any]
    ) -> str:
        """生成同理心话术"""
        scripts = {
            "anxiety": "我能理解您等待了{wait_time}分钟确实让人焦急。请您放心，我会尽快为您处理。",
            "anger": "非常抱歉给您带来不好的体验。您的感受完全可以理解，我会立即为您处理。",
            "frustration": "我理解您多次往返确实让人烦恼。让我们一起解决这个问题。",
            "confusion": "这个问题可能比较复杂，让我来帮您梳理一下。"
        }
        
        script = scripts.get(emotion, "感谢您的反馈，我会认真处理您的问题。")
        
        # 填充上下文变量
        wait_time = context.get("wait_time", 0)
        return script.format(wait_time=wait_time)


class HumanMachineCollaborator:
    """
    人机协同服务修复机制
    协调AI自动化处理与人工介入
    """
    
    def __init__(self):
        self.escalation_queue: deque = deque()
        self.active_collaborations: Dict[str, Dict] = {}
        self.resolution_templates: Dict[str, str] = self._load_templates()
    
    def _load_templates(self) -> Dict[str, str]:
        """加载解决模板"""
        return {
            "empathy_001": "感谢您的耐心等待，我会立即处理您的问题。",
            "compensation_001": "为您申请了优先办理通道，请您直接到{}号窗口。",
            "escalation_001": "我已为您联系专属客户经理，{}将为您提供一对一服务。"
        }
    
    def should_escalate(
        self,
        emotion: str,
        intensity: float,
        repair_attempts: int,
        context: Dict[str, Any]
    ) -> bool:
        """
        判断是否需要升级人工
        
        升级条件：
        1. 情绪强度极高 (>= 0.9)
        2. 修复尝试次数超过阈值 (>= 3)
        3. 客户明确要求人工
        4. 涉及投诉或复杂问题
        """
        if intensity >= 0.9:
            return True
        
        if repair_attempts >= 3:
            return True
        
        if context.get("customer_requested_human", False):
            return True
        
        if context.get("is_complaint", False):
            return True
        
        return False
    
    def create_collaboration_session(
        self,
        instance_id: str,
        customer_info: Dict[str, Any],
        ai_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        创建人机协同会话
        
        AI处理当前步骤，同时准备人工介入
        """
        session = {
            "session_id": f"collab_{uuid.uuid4().hex[:12]}",
            "instance_id": instance_id,
            "status": "ai_in_progress",
            "customer": customer_info,
            "ai_handling": ai_context,
            "human_ready": False,
            "handoff_notes": "",
            "created_at": datetime.now().isoformat()
        }
        
        self.active_collaborations[instance_id] = session
        return session
    
    def request_human_intervention(
        self,
        instance_id: str,
        reason: str,
        priority: int = 3
    ) -> Dict[str, Any]:
        """
        请求人工介入
        
        Args:
            instance_id: 流程实例ID
            reason: 介入原因
            priority: 优先级 (1-5, 1最高)
        
        Returns:
            介入请求信息
        """
        request = {
            "request_id": f"esc_{uuid.uuid4().hex[:12]}",
            "instance_id": instance_id,
            "reason": reason,
            "priority": priority,
            "status": "pending",
            "requested_at": datetime.now(),
            "assigned_to": None,
            "notes": ""
        }
        
        self.escalation_queue.append(request)
        
        # 更新协作会话状态
        if instance_id in self.active_collaborations:
            self.active_collaborations[instance_id]["status"] = "human_intervening"
            self.active_collaborations[instance_id]["human_ready"] = True
        
        return request
    
    def get_resolution_action(
        self,
        strategy: ServiceRepairStrategy,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        获取解决动作
        
        Args:
            strategy: 修复策略
            context: 上下文信息
        
        Returns:
            解决动作
        """
        actions = {
            ServiceRepairStrategy.EMPATHY_RESPONSE: {
                "type": "message",
                "template": "empathy_001",
                "channel": "any"
            },
            ServiceRepairStrategy.PRIORITY_SERVICE: {
                "type": "action",
                "action": "priority_queue",
                "target_window": context.get("available_window", 1),
                "notes": "已开启VIP优先通道"
            },
            ServiceRepairStrategy.COMPENSATION: {
                "type": "action",
                "action": "apply_compensation",
                "compensation_type": context.get("compensation_type", "fee_reduction"),
                "amount": context.get("compensation_amount", 0)
            },
            ServiceRepairStrategy.ESCALATION: {
                "type": "escalation",
                "target_role": "supervisor",
                "message": "已转接专属客户经理"
            },
            ServiceRepairStrategy.SUPERVISOR_INTERVENTION: {
                "type": "escalation",
                "target_role": "supervisor",
                "message": "主管已接入"
            }
        }
        
        return actions.get(strategy, {"type": "unknown"})
    
    def complete_collaboration(
        self,
        instance_id: str,
        resolution: str,
        customer_satisfied: bool
    ) -> Dict[str, Any]:
        """
        完成人机协同会话
        """
        if instance_id in self.active_collaborations:
            session = self.active_collaborations[instance_id]
            session["status"] = "completed"
            session["resolution"] = resolution
            session["customer_satisfied"] = customer_satisfied
            session["completed_at"] = datetime.now().isoformat()
        
        return {
            "instance_id": instance_id,
            "resolved": True,
            "satisfaction": customer_satisfied
        }


class ServiceFlowStateMachine:
    """
    服务流程状态机
    管理流程实例的状态转换
    """
    
    # 有效状态转换
    VALID_TRANSITIONS = {
        "pending": ["in_progress", "cancelled"],
        "in_progress": ["completed", "cancelled", "failed"],
        "completed": [],
        "cancelled": [],
        "failed": ["in_progress"]  # 允许重试
    }
    
    def __init__(self):
        self.instances: Dict[str, ProcessInstance] = {}
        self.process_definitions: Dict[str, ProcessDefinition] = {}
        self._setup_default_processes()
    
    def _setup_default_processes(self):
        """设置默认流程定义"""
        # 客户投诉处理流程
        complaint_process = ProcessDefinition(
            id="proc_001",
            name="客户投诉处理流程",
            category=ProcessCategory.COMPLAINT,
            version="2.1",
            status=ProcessStatus.ACTIVE,
            description="标准客户投诉处理流程，包含情绪识别和修复机制",
            stages=[
                ProcessStage(
                    name="接收",
                    description="接收客户投诉，记录问题",
                    actions=["acknowledge", "listen", "record"],
                    emotion_adaptive=True
                ),
                ProcessStage(
                    name="评估",
                    description="评估问题严重程度和客户情绪",
                    actions=["analyze", "emotion_assess", "classify"],
                    emotion_adaptive=True
                ),
                ProcessStage(
                    name="处理",
                    description="执行问题处理或修复",
                    actions=["resolve", "compensate", "adjust"],
                    emotion_adaptive=True,
                    human_handoff_allowed=True
                ),
                ProcessStage(
                    name="跟进",
                    description="跟进处理结果，确认客户满意度",
                    actions=["follow_up", "confirm", "document"],
                    emotion_adaptive=False
                ),
                ProcessStage(
                    name="关闭",
                    description="完成流程，生成报告",
                    actions=["close", "archive", "report"],
                    emotion_adaptive=False
                )
            ],
            emotion_triggers={
                "anger": ["empathy_response", "priority_service"],
                "frustration": ["empathy_response"],
                "anxiety": ["empathy_response", "status_update"]
            },
            recovery_strategies={
                "empathy_response": "empathy_001",
                "priority_service": "compensation_001"
            },
            avg_duration_minutes=30,
            satisfaction_rate=0.85
        )
        
        self.process_definitions["proc_001"] = complaint_process
        
        # 业务咨询流程
        inquiry_process = ProcessDefinition(
            id="proc_002",
            name="业务咨询流程",
            category=ProcessCategory.INQUIRY,
            version="1.5",
            status=ProcessStatus.ACTIVE,
            description="标准业务咨询处理流程",
            stages=[
                ProcessStage(name="接待", description="接待客户，了解需求", actions=["greet", "identify"]),
                ProcessStage(name="查询", description="查询相关信息", actions=["search", "retrieve"]),
                ProcessStage(name="解答", description="提供专业解答", actions=["explain", "advise"]),
                ProcessStage(name="确认", description="确认客户理解", actions=["confirm", "close"])
            ],
            avg_duration_minutes=10,
            satisfaction_rate=0.92
        )
        
        self.process_definitions["proc_002"] = inquiry_process
    
    def create_instance(
        self,
        process_id: str,
        user_id: str,
        trigger_type: TriggerType,
        context: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None
    ) -> ProcessInstance:
        """
        创建流程实例
        
        Args:
            process_id: 流程定义ID
            user_id: 用户ID
            trigger_type: 触发类型
            context: 初始上下文
            session_id: 会话ID
        
        Returns:
            流程实例
        """
        if process_id not in self.process_definitions:
            raise ValueError(f"Process {process_id} not found")
        
        process = self.process_definitions[process_id]
        
        # 创建阶段实例
        stage_instances = [
            StageInstance(
                name=stage.name,
                status=StageStatus.PENDING
            )
            for stage in process.stages
        ]
        
        instance = ProcessInstance(
            instance_id=f"inst_{uuid.uuid4().hex[:12]}",
            process_id=process_id,
            process_name=process.name,
            user_id=user_id,
            session_id=session_id,
            status="pending",
            current_stage=process.stages[0].name if process.stages else "",
            stages=stage_instances,
            context=context or {},
            started_at=datetime.now(),
            updated_at=datetime.now(),
            triggered_by=trigger_type
        )
        
        self.instances[instance.instance_id] = instance
        return instance
    
    def transition(
        self,
        instance_id: str,
        new_status: str,
        next_stage: Optional[str] = None,
        emotion_state: Optional[Dict[str, Any]] = None
    ) -> ProcessInstance:
        """
        执行状态转换
        
        Args:
            instance_id: 实例ID
            new_status: 新状态
            next_stage: 下一阶段（可选）
            emotion_state: 情绪状态（可选）
        
        Returns:
            更新后的实例
        """
        if instance_id not in self.instances:
            raise ValueError(f"Instance {instance_id} not found")
        
        instance = self.instances[instance_id]
        
        # 验证状态转换
        valid_next_states = self.VALID_TRANSITIONS.get(instance.status, [])
        if new_status not in valid_next_states:
            raise ValueError(
                f"Invalid transition: {instance.status} -> {new_status}"
            )
        
        # 更新状态
        old_status = instance.status
        instance.status = new_status
        instance.updated_at = datetime.now()
        
        # 如果进入进行中状态，自动开始第一阶段
        if old_status == "pending" and new_status == "in_progress":
            if instance.stages:
                instance.stages[0].status = StageStatus.IN_PROGRESS
                instance.stages[0].started_at = datetime.now()
                instance.current_stage = instance.stages[0].name
        
        # 更新阶段
        if next_stage:
            instance.current_stage = next_stage
            for stage in instance.stages:
                if stage.name == next_stage and stage.status == StageStatus.PENDING:
                    stage.status = StageStatus.IN_PROGRESS
                    stage.started_at = datetime.now()
                    break
        
        # 记录情绪趋势
        if emotion_state:
            instance.emotion_trend.append({
                "timestamp": datetime.now().isoformat(),
                "stage": instance.current_stage,
                "emotion": emotion_state.get("emotion"),
                "intensity": emotion_state.get("intensity", 0)
            })
        
        # 如果完成，更新所有阶段
        if new_status == "completed":
            instance.completed_at = datetime.now()
            for stage in instance.stages:
                if stage.status == StageStatus.IN_PROGRESS:
                    stage.status = StageStatus.COMPLETED
                    stage.completed_at = datetime.now()
        
        return instance
    
    def advance_stage(
        self,
        instance_id: str,
        emotion_state: Optional[Dict[str, Any]] = None
    ) -> ProcessInstance:
        """
        推进到下一阶段
        
        Args:
            instance_id: 实例ID
            emotion_state: 当前情绪状态
        
        Returns:
            更新后的实例
        """
        if instance_id not in self.instances:
            raise ValueError(f"Instance {instance_id} not found")
        
        instance = self.instances[instance_id]
        
        # 找到当前阶段索引
        current_idx = -1
        for i, stage in enumerate(instance.stages):
            if stage.name == instance.current_stage:
                current_idx = i
                break
        
        if current_idx == -1:
            raise ValueError(f"Current stage {instance.current_stage} not found")
        
        # 标记当前阶段完成
        instance.stages[current_idx].status = StageStatus.COMPLETED
        instance.stages[current_idx].completed_at = datetime.now()
        if emotion_state:
            instance.stages[current_idx].emotion_at_exit = emotion_state.get("emotion")
        
        # 检查是否有下一阶段
        if current_idx + 1 < len(instance.stages):
            next_stage = instance.stages[current_idx + 1]
            next_stage.status = StageStatus.IN_PROGRESS
            next_stage.started_at = datetime.now()
            next_stage.emotion_at_entry = emotion_state.get("emotion") if emotion_state else None
            instance.current_stage = next_stage.name
            instance.updated_at = datetime.now()
        else:
            # 所有阶段完成，标记流程完成
            instance.status = "completed"
            instance.completed_at = datetime.now()
        
        # 记录情绪趋势
        if emotion_state:
            instance.emotion_trend.append({
                "timestamp": datetime.now().isoformat(),
                "stage": instance.current_stage,
                "emotion": emotion_state.get("emotion"),
                "intensity": emotion_state.get("intensity", 0)
            })
        
        return instance
    
    def get_instance(self, instance_id: str) -> Optional[ProcessInstance]:
        """获取流程实例"""
        return self.instances.get(instance_id)
    
    def get_processes(
        self,
        category: Optional[ProcessCategory] = None,
        status: Optional[ProcessStatus] = None
    ) -> List[ProcessDefinition]:
        """获取流程定义列表"""
        processes = list(self.process_definitions.values())
        
        if category:
            processes = [p for p in processes if p.category == category]
        
        if status:
            processes = [p for p in processes if p.status == status]
        
        return processes
