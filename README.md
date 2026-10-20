# Bank Customer Experience Enhancement System
## 基于AI赋能与情绪感知双驱动的银行网点客户体验提升方案

[![GitHub Stars](https://img.shields.io/github/stars/JACKYwyj/bank-customer-experience)](https://github.com/JACKYwyj/bank-customer-experience)
[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## 一、执行摘要

银行网点的智能化建设不仅要提高业务效率，也要解决客户在等待、操作受阻和异常处理过程中困难无法及时发现、帮助难以及时到达、问题难以连续交接的服务痛点。

无解释的等待、反复失败和重复叙述会积累客户不满，增加投诉升级和信任流失风险，进而影响客户满意度、持续使用意愿及网点运营效率。

本方案将排队进度、操作日志和客户主动表达与情绪参考信息结合，把服务提示转化为进度解释、分步引导、服务修复和人工接手，并记录处理结果，用于识别流程堵点和优化服务安排，有效降低客诉处理成本。

**核心价值：**

| 价值维度 | 具体描述 |
|----------|----------|
| **满意度提升** | 减少无解释等待、重复询问、无效操作和重复叙述 |
| **及时响应** | 将提示关联到具体业务步骤、接手岗位和处理状态 |
| **持续改善** | 服务记录支持识别流程堵点，优化引导岗位和网点动线 |
| **分阶段实施** | 可分阶段投入和验证，降低一次性大范围改造的投入压力 |
| **个性化服务** | 在合规前提下完善客户画像，提供定向服务 |
| **降低成本** | 有效前置处置显著降低客户投诉处理成本 |

---

## 二、系统架构

### 2.1 整体架构

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           接入层 (Gateway Layer)                            │
│        Web门户 │ 移动App │ 智能终端 │ 第三方系统集成                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                           网关层 (API Gateway)                              │
│              统一认证 │ 限流熔断 │ 请求路由 │ 日志监控                        │
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
│                           支撑层 (Supporting Services)                       │
│             Kafka消息队列 │ Redis缓存 │ PostgreSQL                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                           隐私计算层 (Privacy Computing)                    │
│                  联邦学习 │ 差分隐私 │ 端侧加密                            │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 服务端口分配

| 服务 | 端口 | 核心功能 |
|------|------|----------|
| emotion-recognition | 8001 | 多模态情绪识别、告警生成 |
| empathy-ai | 8002 | 共情回应、服务修复话术 |
| journey-orchestrator | 8003 | 客户旅程记录、跨渠道事件管理 |
| service-flow | 8004 | 流程调整、服务修复、人工接手 |
| space-optimizer | 8005 | Z-AHP/Z-TOPSIS网点评价 |
| privacy-shield | 8006 | 隐私设置、数据删除请求 |

---

## 三、核心模块

### 3.1 情绪识别 (Emotion Recognition)

**端口：8001**

融合面部表情、语音语调、文本语义三个维度的情绪识别。

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

### 3.2 共情交互 (Empathy AI)

**端口：8002**

基于上下文和模板生成共情回应及服务修复话术。

### 3.3 客户旅程 (Journey Orchestrator)

**端口：8003**

记录跨渠道服务事件，实现线上线下服务接续。

### 3.4 服务流程 (Service Flow)

**端口：8004**

判断是否干预及如何修复，结合告警信息生成流程调整建议。

### 3.5 空间优化 (Space Optimizer)

**端口：8005**

基于Z-AHP与Z-TOPSIS评价体系，为网点空间调整提供辅助判断。

**评价指标：**

- 平均等待时间、平均服务时间、业务成功率
- 满意度评分、情绪积极率、投诉率
- 面积效率、功能布局评分、动线评分

### 3.6 隐私保护 (Privacy Shield)

**端口：8006**

确保客户数据隐私安全，支持联邦学习架构。

---

## 四、应用场景

### 4.1 等候场景

当客户反复询问进度或持续表现焦虑时，系统先一步完成识别，提醒大堂人员核实原因，说明预计办理顺序，检查是否存在资料缺失或业务分流可能。

### 4.2 自助操作场景

系统依据操作日志识别重复返回、同一步骤多次失败和主动求助，对一般困难提供简短步骤说明和人工帮助入口。

### 4.3 异常服务修复

先核实事实、明确可处理事项和办理时限，给出适度的理解与解释，涉及争议或紧急资金需求时直接转交具备相应权限的人员处理。

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

---

## 六、快速开始

### 6.1 安装依赖

```bash
git clone https://github.com/JACKYwyj/bank-customer-experience.git
cd bank-customer-experience
pip install -r requirements.txt
```

### 6.2 启动服务

```bash
# 启动各服务
cd src/emotion_recognition && python service.py &  # 端口 8001
cd src/empathy_ai && python service.py &           # 端口 8002
cd src/journey_orchestrator && python service.py & # 端口 8003
cd src/service_flow && python service.py &         # 端口 8004
cd src/space_optimizer && python service.py &      # 端口 8005
cd src/privacy_shield && python service.py &       # 端口 8006
```

### 6.3 API 调用示例

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

# 网点空间评价
curl -X POST http://localhost:8005/space/evaluate/branch_001 \
  -H "Content-Type: application/json" \
  -d '{"branch_name": "北京朝阳支行", "indicator_data": {...}}'
```

---

## 七、项目结构

```
bank-customer-experience/
├── src/
│   ├── emotion_recognition/     # 情绪识别模块
│   ├── empathy_ai/              # 共情交互模块
│   ├── journey_orchestrator/    # 客户旅程编排
│   ├── service_flow/            # 服务流程引擎
│   ├── space_optimizer/         # 空间优化评价
│   ├── privacy_shield/          # 隐私保护模块
│   └── common/                  # 公共配置
├── tests/
│   └── unit/                    # 单元测试
├── docs/                        # 开发文档
├── docker/                      # Docker配置
├── requirements.txt
└── README.md
```

---

## 八、后续开发计划

| 阶段 | 内容 | 状态 |
|------|------|------|
| 第一阶段 | 设备盘点、接口梳理、离线模型评估 | ✅ 已完成 |
| 第二阶段 | 接入解释、求助与人工派单 | 🔄 进行中 |
| 第三阶段 | 接入真实模型，开展有限现场试用 | 📋 待开发 |
| 第四阶段 | 服务状态、处理结果和客户评价持久化回写 | 📋 待开发 |

---

## 九、参考资料

[1] 中国银行业协会. 《2024年中国银行业服务报告》[EB/OL]. 2025-06-24.

[2] Markovitch D G, et al. Consumer reactions to chatbot versus human service[J]. Journal of Retailing and Consumer Services, 2024.

[3] Guo Y, et al. Exploring the effect of empathic response in AI service recovery[J]. Journal of Retailing and Consumer Services, 2025.

[4] Juquelier A, et al. Empathic chatbots: A double-edged sword[J]. Journal of Business Research, 2025.

---

**项目仓库**：https://github.com/JACKYwyj/bank-customer-experience

**许可证**：MIT License
