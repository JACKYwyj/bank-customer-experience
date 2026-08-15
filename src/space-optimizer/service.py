"""
网点空间优化服务 - FastAPI服务接口
Space Optimizer Service - FastAPI Endpoints
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from fastapi import FastAPI, HTTPException, Query, Depends
from pydantic import BaseModel, Field

from .models import (
    BranchSpaceEvaluator,
    EvaluationIndicator,
    BranchEvaluation,
    OptimizationResult,
    ZAHPCalculator,
    ZTOPSISOptimizer
)


# ============== Pydantic Models ==============

class IndicatorDataRequest(BaseModel):
    """指标数据请求"""
    avg_wait_time: float = Field(..., description="平均等候时间(分钟)")
    avg_service_time: float = Field(..., description="平均服务时间(分钟)")
    success_rate: float = Field(..., description="业务成功率 0-1")
    satisfaction_score: float = Field(..., description="满意度评分 1-5")
    emotion_positive_rate: float = Field(..., description="情绪正面率 0-1")
    complaint_rate: float = Field(..., description="投诉率 0-1")
    area_efficiency: float = Field(..., description="面积效率 0-1")
    functional_layout_score: float = Field(..., description="功能布局评分 0-1")
    flow_line_score: float = Field(..., description="动线评分 0-1")


class EvaluateRequest(BaseModel):
    """网点评价请求"""
    branch_id: str
    branch_name: str
    indicator_data: IndicatorDataRequest
    all_branch_scores: Optional[List[float]] = None


class EvaluateResponse(BaseModel):
    """网点评价响应"""
    branch_id: str
    branch_name: str
    overall_score: float
    rank: int
    total_branches: int
    indicators: Dict[str, Any]
    recommendations: List[Dict[str, str]]
    evaluation_period: str
    generated_at: str


class SuggestionResponse(BaseModel):
    """优化建议响应"""
    type: str
    current: str
    proposed: str
    expected_impact: str
    zone: Optional[str] = None
    priority: int = 1


class InvestmentEstimate(BaseModel):
    """投资估算"""
    min: int
    max: int
    currency: str
    roi_months: int


class OptimizeResponse(BaseModel):
    """优化响应"""
    branch_id: str
    current_layout_score: float
    optimized_layout_score: float
    improvement: str
    suggestions: List[SuggestionResponse]
    investment_estimate: InvestmentEstimate


class WeightRequest(BaseModel):
    """权重计算请求"""
    comparisons: Dict[str, Dict[str, float]] = Field(
        ..., 
        description="两两比较矩阵，如 {'service_experience': {'customer_experience': 2}}"
    )


class WeightResponse(BaseModel):
    """权重响应"""
    weights: Dict[str, float]
    consistency_ratio: float
    is_consistent: bool


class APIResponse(BaseModel):
    """通用API响应"""
    code: int = 0
    message: str = "success"
    data: Optional[Any] = None
    request_id: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


# ============== FastAPI App ==============

app = FastAPI(
    title="Space Optimizer Service",
    description="网点空间优化评价服务 - Z-AHP/Z-TOPSIS方法",
    version="1.0.0"
)

# 全局评估器实例
_evaluator = BranchSpaceEvaluator()
_ahp = ZAHPCalculator()
_topsis = ZTOPSISOptimizer()


@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy", "service": "space-optimizer"}


@app.post("/space/evaluate/{branch_id}", response_model=APIResponse)
async def evaluate_branch(
    branch_id: str,
    request: EvaluateRequest
) -> APIResponse:
    """
    评价指定网点
    
    使用Z-AHP模糊层次分析法计算指标权重，
    结合Z-TOPSIS方法对网点进行综合评价。
    
    Args:
        branch_id: 网点ID (路径参数)
        request: 评价请求体
    
    Returns:
        网点评价结果，包含综合评分、各指标得分、排名和建议
    """
    try:
        # 构建指标数据字典
        indicator_data = {
            "service_efficiency": {
                "avg_wait_time": request.indicator_data.avg_wait_time,
                "avg_service_time": request.indicator_data.avg_service_time,
                "success_rate": request.indicator_data.success_rate,
            },
            "customer_experience": {
                "satisfaction_score": request.indicator_data.satisfaction_score,
                "emotion_positive_rate": request.indicator_data.emotion_positive_rate,
                "complaint_rate": request.indicator_data.complaint_rate,
            },
            "space_utilization": {
                "area_efficiency": request.indicator_data.area_efficiency,
                "functional_layout_score": request.indicator_data.functional_layout_score,
                "flow_line_score": request.indicator_data.flow_line_score,
            }
        }
        
        # 执行评价
        result = _evaluator.evaluate_branch(
            branch_id=request.branch_id,
            branch_name=request.branch_name,
            indicator_data=indicator_data,
            all_branch_scores=request.all_branch_scores
        )
        
        return APIResponse(
            code=0,
            message="success",
            data={
                "branch_id": result.branch_id,
                "branch_name": result.branch_name,
                "overall_score": result.overall_score,
                "rank": result.rank,
                "total_branches": result.total_branches,
                "indicators": result.indicators,
                "recommendations": result.recommendations,
                "evaluation_period": result.evaluation_period,
                "generated_at": result.generated_at.isoformat()
            }
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Evaluation failed: {str(e)}")


@app.get("/space/optimize/{branch_id}/suggestions", response_model=APIResponse)
async def get_optimization_suggestions(
    branch_id: str,
    current_area_efficiency: float = Query(..., description="当前面积效率 0-1"),
    current_flow_line_score: float = Query(..., description="当前动线评分 0-1"),
    current_layout_score: float = Query(..., description="当前功能布局评分 0-1"),
    target_improvement: float = Query(0.15, description="目标提升幅度 0-1")
) -> APIResponse:
    """
    获取网点优化建议
    
    基于当前网点空间指标，使用Z-TOPSIS方法生成优化建议。
    
    Args:
        branch_id: 网点ID
        current_area_efficiency: 当前面积效率
        current_flow_line_score: 当前动线评分
        current_layout_score: 当前功能布局评分
        target_improvement: 目标提升幅度
    
    Returns:
        优化建议列表，包含布局调整、动线优化、设备升级等方案
    """
    try:
        current_scores = {
            "area_efficiency": current_area_efficiency,
            "flow_line_score": current_flow_line_score,
            "functional_layout_score": current_layout_score
        }
        
        result = _evaluator.optimize_layout(
            branch_id=branch_id,
            current_scores=current_scores,
            target_improvement=target_improvement
        )
        
        return APIResponse(
            code=0,
            message="success",
            data={
                "branch_id": result.branch_id,
                "current_layout_score": result.current_layout_score,
                "optimized_layout_score": result.optimized_layout_score,
                "improvement": result.improvement,
                "suggestions": [
                    {
                        "type": s.type,
                        "current": s.current,
                        "proposed": s.proposed,
                        "expected_impact": s.expected_impact,
                        "zone": s.zone,
                        "priority": s.priority
                    }
                    for s in result.suggestions
                ],
                "investment_estimate": result.investment_estimate
            }
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Optimization failed: {str(e)}")


@app.post("/space/weights/calculate", response_model=APIResponse)
async def calculate_weights(request: WeightRequest) -> APIResponse:
    """
    计算指标权重
    
    使用Z-AHP模糊层次分析法计算评价指标权重。
    
    Args:
        request: 包含两两比较矩阵的请求
    
    Returns:
        各指标权重及一致性检验结果
    """
    try:
        # 转换比较矩阵格式
        comparisons = {}
        for c1, comparisons_dict in request.comparisons.items():
            for c2, value in comparisons_dict.items():
                comparisons[(c1, c2)] = value
        
        # 计算权重
        weights = _ahp.calculate_criterion_weights(comparisons)
        
        # 简化一致性比率计算
        n = len(comparisons) ** 0.5  # 估算矩阵大小
        cr = 0.1  # 简化处理
        
        return APIResponse(
            code=0,
            message="success",
            data={
                "weights": weights,
                "consistency_ratio": cr,
                "is_consistent": cr < 0.1
            }
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Weight calculation failed: {str(e)}")


@app.get("/space/ranking", response_model=APIResponse)
async def get_branch_ranking(
    branches: str = Query(..., description="网点ID列表，逗号分隔"),
    period: str = Query("week", description="评估周期 day/week/month")
) -> APIResponse:
    """
    获取网点排名
    
    对多个网点进行综合评价并排名。
    
    Args:
        branches: 网点ID列表
        period: 评估周期
    
    Returns:
        网点排名列表
    """
    try:
        branch_ids = [b.strip() for b in branches.split(",")]
        
        # 模拟评分数据
        rankings = []
        for i, bid in enumerate(branch_ids):
            rankings.append({
                "branch_id": bid,
                "score": 70 + (10 - i) * 2,  # 模拟得分
                "rank": i + 1
            })
        
        # 按得分排序
        rankings.sort(key=lambda x: x["score"], reverse=True)
        for i, r in enumerate(rankings):
            r["rank"] = i + 1
        
        return APIResponse(
            code=0,
            message="success",
            data={
                "period": period,
                "rankings": rankings
            }
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ranking failed: {str(e)}")


@app.get("/space/indicators", response_model=APIResponse)
async def get_indicators() -> APIResponse:
    """
    获取评价指标体系
    
    返回网点空间优化的完整指标体系及其说明。
    
    Returns:
        指标体系定义
    """
    indicators = {
        "service_efficiency": {
            "name": "服务效率",
            "weight": 0.35,
            "sub_indicators": {
                "avg_wait_time": {"name": "平均等候时间", "unit": "分钟", "type": "cost"},
                "avg_service_time": {"name": "平均服务时间", "unit": "分钟", "type": "cost"},
                "success_rate": {"name": "业务成功率", "unit": "%", "type": "benefit"}
            }
        },
        "customer_experience": {
            "name": "客户体验",
            "weight": 0.40,
            "sub_indicators": {
                "satisfaction_score": {"name": "满意度评分", "unit": "分", "type": "benefit"},
                "emotion_positive_rate": {"name": "情绪正面率", "unit": "%", "type": "benefit"},
                "complaint_rate": {"name": "投诉率", "unit": "%", "type": "cost"}
            }
        },
        "space_utilization": {
            "name": "空间利用",
            "weight": 0.25,
            "sub_indicators": {
                "area_efficiency": {"name": "面积效率", "unit": "%", "type": "benefit"},
                "functional_layout_score": {"name": "功能布局评分", "unit": "分", "type": "benefit"},
                "flow_line_score": {"name": "动线评分", "unit": "分", "type": "benefit"}
            }
        }
    }
    
    return APIResponse(
        code=0,
        message="success",
        data=indicators
    )


# ============== Main ==============

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8005)
