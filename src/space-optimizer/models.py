"""
网点空间优化模块 - Z-AHP模糊层次分析法与Z-TOPSIS方案排序
Space Optimizer Module - Z-AHP Fuzzy Analytic Hierarchy Process & Z-TOPSIS

基于论文第六章第6.1节：网点空间优化评价体系
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Optional, Tuple, Any
from datetime import datetime
from collections import defaultdict
import numpy as np


class EvaluationIndicator(Enum):
    """评价指标枚举"""
    # 服务效率指标
    AVG_WAIT_TIME = "avg_wait_time"           # 平均等候时间
    AVG_SERVICE_TIME = "avg_service_time"     # 平均服务时间
    SUCCESS_RATE = "success_rate"             # 业务成功率
    
    # 客户体验指标
    SATISFACTION_SCORE = "satisfaction_score" # 满意度评分
    EMOTION_POSITIVE_RATE = "emotion_positive_rate"  # 情绪正面率
    COMPLAINT_RATE = "complaint_rate"         # 投诉率
    
    # 空间利用指标
    AREA_EFFICIENCY = "area_efficiency"       # 面积效率
    FUNCTIONAL_LAYOUT_SCORE = "functional_layout_score"  # 功能布局评分
    FLOW_LINE_SCORE = "flow_line_score"       # 动线评分


class ZoneType(Enum):
    """网点功能区类型"""
    QUEUE_AREA = "queue_area"                 # 等候区
    SERVICE_AREA = "service_area"             # 服务区
    SELF_SERVICE_AREA = "self_service_area"   # 自助服务区
    LOUNGE_AREA = "lounge_area"               # 休息区
    AI_INTERACTION_AREA = "ai_interaction_area"  # AI互动区
    VIP_AREA = "vip_area"                     # VIP区


@dataclass
class FuzzyNumber:
    """三角模糊数 (l, m, u) - 用于模糊判断矩阵"""
    l: float  # 下界 (lower)
    m: float  # 中值 (medium)
    u: float  # 上界 (upper)
    
    def __add__(self, other: "FuzzyNumber") -> "FuzzyNumber":
        return FuzzyNumber(self.l + other.l, self.m + other.m, self.u + other.u)
    
    def __mul__(self, other: "FuzzyNumber") -> "FuzzyNumber":
        return FuzzyNumber(self.l * other.l, self.m * other.m, self.u * other.u)
    
    def __truediv__(self, other: "FuzzyNumber") -> "FuzzyNumber":
        return FuzzyNumber(self.l / other.u, self.m / other.m, self.u / other.l)
    
    def __rmul__(self, scalar: float) -> "FuzzyNumber":
        return FuzzyNumber(self.l * scalar, self.m * scalar, self.u * scalar)
    
    def defuzzify(self) -> float:
        """去模糊化 - 使用重心法"""
        return (self.l + self.m + self.u) / 3
    
    @staticmethod
    def from_value(v: float, uncertainty: float = 0.1) -> "FuzzyNumber":
        """从确定值创建模糊数"""
        delta = v * uncertainty
        return FuzzyNumber(max(0, v - delta), v, min(1, v + delta))


@dataclass
class FuzzyComparisonMatrix:
    """模糊判断矩阵"""
    size: int
    matrix: List[List[FuzzyNumber]] = field(default_factory=list)
    
    def __post_init__(self):
        if not self.matrix:
            self.matrix = [
                [FuzzyNumber(1, 1, 1) for _ in range(self.size)]
                for _ in range(self.size)
            ]
    
    def set_value(self, i: int, j: int, value: FuzzyNumber):
        """设置矩阵元素"""
        self.matrix[i][j] = value
    
    def get_value(self, i: int, j: int) -> FuzzyNumber:
        return self.matrix[i][j]


@dataclass
class IndicatorData:
    """指标数据"""
    indicator: EvaluationIndicator
    value: float
    weight: Optional[float] = None
    fuzzy_value: Optional[FuzzyNumber] = None
    
    def __post_init__(self):
        if self.fuzzy_value is None:
            self.fuzzy_value = FuzzyNumber.from_value(self.value)


@dataclass
class BranchEvaluation:
    """网点评价结果"""
    branch_id: str
    branch_name: str
    overall_score: float
    rank: int
    total_branches: int
    indicators: Dict[str, Dict[str, Any]]
    recommendations: List[Dict[str, str]]
    evaluation_period: str
    generated_at: datetime = field(default_factory=datetime.now)


@dataclass
class OptimizationSuggestion:
    """优化建议"""
    type: str
    current: str
    proposed: str
    expected_impact: str
    zone: Optional[str] = None
    priority: int = 1


@dataclass
class OptimizationResult:
    """优化结果"""
    branch_id: str
    current_layout_score: float
    optimized_layout_score: float
    improvement: str
    suggestions: List[OptimizationSuggestion]
    investment_estimate: Dict[str, Any]


class ZAHPCalculator:
    """
    Z-AHP模糊层次分析法计算器
    实现基于三角模糊数的层次分析法计算指标权重
    """
    
    # 模糊标度定义 ( Saaty 1-9 scale 的模糊扩展 )
    FUZZY_SCALE = {
        1: FuzzyNumber(1, 1, 1),
        2: FuzzyNumber(1, 1.5, 2),
        3: FuzzyNumber(1.5, 2, 2.5),
        4: FuzzyNumber(2, 2.5, 3),
        5: FuzzyNumber(2.5, 3, 3.5),
        6: FuzzyNumber(3, 3.5, 4),
        7: FuzzyNumber(3.5, 4, 4.5),
        8: FuzzyNumber(4, 4.5, 5),
        9: FuzzyNumber(4.5, 5, 5.5),
    }
    
    def __init__(self):
        self.criterion_weights: Dict[str, float] = {}
        self.sub_criterion_weights: Dict[str, Dict[str, float]] = defaultdict(dict)
    
    def calculate_criterion_weights(
        self, 
        comparisons: Dict[Tuple[str, str], float]
    ) -> Dict[str, float]:
        """
        计算准则层权重
        
        Args:
            comparisons: 准则间两两比较值，key为(criterion_i, criterion_j)
                        value为相对重要性 (1-9 scale)
        
        Returns:
            各准则的权重字典
        """
        # 构建模糊判断矩阵
        criteria = sorted(set(c for c, _ in comparisons.keys()) | set(c for _, c in comparisons.keys()))
        n = len(criteria)
        
        fuzzy_matrix = FuzzyComparisonMatrix(n)
        
        for i, ci in enumerate(criteria):
            for j, cj in enumerate(criteria):
                if i == j:
                    fuzzy_matrix.set_value(i, j, FuzzyNumber(1, 1, 1))
                elif (ci, cj) in comparisons:
                    value = comparisons[(ci, cj)]
                    # 转换为模糊数
                    if value >= 1:
                        fuzzy_matrix.set_value(i, j, FuzzyNumber.from_value(value, 0.15))
                        fuzzy_matrix.set_value(j, i, FuzzyNumber.from_value(1/value, 0.15))
        
        # 计算权重
        weights = self._fuzzy_weight_vector(fuzzy_matrix)
        
        for i, criterion in enumerate(criteria):
            self.criterion_weights[criterion] = weights[i]
        
        return self.criterion_weights
    
    def _fuzzy_weight_vector(self, matrix: FuzzyComparisonMatrix) -> List[float]:
        """计算模糊权重向量"""
        n = matrix.size
        geometric_means = []
        
        for i in range(n):
            # 计算第i行的几何平均
            product = FuzzyNumber(1, 1, 1)
            for j in range(n):
                product = product * matrix.get_value(i, j)
            # n次方根
            geo_mean = FuzzyNumber(
                product.l ** (1/n),
                product.m ** (1/n),
                product.u ** (1/n)
            )
            geometric_means.append(geo_mean)
        
        # 归一化
        sum_fuzzy = FuzzyNumber(0, 0, 0)
        for gm in geometric_means:
            sum_fuzzy = sum_fuzzy + gm
        
        weights = []
        for gm in geometric_means:
            normalized = gm / sum_fuzzy
            weights.append(normalized.defuzzify())
        
        # 再次归一化确保和为1
        total = sum(weights)
        weights = [w / total for w in weights]
        
        return weights
    
    def calculate_consistency_ratio(self, matrix: FuzzyComparisonMatrix) -> float:
        """计算一致性比率 CR"""
        n = matrix.size
        
        # 将模糊矩阵去模糊化
        crisp_matrix = np.array([
            [matrix.get_value(i, j).defuzzify() for j in range(n)]
            for i in range(n)
        ])
        
        # 计算lambda_max
        eigenvalues = np.linalg.eigvals(crisp_matrix)
        lambda_max = np.max(np.real(eigenvalues))
        
        # 计算CI
        ci = (lambda_max - n) / (n - 1) if n > 1 else 0
        
        # RI值 (随机一致性指标)
        ri_values = {1: 0, 2: 0, 3: 0.58, 4: 0.90, 5: 1.12, 6: 1.24, 7: 1.32, 8: 1.41, 9: 1.45, 10: 1.49}
        ri = ri_values.get(n, 1.49)
        
        # 计算CR
        cr = ci / ri if ri > 0 else 0
        
        return cr


class ZTOPSISOptimizer:
    """
    Z-TOPSIS模糊TOPSIS法方案排序优化器
    实现基于模糊数的TOPSIS多准则决策方法
    """
    
    def __init__(self):
        self.decision_matrix: Optional[np.ndarray] = None
        self.weights: Optional[np.ndarray] = None
        self.fuzzy_decision_matrix: Optional[List[List[FuzzyNumber]]] = None
    
    def build_fuzzy_decision_matrix(
        self,
        alternatives: List[str],
        criteria: List[str],
        values: Dict[Tuple[str, str], float]
    ) -> List[List[FuzzyNumber]]:
        """
        构建模糊决策矩阵
        
        Args:
            alternatives: 方案列表
            criteria: 准则列表
            values: 决策数据，key为(alternative, criterion)
        
        Returns:
            模糊决策矩阵
        """
        n_alt = len(alternatives)
        n_crit = len(criteria)
        
        fuzzy_matrix = []
        for i, alt in enumerate(alternatives):
            row = []
            for j, crit in enumerate(criteria):
                value = values.get((alt, crit), 0.5)
                row.append(FuzzyNumber.from_value(value, 0.1))
            fuzzy_matrix.append(row)
        
        self.fuzzy_decision_matrix = fuzzy_matrix
        return fuzzy_matrix
    
    def normalize_fuzzy_matrix(
        self,
        fuzzy_matrix: List[List[FuzzyNumber]],
        criteria_types: Dict[str, bool]  # True: benefit, False: cost
    ) -> List[List[FuzzyNumber]]:
        """
        规范化模糊决策矩阵
        
        Args:
            criteria_types: 准则类型，True为效益型，False为成本型
        """
        n_alt = len(fuzzy_matrix)
        n_crit = len(fuzzy_matrix[0]) if fuzzy_matrix else 0
        
        # 找出每列的最大最小值
        col_min = [float('inf')] * n_crit
        col_max = [float('-inf')] * n_crit
        
        for i in range(n_alt):
            for j in range(n_crit):
                val = fuzzy_matrix[i][j]
                col_min[j] = min(col_min[j], val.l, val.u)
                col_max[j] = max(col_max[j], val.l, val.u)
        
        normalized = []
        for i in range(n_alt):
            row = []
            for j, crit in enumerate(criteria):
                val = fuzzy_matrix[i][j]
                if criteria_types.get(crit, True):  # 效益型
                    # (x - min) / (max - min)
                    range_val = col_max[j] - col_min[j]
                    if range_val > 0:
                        norm_val = FuzzyNumber(
                            (val.l - col_min[j]) / range_val,
                            (val.m - col_min[j]) / range_val,
                            (val.u - col_min[j]) / range_val
                        )
                    else:
                        norm_val = FuzzyNumber(0.5, 0.5, 0.5)
                else:  # 成本型
                    # (max - x) / (max - min)
                    range_val = col_max[j] - col_min[j]
                    if range_val > 0:
                        norm_val = FuzzyNumber(
                            (col_max[j] - val.u) / range_val,
                            (col_max[j] - val.m) / range_val,
                            (col_max[j] - val.l) / range_val
                        )
                    else:
                        norm_val = FuzzyNumber(0.5, 0.5, 0.5)
                row.append(norm_val)
            normalized.append(row)
        
        return normalized
    
    def calculate_weights(self, criteria: List[str], weights: Dict[str, float]) -> np.ndarray:
        """计算准则权重向量"""
        self.weights = np.array([weights.get(c, 0.0) for c in criteria])
        return self.weights
    
    def calculate_topsis_scores(
        self,
        alternatives: List[str],
        criteria: List[str],
        values: Dict[Tuple[str, str], float],
        weights: Dict[str, float],
        criteria_types: Dict[str, bool]
    ) -> Dict[str, Tuple[float, int]]:
        """
        计算TOPSIS评分并排序
        
        Returns:
            Dict[alternative, (score, rank)]
        """
        # 构建并规范化决策矩阵
        fuzzy_matrix = self.build_fuzzy_decision_matrix(alternatives, criteria, values)
        normalized = self.normalize_fuzzy_matrix(fuzzy_matrix, criteria_types)
        
        # 加权规范化矩阵
        weight_array = self.calculate_weights(criteria, weights)
        weighted = []
        for i in range(len(alternatives)):
            row = []
            for j in range(len(criteria)):
                w = weight_array[j]
                val = normalized[i][j]
                row.append(FuzzyNumber(val.l * w, val.m * w, val.u * w))
            weighted.append(row)
        
        # 计算正理想解和负理想解
        n_alt = len(alternatives)
        n_crit = len(criteria)
        
        pis = []  # Positive Ideal Solution
        nis = []  # Negative Ideal Solution
        
        for j in range(n_crit):
            l_vals = [weighted[i][j].l for i in range(n_alt)]
            m_vals = [weighted[i][j].m for i in range(n_alt)]
            u_vals = [weighted[i][j].u for i in range(n_alt)]
            
            if criteria_types.get(criteria[j], True):  # 效益型
                pis.append(FuzzyNumber(max(l_vals), max(m_vals), max(u_vals)))
                nis.append(FuzzyNumber(min(l_vals), min(m_vals), min(u_vals)))
            else:  # 成本型
                pis.append(FuzzyNumber(min(l_vals), min(m_vals), min(u_vals)))
                nis.append(FuzzyNumber(max(l_vals), max(m_vals), max(u_vals)))
        
        # 计算各方案到正负理想解的距离
        scores = []
        for i in range(n_alt):
            d_pos = 0.0
            d_neg = 0.0
            
            for j in range(n_crit):
                d_pos += (weighted[i][j] - pis[j]).defuzzify() ** 2
                d_neg += (weighted[i][j] - nis[j]).defuzzify() ** 2
            
            d_pos = d_pos ** 0.5
            d_neg = d_neg ** 0.5
            
            # 计算相对贴近度
            if d_pos + d_neg > 0:
                score = d_neg / (d_pos + d_neg)
            else:
                score = 0.5
            
            scores.append(score)
        
        # 排序
        sorted_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)
        
        results = {}
        for rank, idx in enumerate(sorted_indices, 1):
            results[alternatives[idx]] = (scores[idx], rank)
        
        return results


class BranchSpaceEvaluator:
    """
    网点功能区评价模型
    综合使用Z-AHP和Z-TOPSIS对网点空间进行评价和优化
    """
    
    # 默认准则权重 (服务效率, 客户体验, 空间利用)
    DEFAULT_CRITERION_WEIGHTS = {
        "service_efficiency": 0.35,
        "customer_experience": 0.40,
        "space_utilization": 0.25
    }
    
    # 各准则下的子指标权重
    SUB_INDICATOR_WEIGHTS = {
        "service_efficiency": {
            EvaluationIndicator.AVG_WAIT_TIME.value: 0.40,
            EvaluationIndicator.AVG_SERVICE_TIME.value: 0.30,
            EvaluationIndicator.SUCCESS_RATE.value: 0.30,
        },
        "customer_experience": {
            EvaluationIndicator.SATISFACTION_SCORE.value: 0.45,
            EvaluationIndicator.EMOTION_POSITIVE_RATE.value: 0.30,
            EvaluationIndicator.COMPLAINT_RATE.value: 0.25,
        },
        "space_utilization": {
            EvaluationIndicator.AREA_EFFICIENCY.value: 0.35,
            EvaluationIndicator.FUNCTIONAL_LAYOUT_SCORE.value: 0.35,
            EvaluationIndicator.FLOW_LINE_SCORE.value: 0.30,
        }
    }
    
    def __init__(self):
        self.ahp = ZAHPCalculator()
        self.topsis = ZTOPSISOptimizer()
        self._weights_calculated = False
    
    def calculate_weights(
        self,
        criterion_comparisons: Optional[Dict[Tuple[str, str], float]] = None
    ) -> Dict[str, float]:
        """
        计算指标权重
        
        Args:
            criterion_comparisons: 准则间两两比较矩阵
        
        Returns:
            权重字典
        """
        if criterion_comparisons:
            return self.ahp.calculate_criterion_weights(criterion_comparisons)
        else:
            return self.DEFAULT_CRITERION_WEIGHTS.copy()
    
    def evaluate_branch(
        self,
        branch_id: str,
        branch_name: str,
        indicator_data: Dict[str, float],
        all_branch_scores: Optional[List[float]] = None
    ) -> BranchEvaluation:
        """
        评价单个网点
        
        Args:
            branch_id: 网点ID
            branch_name: 网点名称
            indicator_data: 指标数据
            all_branch_scores: 所有网点评分用于计算排名
        
        Returns:
            网点评价结果
        """
        # 计算各准则得分
        scores = {}
        
        # 服务效率
        se_data = indicator_data.get("service_efficiency", {})
        se_score = self._calculate_criterion_score(
            se_data,
            self.SUB_INDICATOR_WEIGHTS["service_efficiency"]
        )
        scores["service_efficiency"] = {
            "score": se_score,
            "metrics": se_data
        }
        
        # 客户体验
        ce_data = indicator_data.get("customer_experience", {})
        ce_score = self._calculate_criterion_score(
            ce_data,
            self.SUB_INDICATOR_WEIGHTS["customer_experience"]
        )
        scores["customer_experience"] = {
            "score": ce_score,
            "metrics": ce_data
        }
        
        # 空间利用
        su_data = indicator_data.get("space_utilization", {})
        su_score = self._calculate_criterion_score(
            su_data,
            self.SUB_INDICATOR_WEIGHTS["space_utilization"]
        )
        scores["space_utilization"] = {
            "score": su_score,
            "metrics": su_data
        }
        
        # 计算综合得分
        overall_score = (
            se_score * self.DEFAULT_CRITERION_WEIGHTS["service_efficiency"] +
            ce_score * self.DEFAULT_CRITERION_WEIGHTS["customer_experience"] +
            su_score * self.DEFAULT_CRITERION_WEIGHTS["space_utilization"]
        )
        
        # 计算排名
        rank = 1
        if all_branch_scores:
            rank = sum(1 for s in all_branch_scores if s > overall_score) + 1
        
        # 生成建议
        recommendations = self._generate_recommendations(scores)
        
        return BranchEvaluation(
            branch_id=branch_id,
            branch_name=branch_name,
            overall_score=round(overall_score, 1),
            rank=rank,
            total_branches=len(all_branch_scores) if all_branch_scores else 1,
            indicators=scores,
            recommendations=recommendations,
            evaluation_period=datetime.now().strftime("%Y-%m-%d")
        )
    
    def _calculate_criterion_score(
        self,
        data: Dict[str, float],
        weights: Dict[str, float]
    ) -> float:
        """计算准则层得分"""
        score = 0.0
        for indicator, weight in weights.items():
            value = data.get(indicator, 0.0)
            # 标准化到0-100
            normalized = min(100, max(0, value * 100)) if indicator != "complaint_rate" else min(100, max(0, (1 - value) * 100))
            score += normalized * weight
        return round(score, 1)
    
    def _generate_recommendations(self, scores: Dict[str, Dict]) -> List[Dict[str, str]]:
        """生成优化建议"""
        recommendations = []
        
        for criterion, data in scores.items():
            score = data["score"]
            metrics = data.get("metrics", {})
            
            if score < 70:
                if criterion == "service_efficiency":
                    if metrics.get("avg_wait_time", 0) > 15:
                        recommendations.append({
                            "area": "等候区",
                            "issue": "等候时间较长",
                            "suggestion": "增加智能导览设备，分流客户"
                        })
                    if metrics.get("success_rate", 1) < 0.95:
                        recommendations.append({
                            "area": "服务区",
                            "issue": "业务成功率偏低",
                            "suggestion": "优化业务办理流程，加强员工培训"
                        })
                
                elif criterion == "customer_experience":
                    if metrics.get("emotion_positive_rate", 0) < 0.75:
                        recommendations.append({
                            "area": "整体服务",
                            "issue": "客户情绪正面率偏低",
                            "suggestion": "部署情绪识别系统，及时干预负面情绪"
                        })
                    if metrics.get("complaint_rate", 0) > 0.03:
                        recommendations.append({
                            "area": "客户关系",
                            "issue": "投诉率偏高",
                            "suggestion": "建立快速投诉处理机制"
                        })
                
                elif criterion == "space_utilization":
                    if metrics.get("area_efficiency", 0) < 0.7:
                        recommendations.append({
                            "area": "功能布局",
                            "issue": "面积使用效率低",
                            "suggestion": "重新规划功能区布局，提高空间利用率"
                        })
                    if metrics.get("flow_line_score", 0) < 0.7:
                        recommendations.append({
                            "area": "动线设计",
                            "issue": "客户动线不顺畅",
                            "suggestion": "优化引导标识，改善客户流向"
                        })
        
        return recommendations[:5]  # 最多返回5条建议
    
    def optimize_layout(
        self,
        branch_id: str,
        current_scores: Dict[str, float],
        target_improvement: float = 0.15
    ) -> OptimizationResult:
        """
        生成网点布局优化方案
        
        Args:
            branch_id: 网点ID
            current_scores: 当前各指标得分
            target_improvement: 目标提升幅度
        
        Returns:
            优化结果
        """
        suggestions = []
        current_overall = sum(
            current_scores.get(k, 0) * w 
            for k, w in self.DEFAULT_CRITERION_WEIGHTS.items()
        )
        
        # 空间利用优化建议
        if current_scores.get("area_efficiency", 0) < 0.75:
            suggestions.append(OptimizationSuggestion(
                type="zone_reallocation",
                current="等候区: 30㎡, 15座位",
                proposed="等候区: 25㎡, 20座位 + AI互动区: 5㎡",
                expected_impact="等候满意度提升15%",
                zone="等候区",
                priority=1
            ))
        
        if current_scores.get("flow_line_score", 0) < 0.75:
            suggestions.append(OptimizationSuggestion(
                type="flow_optimization",
                current="单一入口",
                proposed="双入口+智能分流",
                expected_impact="平均等候时间减少20%",
                zone="入口",
                priority=2
            ))
        
        if current_scores.get("functional_layout_score", 0) < 0.75:
            suggestions.append(OptimizationSuggestion(
                type="equipment_upgrade",
                current="传统取号机",
                proposed="智能导览终端+自助服务机",
                expected_impact="服务效率提升25%",
                zone="服务台",
                priority=3
            ))
        
        # 计算预计优化后的得分
        optimized_overall = min(100, current_overall * (1 + target_improvement))
        
        # 估算投资
        investment_min = len(suggestions) * 15000
        investment_max = investment_min * 2
        
        return OptimizationResult(
            branch_id=branch_id,
            current_layout_score=round(current_overall, 1),
            optimized_layout_score=round(optimized_overall, 1),
            improvement=f"+{(optimized_overall - current_overall):.1f}",
            suggestions=suggestions,
            investment_estimate={
                "min": investment_min,
                "max": investment_max,
                "currency": "CNY",
                "roi_months": 6
            }
        )
