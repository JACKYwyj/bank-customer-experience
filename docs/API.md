# API接口文档 (API Documentation)

## 概述

本文档定义银行客户体验提升系统的所有API接口，采用OpenAPI 3.0规范。

**基础URL**: `https://api.bank-customer-experience.com/api/v1`

**认证方式**: Bearer Token (JWT)

---

## 通用说明

### 请求头

```
Authorization: Bearer <access_token>
Content-Type: application/json
X-Request-ID: <uuid>
X-Language: zh-CN
```

### 响应格式

```json
{
  "code": 0,
  "message": "success",
  "data": { ... },
  "request_id": "xxx",
  "timestamp": "2024-01-01T10:00:00Z"
}
```

### 错误码

| 错误码 | 说明 |
|--------|------|
| 0 | 成功 |
| 1001 | 参数错误 |
| 1002 | 认证失败 |
| 1003 | 权限不足 |
| 2001 | 资源不存在 |
| 3001 | 服务内部错误 |
| 4001 | 限流中 |
| 5001 | 系统维护中 |

---

## 1. 情绪识别服务 (Emotion Recognition)

### 1.1 创建情绪识别会话

```
POST /emotion/sessions
```

创建新的情绪识别会话，获取session_id用于后续请求。

**请求体**:

```json
{
  "user_id": "user_12345",
  "channel": "web",           // web | mobile | kiosk | branch
  "device_id": "device_xxx",
  "metadata": {
    "branch_id": "branch_001",
    "window_id": "window_01"
  }
}
```

**响应**:

```json
{
  "code": 0,
  "data": {
    "session_id": "sess_abc123",
    "user_id": "user_12345",
    "created_at": "2024-01-01T10:00:00Z",
    "expires_at": "2024-01-01T11:00:00Z"
  }
}
```

### 1.2 提交多模态数据进行情绪识别

```
POST /emotion/recognize
Content-Type: multipart/form-data
```

**请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| session_id | string | 是 | 会话ID |
| image | file | 否 | 面部图片 (JPEG/PNG, max 5MB) |
| audio | file | 否 | 语音片段 (WAV/MP3, max 10MB, ≤30s) |
| text | string | 否 | 文本内容 (max 1000字符) |

**响应**:

```json
{
  "code": 0,
  "data": {
    "session_id": "sess_abc123",
    "emotion": {
      "primary": "anxiety",
      "primary_confidence": 0.87,
      "secondary": "confusion",
      "secondary_confidence": 0.65,
      "valence": -0.3,
      "arousal": 0.7,
      "multi_modal": {
        "facial": {
          "detected": true,
          "emotion": "anxiety",
          "confidence": 0.92,
          "landmarks": [...],
          "quality_score": 0.88
        },
        "vocal": {
          "detected": true,
          "emotion": "anxiety",
          "confidence": 0.85,
          "pitch_avg": 220,
          "speech_rate": 2.1
        },
        "text": {
          "detected": true,
          "emotion": "confusion",
          "confidence": 0.78,
          "keywords": ["慢", "投诉", "等"]
        }
      },
      "fused_confidence": 0.87
    },
    "alert": {
      "triggered": false,
      "type": null,
      "recommendation": null
    },
    "timestamp": "2024-01-01T10:00:05Z"
  }
}
```

### 1.3 获取情绪追踪历史

```
GET /emotion/sessions/{session_id}/history
```

**路径参数**:

| 参数 | 类型 | 说明 |
|------|------|------|
| session_id | string | 会话ID |

**查询参数**:

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| start_time | datetime | -24h | 开始时间 |
| end_time | datetime | now | 结束时间 |
| limit | int | 100 | 返回数量 |

**响应**:

```json
{
  "code": 0,
  "data": {
    "session_id": "sess_abc123",
    "records": [
      {
        "timestamp": "2024-01-01T10:00:00Z",
        "emotion": "neutral",
        "confidence": 0.75,
        "modalities": ["text"]
      },
      {
        "timestamp": "2024-01-01T10:00:05Z",
        "emotion": "anxiety",
        "confidence": 0.87,
        "modalities": ["facial", "vocal", "text"]
      }
    ],
    "statistics": {
      "emotion_distribution": {
        "neutral": 0.1,
        "anxiety": 0.6,
        "confusion": 0.2,
        "satisfaction": 0.1
      },
      "avg_confidence": 0.82,
      "total_records": 2
    }
  }
}
```

---

## 2. 同理心AI服务 (Empathy AI)

### 2.1 发送对话消息

```
POST /empathy/chat
```

**请求体**:

```json
{
  "session_id": "sess_abc123",
  "user_id": "user_12345",
  "message": "我要投诉，等了20分钟还没轮到！",
  "emotion_context": {
    "current_emotion": "angry",
    "intensity": 0.85,
    "duration_seconds": 120
  },
  "context": {
    "service_type": "account_inquiry",
    "queue_position": 5,
    "wait_time_minutes": 20,
    "business_type": "account",
    "previous_interactions": 3,
    "is_returning_customer": true
  }
}
```

**响应**:

```json
{
  "code": 0,
  "data": {
    "response": {
      "message": "非常抱歉让您久等了，我能理解等待20分钟确实让人焦急。请问我能为您做些什么来弥补这次不好的体验？",
      "empathy_level": "high",
      "empathy_score": 0.92,
      "action_recommendations": [
        {
          "type": "service_compensation",
          "triggered": true,
          "options": ["免排队优先办理", "手续费减免"]
        },
        {
          "type": "emotional_validation",
          "triggered": true,
          "script": "您的感受完全可以理解，长时间等待确实会影响心情。"
        }
      ],
      "escalation": {
        "required": false,
        "reason": null
      }
    },
    "agent": {
      "id": "agent_001",
      "name": "小e",
      "avatar_url": "https://xxx/avatar.png",
      "personality": "warm_professional",
      "voice_url": "https://xxx/voice.wav"
    },
    "next_prompts": [
      "请问您要办理什么业务？",
      "我可以帮您查询账户信息"
    ]
  }
}
```

### 2.2 获取虚拟代理信息

```
GET /empathy/agents/{agent_id}
```

**响应**:

```json
{
  "code": 0,
  "data": {
    "id": "agent_001",
    "name": "小e",
    "personality": "warm_professional",
    "languages": ["zh-CN", "en-US"],
    "specialties": ["account_inquiry", "complaint_handling", "emotional_support"],
    "avatar_url": "https://xxx/avatar.png",
    "voice_config": {
      "voice_id": "female_young_professional",
      "speed": 1.0,
      "pitch": 1.0
    },
    "working_hours": {
      "timezone": "Asia/Shanghai",
      "hours": "09:00-21:00"
    }
  }
}
```

---

## 3. 服务流程引擎 (Service Flow)

### 3.1 获取服务流程列表

```
GET /flow/processes
```

**查询参数**:

| 参数 | 类型 | 说明 |
|------|------|------|
| category | string | 流程类别 (complaint, inquiry, transaction) |
| status | string | 状态 (active, deprecated) |
| page | int | 页码 |
| page_size | int | 每页数量 |

**响应**:

```json
{
  "code": 0,
  "data": {
    "items": [
      {
        "id": "proc_001",
        "name": "客户投诉处理流程",
        "category": "complaint",
        "version": "2.1",
        "status": "active",
        "description": "标准客户投诉处理流程，包含情绪识别和修复机制",
        "stages": ["接收", "评估", "处理", "跟进", "关闭"],
        "avg_duration_minutes": 30,
        "satisfaction_rate": 0.85
      }
    ],
    "total": 15,
    "page": 1,
    "page_size": 10
  }
}
```

### 3.2 触发服务流程

```
POST /flow/processes/{process_id}/trigger
```

**请求体**:

```json
{
  "session_id": "sess_abc123",
  "user_id": "user_12345",
  "trigger_type": "emotion_alert",
  "trigger_data": {
    "emotion": "angry",
    "intensity": 0.9,
    "reason": "长时间等待"
  },
  "initial_context": {
    "branch_id": "branch_001",
    "service_type": "complaint"
  }
}
```

**响应**:

```json
{
  "code": 0,
  "data": {
    "instance_id": "inst_xyz789",
    "process_id": "proc_001",
    "current_stage": "评估",
    "started_at": "2024-01-01T10:00:00Z",
    "recommended_actions": [
      {
        "action": "priority_service",
        "description": "优先处理此客户",
        "priority_boost": 5
      },
      {
        "action": "empathy_response",
        "description": "发送同理心回复",
        "template_id": "empathy_001"
      }
    ]
  }
}
```

### 3.3 获取流程实例状态

```
GET /flow/instances/{instance_id}
```

**响应**:

```json
{
  "code": 0,
  "data": {
    "instance_id": "inst_xyz789",
    "process_id": "proc_001",
    "process_name": "客户投诉处理流程",
    "status": "in_progress",
    "current_stage": "处理",
    "stages": [
      {"name": "接收", "status": "completed", "completed_at": "2024-01-01T10:00:00Z"},
      {"name": "评估", "status": "completed", "completed_at": "2024-01-01T10:00:05Z"},
      {"name": "处理", "status": "in_progress", "started_at": "2024-01-01T10:00:05Z"},
      {"name": "跟进", "status": "pending"},
      {"name": "关闭", "status": "pending"}
    ],
    "context": {
      "emotion_at_entry": "angry",
      "emotion_current": "neutral",
      "emotion_improvement": 0.7,
      "interactions_count": 3
    },
    "started_at": "2024-01-01T10:00:00Z",
    "updated_at": "2024-01-01T10:05:00Z"
  }
}
```

---

## 4. 客户旅程服务 (Journey)

### 4.1 获取客户360视图

```
GET /journey/customer/{user_id}
```

**响应**:

```json
{
  "code": 0,
  "data": {
    "user_id": "user_12345",
    "profile": {
      "name": "张三",
      "tier": "gold",
      "segments": ["high_value", "digital_prefer"],
      "risk_level": "low"
    },
    "current_session": {
      "session_id": "sess_abc123",
      "channel": "branch",
      "location": "北京朝阳支行",
      "arrived_at": "2024-01-01T09:30:00Z",
      "emotion_trend": ["neutral", "anxious", "neutral"]
    },
    "journey_summary": {
      "total_interactions_30d": 12,
      "avg_satisfaction": 4.2,
      "preferred_channel": "mobile",
      "last_contact": "2024-01-01T09:30:00Z"
    },
    "preferences": {
      "language": "zh-CN",
      "accessibility": [],
      "contact_method": "app_push"
    }
  }
}
```

### 4.2 记录客户交互事件

```
POST /journey/events
```

**请求体**:

```json
{
  "user_id": "user_12345",
  "event_type": "emotion_change",
  "event_data": {
    "session_id": "sess_abc123",
    "from_emotion": "anxious",
    "to_emotion": "neutral",
    "trigger": "service_recovery",
    "channel": "branch"
  },
  "timestamp": "2024-01-01T10:05:00Z"
}
```

### 4.3 获取个性化推荐

```
GET /journey/recommendations/{user_id}
```

**响应**:

```json
{
  "code": 0,
  "data": {
    "user_id": "user_12345",
    "recommendations": [
      {
        "type": "service",
        "priority": 1,
        "title": "优先办理窗口",
        "description": "已为您开启VIP优先通道，减少等待时间",
        "action_url": "/redirect/priority-queue"
      },
      {
        "type": "offer",
        "priority": 2,
        "title": "专属理财顾问",
        "description": "您是我们的高净值客户，特提供一对一专属服务",
        "action_url": "/redirect/advisor-booking"
      }
    ],
    "generated_at": "2024-01-01T10:00:00Z"
  }
}
```

---

## 5. 隐私保护服务 (Privacy Shield)

### 5.1 获取隐私设置

```
GET /privacy/settings/{user_id}
```

**响应**:

```json
{
  "code": 0,
  "data": {
    "user_id": "user_12345",
    "settings": {
      "emotion_data_collection": true,
      "biometric_storage": false,
      "data_retention_days": 90,
      "third_party_sharing": false,
      "marketing_use": false
    },
    "rights": {
      "access": true,
      "correction": true,
      "deletion": true,
      "portability": true,
      "objection": true
    },
    "consent_history": [
      {"type": "emotion_data", "granted": true, "date": "2024-01-01"},
      {"type": "marketing", "granted": false, "date": "2024-01-01"}
    ]
  }
}
```

### 5.2 更新隐私设置

```
PUT /privacy/settings/{user_id}
```

**请求体**:

```json
{
  "emotion_data_collection": false,
  "data_retention_days": 30
}
```

### 5.3 申请数据删除

```
POST /privacy/requests/delete
```

**请求体**:

```json
{
  "user_id": "user_12345",
  "request_type": "full_deletion",
  "reason": "个人偏好",
  "confirmation_code": "ABC123"
}
```

**响应**:

```json
{
  "code": 0,
  "data": {
    "request_id": "req_456",
    "status": "processing",
    "estimated_completion": "2024-01-03T10:00:00Z",
    "scope": ["emotion_data", "interaction_history", "preferences"]
  }
}
```

---

## 6. 空间优化服务 (Space Optimizer)

### 6.1 获取网点评价

```
GET /space/evaluate/{branch_id}
```

**查询参数**:

| 参数 | 类型 | 说明 |
|------|------|------|
| period | string | 评估周期 (day, week, month) |
| indicators | string | 指标ID，多个用逗号分隔 |

**响应**:

```json
{
  "code": 0,
  "data": {
    "branch_id": "branch_001",
    "branch_name": "北京朝阳支行",
    "evaluation_period": "2024-01-01 ~ 2024-01-07",
    "overall_score": 85.6,
    "rank": 12,
    "total_branches": 156,
    "indicators": {
      "service_efficiency": {
        "score": 82.3,
        "metrics": {
          "avg_wait_time": 12.5,
          "avg_service_time": 8.2,
          "success_rate": 0.98
        }
      },
      "customer_experience": {
        "score": 88.7,
        "metrics": {
          "satisfaction_score": 4.3,
          "emotion_positive_rate": 0.85,
          "complaint_rate": 0.02
        }
      },
      "space_utilization": {
        "score": 79.5,
        "metrics": {
          "area_efficiency": 0.75,
          "functional_layout_score": 0.82,
          "flow_line_score": 0.78
        }
      }
    },
    "recommendations": [
      {
        "area": "等候区",
        "issue": "等候时间较长",
        "suggestion": "增加智能导览设备，分流客户"
      }
    ],
    "generated_at": "2024-01-08T00:00:00Z"
  }
}
```

### 6.2 获取优化建议

```
GET /space/optimize/{branch_id}/suggestions
```

**响应**:

```json
{
  "code": 0,
  "data": {
    "branch_id": "branch_001",
    "current_layout_score": 72.5,
    "optimized_layout_score": 88.3,
    "improvement": "+15.8",
    "suggestions": [
      {
        "type": "zone_reallocation",
        "current": "等候区: 30㎡, 15座位",
        "proposed": "等候区: 25㎡, 20座位 + AI互动区: 5㎡",
        "expected_impact": "等候满意度提升15%"
      },
      {
        "type": "flow_optimization",
        "current": "单一入口",
        "proposed": "双入口+智能分流",
        "expected_impact": "平均等候时间减少20%"
      }
    ],
    "investment_estimate": {
      "min": 50000,
      "max": 80000,
      "currency": "CNY",
      "roi_months": 6
    }
  }
}
```

---

## 7. 数据分析服务 (Analytics)

### 7.1 获取情绪分析报表

```
GET /analytics/emotion/report
```

**查询参数**:

| 参数 | 类型 | 说明 |
|------|------|------|
| branch_id | string | 网点ID |
| start_date | date | 开始日期 |
| end_date | date | 结束日期 |
| group_by | string | 分组方式 (day, hour, branch) |

**响应**:

```json
{
  "code": 0,
  "data": {
    "report_period": "2024-01-01 ~ 2024-01-07",
    "summary": {
      "total_sessions": 15420,
      "avg_emotion_positive_rate": 0.78,
      "emotion_distribution": {
        "satisfaction": 0.45,
        "neutral": 0.33,
        "anxiety": 0.12,
        "anger": 0.05,
        "confusion": 0.05
      },
      "emotion_trend": [
        {"date": "2024-01-01", "positive_rate": 0.76, "avg_intensity": 0.62},
        {"date": "2024-01-02", "positive_rate": 0.79, "avg_intensity": 0.58}
      ]
    },
    "by_branch": [
      {
        "branch_id": "branch_001",
        "branch_name": "北京朝阳支行",
        "positive_rate": 0.82,
        "rank": 1
      }
    ],
    "insights": [
      {
        "type": "pattern",
        "title": "下午3点情绪波动较大",
        "description": "该时段等候时间较长，客户焦虑情绪上升",
        "confidence": 0.88
      }
    ]
  }
}
```

### 7.2 获取服务满意度分析

```
GET /analytics/satisfaction/report
```

---

## 8. WebSocket实时接口

### 8.1 连接情绪实时推送

```
WS /ws/emotion/{session_id}
```

**连接示例**:

```javascript
const ws = new WebSocket('wss://api.bank-customer-experience.com/ws/emotion/sess_abc123');
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Emotion update:', data);
};
```

**推送消息格式**:

```json
{
  "type": "emotion_update",
  "session_id": "sess_abc123",
  "data": {
    "emotion": "anxiety",
    "intensity": 0.75,
    "timestamp": "2024-01-01T10:00:05Z"
  }
}
```

```json
{
  "type": "alert",
  "session_id": "sess_abc123",
  "data": {
    "alert_type": "negative_emotion_escalation",
    "emotion": "anger",
    "intensity": 0.92,
    "recommendation": "建议立即人工介入"
  }
}
```

---

## 9. 回调接口 (Webhook)

### 9.1 注册回调

```
POST /webhooks
```

**请求体**:

```json
{
  "url": "https://your-server.com/webhook",
  "events": ["emotion.alert", "journey.completed", "privacy.request"],
  "secret": "your_webhook_secret",
  "description": "生产环境回调"
}
```

### 9.2 回调消息格式

```json
{
  "event": "emotion.alert",
  "timestamp": "2024-01-01T10:00:00Z",
  "data": {
    "session_id": "sess_abc123",
    "user_id": "user_12345",
    "alert_type": "negative_emotion_escalation",
    "emotion": "anger",
    "intensity": 0.92
  },
  "signature": "sha256=xxx"
}
```

---

*文档版本：v1.0*
*最后更新：2024-01-15*
