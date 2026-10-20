"""
情绪识别模拟测试模块
Emotion Recognition Simulation Test Module

用于测试和演示系统的模拟数据生成器
支持多种场景模拟：等候、自助操作、异常处理等
"""

import random
import time
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import json


# ============== 模拟场景定义 ==============

@dataclass
class SimulationScenario:
    """模拟场景配置"""
    name: str
    description: str
    duration_seconds: int
    emotion_sequence: List[Dict[str, Any]]  # [{emotion, intensity, duration}]
    expected_alerts: List[str]  # 预期触发的告警类型


# 预设模拟场景
SCENARIOS = {
    # 场景1：客户等待焦虑
    "waiting_anxiety": SimulationScenario(
        name="等待焦虑场景",
        description="客户在网点等待时间较长，逐渐产生焦虑情绪",
        duration_seconds=180,
        emotion_sequence=[
            {"emotion": "neutral", "intensity": 0.3, "duration": 30},
            {"emotion": "anxiety", "intensity": 0.5, "duration": 60},
            {"emotion": "anxiety", "intensity": 0.65, "duration": 60},
            {"emotion": "frustration", "intensity": 0.6, "duration": 30},
        ],
        expected_alerts=["long_term_anxiety", "service_recovery_needed"]
    ),
    
    # 场景2：自助设备操作失败
    "self_service_failure": SimulationScenario(
        name="自助操作失败场景",
        description="客户在自助设备上多次操作失败，情绪逐渐恶化",
        duration_seconds=120,
        emotion_sequence=[
            {"emotion": "neutral", "intensity": 0.3, "duration": 20},
            {"emotion": "confusion", "intensity": 0.5, "duration": 30},
            {"emotion": "frustration", "intensity": 0.65, "duration": 40},
            {"emotion": "anger", "intensity": 0.75, "duration": 30},
        ],
        expected_alerts=["negative_emotion_escalation", "service_recovery_needed"]
    ),
    
    # 场景3：投诉升级
    "complaint_escalation": SimulationScenario(
        name="投诉升级场景",
        description="客户因服务问题产生强烈不满，情绪快速升级",
        duration_seconds=60,
        emotion_sequence=[
            {"emotion": "anger", "intensity": 0.8, "duration": 20},
            {"emotion": "anger", "intensity": 0.88, "duration": 20},
            {"emotion": "anger", "intensity": 0.92, "duration": 20},
        ],
        expected_alerts=["conflict_risk"]
    ),
    
    # 场景4：正常服务流程
    "normal_service": SimulationScenario(
        name="正常服务场景",
        description="客户获得良好服务，情绪稳定或正向",
        duration_seconds=120,
        emotion_sequence=[
            {"emotion": "neutral", "intensity": 0.3, "duration": 30},
            {"emotion": "satisfaction", "intensity": 0.6, "duration": 60},
            {"emotion": "satisfaction", "intensity": 0.7, "duration": 30},
        ],
        expected_alerts=[]
    ),
    
    # 场景5：老年客户服务
    "elderly_service": SimulationScenario(
        name="老年客户服务场景",
        description="老年客户对自助设备不熟悉，需要更多帮助",
        duration_seconds=180,
        emotion_sequence=[
            {"emotion": "confusion", "intensity": 0.5, "duration": 60},
            {"emotion": "confusion", "intensity": 0.55, "duration": 60},
            {"emotion": "anxiety", "intensity": 0.5, "duration": 60},
        ],
        expected_alerts=["long_term_anxiety"]
    ),
    
    # 场景6：VIP客户紧急业务
    "vip_urgent": SimulationScenario(
        name="VIP紧急业务场景",
        description="VIP客户有紧急业务需求，等待时间容忍度低",
        duration_seconds=90,
        emotion_sequence=[
            {"emotion": "anxiety", "intensity": 0.7, "duration": 30},
            {"emotion": "anxiety", "intensity": 0.8, "duration": 30},
            {"emotion": "anger", "intensity": 0.75, "duration": 30},
        ],
        expected_alerts=["long_term_anxiety", "conflict_risk"]
    )
}


# ============== 模拟数据生成器 ==============

class SimulationDataGenerator:
    """模拟数据生成器"""
    
    # 情绪类型映射（用于生成符合场景的输入）
    EMOTION_TEXT_MAP = {
        "neutral": ["好的", "明白", "了解"],
        "anxiety": ["等太久了", "还要等多久", "有点着急", "能不能快点"],
        "frustration": ["怎么这么慢", "已经等了好久了", "太麻烦了"],
        "anger": ["我要投诉", "太差了", "完全不能接受", "这是什么服务"],
        "confusion": ["这个怎么操作", "看不懂", "不知道怎么弄"],
        "satisfaction": ["很好", "谢谢", "服务不错", "很快"]
    }
    
    @classmethod
    def generate_text_input(cls, emotion: str, intensity: float) -> str:
        """根据情绪生成模拟文本输入"""
        templates = cls.EMOTION_TEXT_MAP.get(emotion, ["..."])
        base_text = random.choice(templates)
        
        # 根据强度调整表达
        if intensity > 0.8:
            base_text = "非常" + base_text if random.random() > 0.5 else base_text + "！！"
        elif intensity > 0.6:
            base_text = base_text + "！"
        
        return base_text
    
    @classmethod
    def generate_fake_image_base64(cls) -> str:
        """生成模拟图像数据的base64（占位符）"""
        # 实际应用中这里应该是真实的图像数据
        return "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
    
    @classmethod
    def generate_fake_audio_bytes(cls) -> bytes:
        """生成模拟音频数据的bytes（占位符）"""
        # 实际应用中这里应该是真实的音频数据
        return b"FAKE_AUDIO_DATA_PLACEHOLDER"


# ============== 模拟测试运行器 ==============

class SimulationTestRunner:
    """
    模拟测试运行器
    
    用于自动运行各种场景测试，验证系统响应
    """
    
    def __init__(self, api_base_url: str = "http://localhost:8001"):
        self.api_base_url = api_base_url
        self.scenarios = SCENARIOS
        self.results: List[Dict[str, Any]] = []
    
    def run_scenario(
        self, 
        scenario_name: str,
        session_id: str,
        use_http: bool = False
    ) -> Dict[str, Any]:
        """
        运行单个场景模拟
        
        Args:
            scenario_name: 场景名称
            session_id: 会话ID
            use_http: 是否通过HTTP调用API
            
        Returns:
            测试结果
        """
        if scenario_name not in self.scenarios:
            raise ValueError(f"Unknown scenario: {scenario_name}")
        
        scenario = self.scenarios[scenario_name]
        start_time = datetime.now()
        
        # 记录情绪历史
        emotion_history = []
        alerts_triggered = []
        api_calls = []
        
        print(f"\n{'='*60}")
        print(f"开始模拟测试: {scenario.name}")
        print(f"描述: {scenario.description}")
        print(f"预计持续: {scenario.duration_seconds}秒")
        print(f"{'='*60}")
        
        # 模拟时间推进
        current_time = 0
        for step in scenario.emotion_sequence:
            emotion = step["emotion"]
            intensity = step["intensity"]
            duration = step["duration"]
            
            print(f"\n[时间 {current_time}s] 情绪: {emotion}, 强度: {intensity}")
            
            # 模拟API调用
            if use_http:
                # TODO: 通过HTTP调用真实API
                pass
            else:
                # 本地模拟调用
                from src.emotion_recognition.models import (
                    create_engine, EmotionType
                )
                
                engine = create_engine(backend="mock")
                
                # 模拟输入数据
                text = SimulationDataGenerator.generate_text_input(emotion, intensity)
                print(f"  输入文本: {text}")
                
                # 调用识别
                result = engine.recognize_from_multi_modal(
                    session_id=session_id,
                    text=text,
                    context={
                        "wait_time_seconds": current_time,
                        "emotion_history": emotion_history[-3:] if len(emotion_history) > 3 else emotion_history
                    }
                )
                
                # 记录结果
                step_result = {
                    "timestamp": (start_time + timedelta(seconds=current_time)).isoformat(),
                    "time_offset": current_time,
                    "emotion": emotion,
                    "intensity": intensity,
                    "recognized_emotion": result.fused.primary_emotion.value if result.fused else None,
                    "confidence": result.fused.fused_confidence if result.fused else 0,
                    "alert_triggered": result.alert.get("triggered") if result.alert else False,
                    "alert_type": result.alert.get("type") if result.alert else None,
                    "active_modalities": [m.value for m in result.active_modalities] if result else []
                }
                
                api_calls.append(step_result)
                emotion_history.append(result.fused if result.fused else None)
                
                # 检查告警
                if result.alert and result.alert.get("triggered"):
                    alerts_triggered.append(result.alert.get("type"))
                    print(f"  ⚠️ 告警触发: {result.alert.get('type')}")
                    print(f"  建议: {result.alert.get('recommendation')}")
                
                print(f"  识别结果: {step_result['recognized_emotion']} (置信度: {step_result['confidence']:.2f})")
            
            current_time += duration
            time.sleep(0.1)  # 模拟延迟
        
        # 汇总结果
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # 计算指标
        alert_match = all(a in alerts_triggered for a in scenario.expected_alerts)
        
        result = {
            "scenario": scenario_name,
            "scenario_name": scenario.name,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "duration_seconds": duration,
            "total_steps": len(scenario.emotion_sequence),
            "alerts_triggered": alerts_triggered,
            "expected_alerts": scenario.expected_alerts,
            "alert_match": alert_match,
            "steps": api_calls,
            "status": "passed" if alert_match else "needs_review"
        }
        
        self.results.append(result)
        
        # 打印结果摘要
        print(f"\n{'='*60}")
        print(f"测试完成: {scenario.name}")
        print(f"持续时间: {duration:.1f}秒")
        print(f"触发告警: {len(alerts_triggered)} 次")
        print(f"告警列表: {alerts_triggered}")
        print(f"预期告警: {scenario.expected_alerts}")
        print(f"匹配结果: {'✅ 通过' if alert_match else '⚠️ 需复核'}")
        print(f"{'='*60}\n")
        
        return result
    
    def run_all_scenarios(self, session_prefix: str = "sim_test") -> List[Dict[str, Any]]:
        """运行所有预设场景"""
        print("\n" + "="*60)
        print("开始批量模拟测试")
        print(f"共 {len(self.scenarios)} 个场景")
        print("="*60)
        
        results = []
        for i, scenario_name in enumerate(self.scenarios.keys()):
            session_id = f"{session_prefix}_{scenario_name}_{int(time.time())}"
            result = self.run_scenario(scenario_name, session_id)
            results.append(result)
        
        # 打印汇总
        self.print_summary(results)
        
        return results
    
    def print_summary(self, results: List[Dict[str, Any]]):
        """打印测试汇总"""
        print("\n" + "="*60)
        print("批量测试汇总")
        print("="*60)
        
        passed = sum(1 for r in results if r["status"] == "passed")
        total = len(results)
        
        for r in results:
            status_icon = "✅" if r["status"] == "passed" else "⚠️"
            print(f"{status_icon} {r['scenario_name']}: {r['status']}")
            print(f"   告警触发: {r['alerts_triggered']}")
        
        print(f"\n总计: {passed}/{total} 通过")
        print("="*60)
    
    def export_results(self, filepath: str):
        """导出测试结果到JSON文件"""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump({
                "test_time": datetime.now().isoformat(),
                "total_scenarios": len(self.results),
                "results": self.results
            }, f, ensure_ascii=False, indent=2)
        print(f"测试结果已导出到: {filepath}")


# ============== 命令行接口 ==============

def main():
    """命令行入口"""
    import argparse
    
    parser = argparse.ArgumentParser(description="情绪识别模拟测试")
    parser.add_argument(
        "--scenario", 
        choices=list(SCENARIOS.keys()) + ["all"],
        default="all",
        help="选择测试场景"
    )
    parser.add_argument(
        "--session",
        type=str,
        default="cli_test",
        help="会话ID前缀"
    )
    parser.add_argument(
        "--export",
        type=str,
        help="导出结果到文件"
    )
    
    args = parser.parse_args()
    
    runner = SimulationTestRunner()
    
    if args.scenario == "all":
        results = runner.run_all_scenarios(args.session)
    else:
        result = runner.run_scenario(args.scenario, f"{args.session}_{args.scenario}")
        results = [result]
    
    if args.export:
        runner.export_results(args.export)


if __name__ == "__main__":
    main()
