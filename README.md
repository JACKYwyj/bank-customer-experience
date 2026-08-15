# Bank Customer Experience Enhancement System
## 基于AI赋能与情绪感知双驱动的银行网点客户体验提升系统

### 项目概述

本项目基于AI赋能与情绪感知双驱动的银行网点客户体验提升实策研究实现，构建集多模态情绪识别、AI驱动的服务流程、人机协同、隐私安全于一体的智慧银行网点系统。

### 核心特性

- 🎭 **多模态情绪识别**：融合面部表情、语音语调、文本语义多维度情绪分析
- 🤝 **人工同理心增强**：AI承担标准化任务，释放人工聚焦高价值服务
- 🔒 **emoAIsec隐私安全**：联邦学习 + 差分隐私保护敏感数据
- 🌐 **全渠道客户旅程**：打通线上线下数据，实现无缝服务体验
- 🏢 **智能网点空间优化**：Z-AHP/Z-TOPSIS评价体系优化功能分区

### 系统架构图

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           表现层 (Presentation)                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐ │
│  │  Web Portal │  │ Mobile App  │  │ Physical    │  │ Branch Kiosk   │ │
│  │             │  │             │  │ Branch      │  │                │ │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────────┘ │
├─────────────────────────────────────────────────────────────────────────┤
│                           服务层 (Services)                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐ │
│  │  Emotion    │  │  Empathy    │  │  Service    │  │ Journey         │ │
│  │  Recognition│  │  AI         │  │  Flow       │  │ Orchestrator    │ │
│  │  :8001      │  │  :8002      │  │  :8004      │  │ :8003           │ │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────────┘ │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                      │
│  │  Space      │  │  Privacy    │  │  Common     │                      │
│  │  Optimizer  │  │  Shield     │  │  Config     │                      │
│  │  :8005      │  │  :8006      │  │             │                      │
│  └─────────────┘  └─────────────┘  └─────────────┘                      │
├─────────────────────────────────────────────────────────────────────────┤
│                           数据层 (Data)                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐ │
│  │ PostgreSQL  │  │   Redis     │  │   Kafka     │  │ Edge Storage    │ │
│  │             │  │             │  │             │  │                 │ │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────────┘ │
├─────────────────────────────────────────────────────────────────────────┤
│                         隐私计算层 (Privacy Computing)                   │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                      │
│  │  Federated  │  │ Differential│  │   Edge      │                      │
│  │  Learning   │  │  Privacy    │  │  Encryption │                      │
│  └─────────────┘  └─────────────┘  └─────────────┘                      │
└─────────────────────────────────────────────────────────────────────────┘
```

### 服务端口分配

| 服务 | 端口 | 描述 |
|------|------|------|
| emotion-recognition | 8001 | 多模态情绪识别服务 |
| empathy-ai | 8002 | 人工同理心AI服务 |
| journey-orchestrator | 8003 | 客户旅程编排服务 |
| service-flow | 8004 | 服务流程引擎 |
| space-optimizer | 8005 | 网点空间优化服务 |
| privacy-shield | 8006 | 隐私保护服务 |

### 技术栈

- **语言**: Python 3.11+
- **框架**: FastAPI, PyTorch, Transformers
- **数据库**: PostgreSQL, Redis
- **消息队列**: Apache Kafka
- **隐私计算**: PySyft (联邦学习), OpenDP (差分隐私)
- **容器化**: Docker, Kubernetes

### 快速开始

#### 1. 环境要求

- Python 3.11+
- PostgreSQL 14+
- Redis 7+
- Kafka 3.5+

#### 2. 安装依赖

```bash
# 克隆项目
git clone https://github.com/your-org/bank-customer-experience.git
cd bank-customer-experience

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# 或: venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
```

#### 3. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 填写必要的配置
```

主要配置项：
```env
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/bank_customer
REDIS_HOST=localhost
REDIS_PORT=6379
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
JWT_SECRET_KEY=your-secret-key-change-in-production
```

#### 4. 启动服务

**开发环境 (直接运行)**:
```bash
# 启动各个服务
cd src/emotion-recognition && python service.py &
cd src/empathy-ai && python service.py &
cd src/journey-orchestrator && python service.py &
cd src/service-flow && python service.py &
cd src/space-optimizer && python service.py &
cd src/privacy-shield && python service.py &
```

**Docker Compose**:
```bash
docker-compose up -d
```

#### 5. 运行测试

```bash
# 运行所有测试
pytest tests/ -v

# 运行带覆盖率报告的测试
pytest tests/ --cov=src --cov-report=html

# 运行特定模块测试
pytest tests/unit/test_emotion_recognition.py -v
```

### API 使用示例

#### 1. 情绪识别服务 (Port 8001)

```bash
# 创建情绪识别会话
curl -X POST http://localhost:8001/emotion/sessions \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user_001",
    "session_type": "branch_service",
    "branch_id": "branch_beijing_001"
  }'

# 多模态情绪识别
curl -X POST http://localhost:8001/emotion/recognize \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "emo_session_xxx",
    "text": "等太久了，我要投诉！",
    "context": {"wait_time": 25}
  }'

# 获取情绪历史
curl http://localhost:8001/emotion/sessions/{session_id}/history
```

#### 2. 同理心AI服务 (Port 8002)

```bash
# 发送对话消息
curl -X POST http://localhost:8002/empathy/chat \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user_001",
    "message": "我要投诉！等了25分钟还没轮到！",
    "current_emotion": "angry",
    "emotion_intensity": 0.85,
    "wait_time_minutes": 25,
    "customer_tier": "gold"
  }'

# 获取代理信息
curl http://localhost:8002/empathy/agents/agent_001

# 获取服务修复话术
curl -X POST http://localhost:8002/empathy/recovery/scripts \
  -H "Content-Type: application/json" \
  -d '{"emotion": "anxiety", "intensity": 0.7}'
```

#### 3. 客户旅程编排服务 (Port 8003)

```bash
# 记录客户事件
curl -X POST http://localhost:8003/journey/events \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user_001",
    "event_type": "emotion_change",
    "channel": "branch",
    "event_data": {"to_emotion": "anxious", "intensity": 0.6}
  }'

# 获取客户360视图
curl http://localhost:8003/journey/customer/user_001?include_session=true

# 获取个性化推荐
curl http://localhost:8003/journey/recommendations/user_001?max_count=5
```

#### 4. 服务流程引擎 (Port 8004)

```bash
# 获取服务流程列表
curl http://localhost:8004/flow/processes

# 触发服务流程
curl -X POST http://localhost:8004/flow/processes/proc_001/trigger \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user_001",
    "trigger_type": "emotion_alert",
    "trigger_data": {"emotion": "anxiety", "intensity": 0.7}
  }'

# 获取流程实例状态
curl http://localhost:8004/flow/instances/{instance_id}

# 基于情绪调整流程
curl -X POST http://localhost:8004/flow/adjust \
  -H "Content-Type: application/json" \
  -d '{
    "instance_id": "inst_xxx",
    "emotion": {"emotion": "anxiety", "intensity": 0.7, "duration_seconds": 90}
  }'
```

#### 5. 网点空间优化服务 (Port 8005)

```bash
# 评价网点
curl -X POST http://localhost:8005/space/evaluate/branch_001 \
  -H "Content-Type: application/json" \
  -d '{
    "branch_name": "北京朝阳支行",
    "indicator_data": {
      "avg_wait_time": 10,
      "avg_service_time": 8,
      "success_rate": 0.95,
      "satisfaction_score": 4.2,
      "emotion_positive_rate": 0.8,
      "complaint_rate": 0.02,
      "area_efficiency": 0.75,
      "functional_layout_score": 0.8,
      "flow_line_score": 0.7
    }
  }'

# 获取优化建议
curl "http://localhost:8005/space/optimize/branch_001/suggestions?current_area_efficiency=0.6&current_flow_line_score=0.65&current_layout_score=0.7"

# 计算指标权重
curl -X POST http://localhost:8005/space/weights/calculate \
  -H "Content-Type: application/json" \
  -d '{
    "comparisons": {
      "service_experience": {"customer_experience": 2},
      "service_experience": {"space_utilization": 3},
      "customer_experience": {"space_utilization": 2}
    }
  }'
```

#### 6. 隐私保护服务 (Port 8006)

```bash
# 获取隐私设置
curl http://localhost:8006/privacy/settings/user_001

# 更新隐私设置
curl -X PUT http://localhost:8006/privacy/settings/user_001 \
  -H "Content-Type: application/json" \
  -d '{"emotion_data_collection": true, "biometric_storage": false}'

# 申请数据删除
curl -X POST http://localhost:8006/privacy/requests/delete \
  -H "Content-Type: application/json" \
  -d '{"user_id": "user_001", "data_types": ["emotion_data", "behavioral_data"]}'

# 获取隐私仪表板
curl http://localhost:8006/privacy/dashboard/user_001

# 提交联邦学习更新
curl -X POST http://localhost:8006/privacy/federated-learning/submit \
  -H "Content-Type: application/json" \
  -d '{
    "client_id": "branch_001",
    "round": 1,
    "gradient_data": {"w1": 0.1, "w2": 0.2},
    "sample_count": 100
  }'
```

### 目录结构

```
bank-customer-experience/
├── src/                          # 源代码
│   ├── emotion-recognition/      # 情绪识别模块
│   │   ├── models.py             # 数据模型
│   │   ├── service.py            # FastAPI服务
│   │   └── __init__.py
│   ├── empathy-ai/               # 同理心AI模块
│   │   ├── models.py
│   │   ├── service.py
│   │   └── __init__.py
│   ├── privacy-shield/           # 隐私保护模块
│   │   ├── models.py
│   │   ├── service.py
│   │   └── __init__.py
│   ├── journey-orchestrator/     # 旅程编排模块
│   │   ├── models.py
│   │   ├── service.py
│   │   └── __init__.py
│   ├── space-optimizer/          # 空间优化模块
│   │   ├── models.py
│   │   ├── service.py
│   │   └── __init__.py
│   ├── service-flow/             # 服务流程模块
│   │   ├── models.py
│   │   ├── service.py
│   │   └── __init__.py
│   └── common/                   # 公共模块
│       ├── config.py
│       └── __init__.py
├── tests/                        # 测试代码
│   ├── unit/                     # 单元测试
│   ├── integration/              # 集成测试
│   └── conftest.py               # pytest配置
├── docs/                         # 开发文档
├── docker/                       # Docker配置
├── scripts/                      # 辅助脚本
├── configs/                      # 配置文件
├── requirements.txt              # Python依赖
├── pytest.ini                    # pytest配置
├── docker-compose.yml            # Docker Compose配置
└── README.md
```

### 系统模块

| 模块 | 说明 | 核心功能 |
|------|------|----------|
| `emotion-recognition` | 多模态情绪识别引擎 | 面部/语音/文本情绪分析 |
| `empathy-ai` | 人工同理心AI | 智能共情交互、服务安抚 |
| `privacy-shield` | emoAIsec隐私保护 | 联邦学习、差分隐私 |
| `journey-orchestrator` | 客户旅程编排 | 全渠道数据同步、个性化服务 |
| `space-optimizer` | 网点空间优化 | Z-AHP/Z-TOPSIS评价 |
| `service-flow` | 服务流程引擎 | 人机协同、情绪驱动的服务修复 |

### 开发文档

- [系统设计文档](./docs/SYSTEM_DESIGN.md)
- [API接口文档](./docs/API.md)
- [数据库设计文档](./docs/DATABASE.md)
- [部署文档](./docs/DEPLOYMENT.md)
- [模块详细设计](./docs/modules/)

### 测试覆盖

运行测试并生成覆盖率报告：

```bash
# 生成覆盖率报告 (HTML)
pytest tests/ --cov=src --cov-report=html --cov-report=term

# 查看覆盖率报告
open htmlcov/index.html

# 只运行特定测试
pytest tests/unit/test_emotion_recognition.py -v
pytest tests/unit/test_journey_orchestrator.py -v
```

当前测试覆盖模块：
- emotion-recognition
- empathy-ai
- privacy-shield
- space-optimizer
- journey-orchestrator
- service-flow

### 贡献指南

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

### 许可证

MIT License

