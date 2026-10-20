# Bank Customer Experience Enhancement System
## 基于AI赋能与情绪感知双驱动的银行网点客户体验提升方案

[![GitHub Stars](https://img.shields.io/github/stars/JACKYwyj/bank-customer-experience)](https://github.com/JACKYwyj/bank-customer-experience)
[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/Tests-127%20passed-brightgreen)](https://github.com/JACKYwyj/bank-customer-experience/tree/main/tests/unit)
[![Pages](https://img.shields.io/badge/GitHub%20Pages-Live-green)](https://jackywyj.github.io/bank-customer-experience)

---

## 🌐 在线演示

| 链接 | 说明 |
|------|------|
| **🔗 在线演示** | https://jackywyj.github.io/bank-customer-experience/demo/ |
| **🇨🇳 中文版本** | https://jackywyj.github.io/bank-customer-experience/zh/ |
| **🇺🇸 English Version** | https://jackywyj.github.io/bank-customer-experience/en/ |

---

## Language / 语言

| [🇨🇳 中文](./README_zh.md) | [🇺🇸 English](./README_en.md) |

---

## 目录

| 序号 | 章节 | 说明 |
|------|------|------|
| 1 | [项目简介](#1-项目简介) | 执行摘要、核心价值、技术架构 |
| 2 | [核心模块](#2-核心模块) | 6个微服务模块 |
| 3 | [项目结构](#3-项目结构) | 目录结构 |
| 4 | [快速开始](#4-快速开始) | 安装、测试、启动 |
| 5 | [模拟测试](#5-模拟测试) | 6个预设场景 |
| 6 | [部署指南](#6-部署指南) | Docker、Kubernetes |
| 7 | [开发指南](#7-开发指南) | 代码规范 |
| 8 | [开发计划](#8-开发计划) | 四阶段路线图 |
| 9 | [参考资料](#9-参考资料) | 引用文献 |
| 10 | [许可证](#10-许可证) | MIT许可证 |

---

## 1. 项目简介

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
│                           表现层 (Presentation Layer)                          │
│        Web门户 │ 移动App │ 智能终端 │ 第三方系统集成                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                           服务层 (Service Layer)                              │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐      │
│  │   情绪识别   │ │   共情交互   │ │   服务流程   │ │   客户旅程   │      │
│  │    :8001    │ │    :8002    │ │    :8004    │ │    :8003    │      │
│  └──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘      │
│  ┌──────────────┐ ┌──────────────┐                                       │
│  │   空间优化   │ │   隐私保护   │                                       │
│  │    :8005    │ │    :8006    │                                       │
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

## 2. 核心模块

### 2.1 情绪识别 (端口 8001)

**位置**: [src/emotion_recognition/](src/emotion_recognition/)

**功能**: 多模态情绪识别（面部、语音、文本）

**融合权重**（原型初始参数）:

| 模态 | 权重 | 有效阈值 |
|------|------|----------|
| 面部表情 | 0.40 | 置信度 > 0.5 |
| 语音语调 | 0.35 | 置信度 > 0.5 |
| 文本语义 | 0.25 | 置信度 > 0.5 |

**告警规则**:

| 情绪 | 触发条件 | 建议响应 |
|------|----------|----------|
| 焦虑 (anxiety) | 分值 ≥ 0.5 且持续 ≥ 60秒 | 先解释进度并观察 |
| 愤怒 (anger) | 分值 ≥ 0.8 且持续 ≥ 30秒 | 建议人工接手 |
| 受挫 (frustration) | 分值 ≥ 0.6 且持续 ≥ 90秒 | 建议服务修复 |

**文件**: [models.py](src/emotion_recognition/models.py) | [service.py](src/emotion_recognition/service.py)

---

### 2.2 共情交互 (端口 8002)

**位置**: [src/empathy_ai/](src/empathy_ai/)

**功能**: 基于上下文的共情回应和服务修复话术

**文件**: [models.py](src/empathy_ai/models.py) | [service.py](src/empathy_ai/service.py)

---

### 2.3 客户旅程 (端口 8003)

**位置**: [src/journey_orchestrator/](src/journey_orchestrator/)

**功能**: 跨渠道服务事件记录，线上线下服务接续

**文件**: [models.py](src/journey_orchestrator/models.py) | [service.py](src/journey_orchestrator/service.py)

---

### 2.4 服务流程 (端口 8004)

**位置**: [src/service_flow/](src/service_flow/)

**功能**: 干预决策、告警驱动的流程调整、人机协同

**文件**: [models.py](src/service_flow/models.py) | [service.py](src/service_flow/service.py)

---

### 2.5 空间优化 (端口 8005)

**位置**: [src/space_optimizer/](src/space_optimizer/)

**功能**: Z-AHP/Z-TOPSIS评价体系

**文件**: [models.py](src/space_optimizer/models.py) | [service.py](src/space_optimizer/service.py)

---

### 2.6 隐私保护 (端口 8006)

**位置**: [src/privacy_shield/](src/privacy_shield/)

**功能**: 联邦学习隐私保护

**文件**: [models.py](src/privacy_shield/models.py) | [service.py](src/privacy_shield/service.py)

---

## 3. 项目结构

```
bank-customer-experience/
├── src/                              # 源代码
│   ├── emotion_recognition/          # [模块1] 情绪识别
│   ├── empathy_ai/                  # [模块2] 共情交互
│   ├── journey_orchestrator/         # [模块3] 客户旅程
│   ├── service_flow/                # [模块4] 服务流程
│   ├── space_optimizer/             # [模块5] 空间优化
│   ├── privacy_shield/             # [模块6] 隐私保护
│   └── common/                     # 公共配置
├── tests/                            # 测试代码
│   ├── unit/                       # 单元测试 (127个)
│   ├── test_simulation.py           # 模拟测试
│   └── conftest.py                 # pytest配置
├── docs/                             # 开发文档
│   ├── README_en.md                # 英文版
│   ├── README_zh.md               # 中文版
│   ├── demo/                       # 交互演示
│   ├── SYSTEM_DESIGN.md            # 系统设计
│   ├── API.md                     # API文档
│   ├── DEPLOYMENT.md              # 部署文档
│   └── DATABASE.md               # 数据库设计
├── docker/                          # Docker配置
│   ├── Dockerfile.*                # 各服务Dockerfile
│   └── docker-compose.yml
├── requirements.txt                 # Python依赖
├── pytest.ini                      # pytest配置
└── README.md                       # 本文件
```

---

## 4. 快速开始

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
source venv/bin/activate

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
# Docker Compose启动
docker-compose up -d

# 或单独启动各服务
cd src/emotion_recognition && python service.py &  # 端口 8001
cd src/empathy_ai && python service.py &           # 端口 8002
cd src/journey_orchestrator && python service.py & # 端口 8003
cd src/service_flow && python service.py &          # 端口 8004
cd src/space_optimizer && python service.py &       # 端口 8005
cd src/privacy_shield && python service.py &         # 端口 8006
```

---

## 5. 模拟测试

6个预设场景用于测试：

```bash
# 运行所有场景
python tests/test_simulation.py --scenario all

# 运行单个场景
python tests/test_simulation.py --scenario waiting_anxiety
```

| 场景 | 描述 | 预期告警 |
|------|------|----------|
| waiting_anxiety | 等待焦虑 | long_term_anxiety |
| self_service_failure | 自助操作失败 | negative_emotion_escalation |
| complaint_escalation | 投诉升级 | conflict_risk |
| normal_service | 正常服务 | 无 |
| elderly_service | 老年客户服务 | long_term_anxiety |
| vip_urgent | VIP紧急业务 | conflict_risk |

**测试结果**: 127个单元测试 + 6个模拟场景 ✅

---

## 6. 部署指南

### Docker Compose

```bash
docker-compose up -d
```

### Kubernetes

```bash
kubectl apply -f k8s/ -n bank-customer-experience
```

---

## 7. 开发指南

### 技术栈

| 类别 | 技术 |
|------|------|
| 语言 | Python 3.11+ |
| 框架 | FastAPI, PyTorch, Transformers |
| 数据库 | PostgreSQL, Redis |
| 消息队列 | Apache Kafka |
| 隐私计算 | PySyft, OpenDP |
| 测试 | pytest, pytest-asyncio, pytest-cov |

---

## 8. 开发计划

| 阶段 | 内容 | 状态 |
|------|------|------|
| 第一阶段 | 设备盘点、接口梳理、离线模型评估 | ✅ 已完成 |
| 第二阶段 | 接入解释、求助与人工派单 | 🔄 进行中 |
| 第三阶段 | 接入真实模型，开展有限现场试用 | 📋 待开发 |
| 第四阶段 | 服务状态、处理结果和客户评价持久化回写 | 📋 待开发 |

---

## 9. 参考资料

[1] 中国银行业协会. 《2024年中国银行业服务报告》. 2025.

[2] Markovitch D G, et al. Consumer reactions to chatbot versus human service. Journal of Retailing and Consumer Services, 2024.

[3] Guo Y, et al. Exploring the effect of empathic response in AI service recovery. Journal of Retailing and Consumer Services, 2025.

[4] Juquelier A, et al. Empathic chatbots: A double-edged sword. Journal of Business Research, 2025.

---

## 10. 许可证

MIT License

---

## 联系方式

- **邮箱**: [1230009401@student.must.edu.mo](mailto:1230009401@student.must.edu.mo)
- **仓库**: https://github.com/JACKYwyj/bank-customer-experience
- **在线演示**: https://jackywyj.github.io/bank-customer-experience/demo/
