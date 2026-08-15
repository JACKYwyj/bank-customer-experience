"""
space-optimizer 模块单元测试
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from src.space_optimizer.models import (
    FuzzyNumber,
    FuzzyComparisonMatrix,
    ZAHPCalculator,
    ZTOPSISOptimizer,
    BranchSpaceEvaluator,
    EvaluationIndicator,
    ZoneType
)


class TestFuzzyNumber:
    """测试模糊数"""
    
    def test_fuzzy_number_creation(self):
        fn = FuzzyNumber(0.5, 1.0, 1.5)
        assert fn.l == 0.5
        assert fn.m == 1.0
        assert fn.u == 1.5
    
    def test_fuzzy_number_addition(self):
        fn1 = FuzzyNumber(0.5, 1.0, 1.5)
        fn2 = FuzzyNumber(1.0, 2.0, 3.0)
        result = fn1 + fn2
        assert result.l == 1.5
        assert result.m == 3.0
        assert result.u == 4.5
    
    def test_fuzzy_number_multiplication(self):
        fn1 = FuzzyNumber(0.5, 1.0, 1.5)
        fn2 = FuzzyNumber(1.0, 2.0, 3.0)
        result = fn1 * fn2
        assert result.l == 0.5
        assert result.m == 2.0
        assert result.u == 4.5
    
    def test_fuzzy_number_defuzzify(self):
        fn = FuzzyNumber(0.6, 1.0, 1.4)
        result = fn.defuzzify()
        assert result == pytest.approx(1.0)
    
    def test_from_value(self):
        fn = FuzzyNumber.from_value(0.8, 0.1)
        assert fn.m == 0.8
        assert fn.l < fn.m
        assert fn.u > fn.m


class TestZAHPCalculator:
    """测试Z-AHP计算器"""
    
    def test_calculate_criterion_weights(self):
        calc = ZAHPCalculator()
        
        comparisons = {
            ("service", "experience"): 2,
            ("service", "utilization"): 3,
            ("experience", "utilization"): 2
        }
        
        weights = calc.calculate_criterion_weights(comparisons)
        
        assert len(weights) == 3
        assert abs(sum(weights.values()) - 1.0) < 0.01  # 权重和为1
        for w in weights.values():
            assert 0 <= w <= 1
    
    def test_default_weights(self):
        calc = ZAHPCalculator()
        # 测试默认准则权重
        default_weights = {
            "service_efficiency": 0.35,
            "customer_experience": 0.40,
            "space_utilization": 0.25
        }
        assert abs(sum(default_weights.values()) - 1.0) < 0.01


class TestZTOPSISOptimizer:
    """测试Z-TOPSIS优化器"""
    
    def test_build_fuzzy_decision_matrix(self):
        optimizer = ZTOPSISOptimizer()
        
        alternatives = ["branch_a", "branch_b"]
        criteria = ["wait_time", "satisfaction"]
        values = {
            ("branch_a", "wait_time"): 0.3,
            ("branch_a", "satisfaction"): 0.8,
            ("branch_b", "wait_time"): 0.5,
            ("branch_b", "satisfaction"): 0.7
        }
        
        matrix = optimizer.build_fuzzy_decision_matrix(alternatives, criteria, values)
        
        assert len(matrix) == 2
        assert len(matrix[0]) == 2
        assert isinstance(matrix[0][0], FuzzyNumber)
    
    def test_calculate_topsis_scores(self):
        optimizer = ZTOPSISOptimizer()
        
        alternatives = ["branch_a", "branch_b", "branch_c"]
        criteria = ["efficiency", "satisfaction", "utilization"]
        values = {
            ("branch_a", "efficiency"): 0.8,
            ("branch_a", "satisfaction"): 0.7,
            ("branch_a", "utilization"): 0.6,
            ("branch_b", "efficiency"): 0.7,
            ("branch_b", "satisfaction"): 0.8,
            ("branch_b", "utilization"): 0.7,
            ("branch_c", "efficiency"): 0.6,
            ("branch_c", "satisfaction"): 0.6,
            ("branch_c", "utilization"): 0.8
        }
        
        weights = {"efficiency": 0.4, "satisfaction": 0.4, "utilization": 0.2}
        criteria_types = {c: True for c in criteria}
        
        results = optimizer.calculate_topsis_scores(
            alternatives, criteria, values, weights, criteria_types
        )
        
        assert len(results) == 3
        for alt, (score, rank) in results.items():
            assert 0 <= score <= 1
            assert 1 <= rank <= 3


class TestBranchSpaceEvaluator:
    """测试网点空间评估器"""
    
    def test_evaluate_branch(self):
        evaluator = BranchSpaceEvaluator()
        
        indicator_data = {
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
        
        all_scores = [75, 80, 85, 82, 78]
        
        result = evaluator.evaluate_branch(
            branch_id="branch_001",
            branch_name="北京朝阳支行",
            indicator_data=indicator_data,
            all_branch_scores=all_scores
        )
        
        assert result.branch_id == "branch_001"
        assert result.branch_name == "北京朝阳支行"
        assert 0 <= result.overall_score <= 100
        assert result.rank >= 1
    
    def test_generate_recommendations(self):
        evaluator = BranchSpaceEvaluator()
        
        scores = {
            "service_efficiency": {
                "score": 65,
                "metrics": {"avg_wait_time": 20, "success_rate": 0.9}
            },
            "customer_experience": {
                "score": 72,
                "metrics": {"emotion_positive_rate": 0.7, "complaint_rate": 0.04}
            },
            "space_utilization": {
                "score": 68,
                "metrics": {"area_efficiency": 0.6, "flow_line_score": 0.65}
            }
        }
        
        recommendations = evaluator._generate_recommendations(scores)
        
        assert len(recommendations) > 0
        for rec in recommendations:
            assert "area" in rec
            assert "issue" in rec
            assert "suggestion" in rec
    
    def test_optimize_layout(self):
        evaluator = BranchSpaceEvaluator()
        
        # Pass criterion-level scores (not sub-indicator scores)
        current_scores = {
            "service_efficiency": 0.65,
            "customer_experience": 0.72,
            "space_utilization": 0.60  # Low score triggers optimization suggestions
        }
        
        result = evaluator.optimize_layout(
            branch_id="branch_001",
            current_scores=current_scores,
            target_improvement=0.15
        )
        
        assert result.branch_id == "branch_001"
        assert result.current_layout_score > 0
        assert result.optimized_layout_score > result.current_layout_score
        assert len(result.suggestions) > 0
        assert "min" in result.investment_estimate
        assert "max" in result.investment_estimate


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
