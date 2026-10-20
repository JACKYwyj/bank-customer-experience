# Bank Customer Experience Enhancement System
## 基于AI赋能与情绪感知双驱动的银行网点客户体验提升方案

[![GitHub Stars](https://img.shields.io/github/stars/JACKYwyj/bank-customer-experience)](https://github.com/JACKYwyj/bank-customer-experience)
[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/Tests-127%20passed-brightgreen)](tests/unit/)

---

## 一、项目简介

### 1.1 执行摘要

银行网点的智能化建设不仅要提高业务效率，也要解决客户在等待、操作受阻和异常处理过程中困难无法及时发现、帮助难以及时到达、问题难以连续交接的服务痛点。

本方案将排队进度、操作日志和客户主动表达与情绪参考信息结合，把服务提示转化为进度解释、分步引导、服务修复和人工接手，有效降低客诉处理成本。

### 1.2 核心价值

| 价值维度 | 具体描述 |
|----------|----------|
| 满意度提升 | 减少无解释等待、重复询问、无效操作和重复叙述 |
| 及时响应 | 将提示关联到具体业务步骤、接手岗位和处理状态 |
| 持续改善 | 服务记录支持识别流程堵点，优化引导岗位和网点动线 |
| 分阶段实施 | 可分阶段投入和验证，降低一次性大范围改造的投入压力 |
| 个性化服务 | 在合规前提下完善客户画像，提供定向服务 |
| 降低成本 | 有效前置处置显著降低客户投诉处理成本 |

### 1.3 技术架构

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           接入层 (Gateway Layer)                            │
│        Web门户 │ 移动App │ 智能终端 │ 第三方系统集成                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                           服务层 (Business Services)                         │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐      │
│  │   情绪识别   │ │   共情交互   │ │   服务流程   │ │   客户旅程   │      │
│  │  (8001)     │ │   (8002)     │ │   (8004)     │ │   (8003)     │      │
│  └──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘      │
│  ┌──────────────┐ ┌──────────────┐                                       │
│  │   空间优化   │ │   隐私保护   │                                       │
│  │  (8005)     │ │   (8006)     │                                       │
│  └──────────────┘ └──────────────┘                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                           数据层 (Data Layer)                               │
│             PostgreSQL │ Redis缓存 │ Kafka消息队列                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                           隐私计算层 (Privacy Computing)                    │
│                  联邦学习 │ 差分隐私 │ 端侧加密                            │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 二、核心模块

### 2.1 情绪识别 (Emotion Recognition) - 端口 8001

**功能**：融合面部表情、语音语调、文本语义三个维度的情绪识别。

**多模态融合权重（原型初始参数）：**

| 模态 | 权重 | 有效阈值 |
|------|------|----------|
| 面部表情 | 0.40 | 置信度 > 0.5 |
| 语音语调 | 0.35 | 置信度 > 0.5 |
| 文本语义 | 0.25 | 置信度 > 0.5 |

**告警规则：**

| 情绪 | 触发条件 | 建议响应 |
|------|----------|----------|
| 焦虑 (anxiety) | 分值 ≥ 0.5 且持续 ≥ 60秒 | 先解释进度并观察 |
| 愤怒 (anger) | 分值 ≥ 0.8 且持续 ≥ 30秒 | 建议人工接手 |
| 受挫 (frustration) | 分值 ≥ 0.6 且持续 ≥ 90秒 | 建议服务修复 |

### 2.2 共情交互 (Empathy AI) - 端口 8002

**功能**：基于上下文和模板生成共情回应及服务修复话术。

### 2.3 客户旅程 (Journey Orchestrator) - 端口 8003

**功能**：记录跨渠道服务事件，实现线上线下服务接续。

### 2.4 服务流程 (Service Flow) - 端口 8004

**功能**：判断是否干预及如何修复，结合告警信息生成流程调整建议。

### 2.5 空间优化 (Space Optimizer) - 端口 8005

**功能**：基于Z-AHP与Z-TOPSIS评价体系，为网点空间调整提供辅助判断。

**评价指标：**

| 指标类型 | 指标名称 | 优化方向 |
|----------|----------|----------|
| 等待数据 | 平均等待时间、平均服务时间 | 越低越好 |
| 业务数据 | 业务成功率、满意度评分、情绪积极率、投诉率 | 成功率/满意度越高越好 |
| 空间数据 | 面积效率、功能布局评分、动线评分 | 越高越好 |

### 2.6 隐私保护 (Privacy Shield) - 端口 8006

**功能**：确保客户数据隐私安全，支持联邦学习架构。

---

## 三、项目结构

```
bank-customer-experience/
├── src/                              # 源代码
│   ├── emotion_recognition/          # 情绪识别模块
│   │   ├── models.py                # 数据模型、融合规则、端侧模型配置
│   │   └── service.py               # FastAPI服务接口
│   ├── empathy_ai/                  # 共情交互模块
│   │   ├── models.py                # 共情策略、话术模板
│   │   └── service.py               # FastAPI服务接口
│   ├── journey_orchestrator/        # 客户旅程编排
│   │   ├── models.py                # 事件模型、客户视图
│   │   └── service.py               # FastAPI服务接口
│   ├── service_flow/                # 服务流程引擎
│   │   ├── models.py                # 流程定义、告警规则、人机协同
│   │   └── service.py               # FastAPI服务接口
│   ├── space_optimizer/             # 空间优化评价
│   │   ├── models.py                # Z-AHP/Z-TOPSIS算法
│   │   └── service.py               # FastAPI服务接口
│   ├── privacy_shield/              # 隐私保护模块
│   │   ├── models.py                # 隐私配置、联邦学习
│   │   └── service.py               # FastAPI服务接口
│   └── common/                      # 公共配置
│       └── config.py
├── tests/                           # 测试代码
│   ├── unit/                        # 单元测试 (127 tests)
│   ├── test_simulation.py           # 模拟测试（6个场景）
│   └── conftest.py                  # pytest配置
├── docs/                            # 开发文档
│   ├── SYSTEM_DESIGN.md             # 系统设计文档
│   ├── API.md                       # API接口文档
│   ├── DEPLOYMENT.md                # 部署文档
│   ├── DATABASE.md                  # 数据库设计
│   └── EMOTION_RECOGNITION_ARCHITECTURE.md
├── docker/                          # Docker配置
│   ├── Dockerfile.emotion-recognition
│   ├── Dockerfile.empathy-ai
│   ├── Dockerfile.journey-orchestrator
│   ├── Dockerfile.privacy-shield
│   ├── Dockerfile.service-flow
│   ├── Dockerfile.space-optimizer
│   └── docker-compose.yml
├── scripts/                         # 辅助脚本
├── configs/                         # 配置文件
├── requirements.txt                 # Python依赖
├── pytest.ini                       # pytest配置
├── setup.py                         # 安装脚本
├── CHANGELOG.md                     # 变更日志
├── LICENSE                          # MIT许可证
└── README.md                        # 项目文档
```

---

## 四、快速开始

### 4.1 环境要求

- Python 3.11+
- PostgreSQL 14+ (可选)
- Redis 7+ (可选)
- Kafka 3.5+ (可选)

### 4.2 安装

```bash
# 克隆项目
git clone https://github.com/JACKYwyj/bank-customer-experience.git
cd bank-customer-experience

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # Linux/Mac

# 安装依赖
pip install -r requirements.txt
```

### 4.3 运行测试

```bash
# 运行所有单元测试
pytest tests/unit/ -v

# 运行模拟测试
python tests/test_simulation.py --scenario all

# 生成覆盖率报告
pytest tests/unit/ --cov=src --cov-report=html
```

### 4.4 启动服务

```bash
# 启动所有服务（使用Docker）
docker-compose up -d

# 或单独启动各服务
cd src/emotion_recognition && python service.py &  # 端口 8001
cd src/empathy_ai && python service.py &           # 端口 8002
cd src/journey_orchestrator && python service.py & # 端口 8003
cd src/service_flow && python service.py &         # 端口 8004
cd src/space_optimizer && python service.py &      # 端口 8005
cd src/privacy_shield && python service.py &       # 端口 8006
```

### 4.5 API 调用示例

```bash
# 创建情绪识别会话
curl -X POST http://localhost:8001/emotion/sessions \
  -H "Content-Type: application/json" \
  -d '{"user_id": "user_001", "session_type": "branch_service"}'

# 情绪识别
curl -X POST http://localhost:8001/emotion/recognize \
  -H "Content-Type: application/json" \
  -d '{"session_id": "xxx", "text": "等太久了！"}'

# 共情交互
curl -X POST http://localhost:8002/empathy/chat \
  -H "Content-Type: application/json" \
  -d '{"user_id": "user_001", "message": "我要投诉！", "current_emotion": "angry"}'

# 服务流程调整
curl -X POST http://localhost:8004/flow/adjust \
  -H "Content-Type: application/json" \
  -d '{"instance_id": "xxx", "emotion": {"emotion": "anxiety", "intensity": 0.7}}'

# 网点空间评价
curl -X POST http://localhost:8005/space/evaluate/branch_001 \
  -H "Content-Type: application/json" \
  -d '{"branch_name": "北京朝阳支行", "indicator_data": {...}}'
```

---

## 五、技术栈

| 类别 | 技术选型 |
|------|----------|
| **语言** | Python 3.11+ |
| **框架** | FastAPI, PyTorch, Transformers |
| **数据库** | PostgreSQL, Redis |
| **消息队列** | Apache Kafka |
| **隐私计算** | PySyft (联邦学习), OpenDP (差分隐私) |
| **容器化** | Docker |
| **测试** | pytest, pytest-asyncio, pytest-cov |

---

## 六、模拟测试

项目包含完整的模拟测试功能，支持6种预设场景：

```bash
# 运行所有场景
python tests/test_simulation.py --scenario all

# 运行单个场景
python tests/test_simulation.py --scenario waiting_anxiety

# 导出测试结果
python tests/test_simulation.py --scenario all --export results.json
```

**预设场景：**

| 场景 | 描述 |
|------|------|
| waiting_anxiety | 等待焦虑场景 |
| self_service_failure | 自助操作失败场景 |
| complaint_escalation | 投诉升级场景 |
| normal_service | 正常服务场景 |
| elderly_service | 老年客户服务场景 |
| vip_urgent | VIP紧急业务场景 |

---

## 七、部署方式

### 7.1 Docker Compose

```bash
# 构建并启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f emotion-recognition
```

### 7.2 Kubernetes

```bash
# 创建命名空间
kubectl create namespace bank-customer-experience

# 部署服务
kubectl apply -f k8s/ -n bank-customer-experience
```

详见 [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)

---

## 八、开发指南

### 8.1 添加新模块

1. 在 `src/` 下创建模块目录
2. 实现 `models.py` 和 `service.py`
3. 添加单元测试到 `tests/unit/`
4. 更新 `docker-compose.yml`

### 8.2 代码规范

```bash
# 格式化代码
black src/ tests/

# 导入排序
isort src/ tests/

# 类型检查
mypy src/

# 代码检查
flake8 src/ tests/
```

### 8.3 提交规范

```
feat: 新功能
fix: 修复bug
docs: 文档更新
test: 测试相关
refactor: 重构
```

---

## 九、后续开发计划

| 阶段 | 内容 | 状态 |
|------|------|------|
| 第一阶段 | 设备盘点、接口梳理、离线模型评估 | ✅ 已完成 |
| 第二阶段 | 接入解释、求助与人工派单 | 🔄 进行中 |
| 第三阶段 | 接入真实模型，开展有限现场试用 | 📋 待开发 |
| 第四阶段 | 服务状态、处理结果和客户评价持久化回写 | 📋 待开发 |

---

## 十、参考资料

[1] 中国银行业协会. 《2024年中国银行业服务报告》[EB/OL]. 2025-06-24.

[2] Markovitch D G, et al. Consumer reactions to chatbot versus human service[J]. Journal of Retailing and Consumer Services, 2024.

[3] Guo Y, et al. Exploring the effect of empathic response in AI service recovery[J]. Journal of Retailing and Consumer Services, 2025.

[4] Juquelier A, et al. Empathic chatbots: A double-edged sword[J]. Journal of Business Research, 2025.

---

## 许可证

MIT License - 详见 [LICENSE](LICENSE)

---

**项目仓库**：https://github.com/JACKYwyj/bank-customer-experience
