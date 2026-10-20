# Bank Customer Experience Enhancement System
## 基于AI赋能与情绪感知双驱动的银行网点客户体验提升方案

**澳门科技大学**  
**指导老师：马如飞**  
**团队成员：王蕴杰 郑贻铭 高岳涵**

---

[![GitHub Stars](https://img.shields.io/github/stars/JACKYwyj/bank-customer-experience)](https://github.com/JACKYwyj/bank-customer-experience)
[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## 一、执行摘要

银行网点的智能化建设不仅要提高业务效率，也要解决客户在等待、操作受阻和异常处理过程中困难无法及时发现、帮助难以及时到达、问题难以连续交接的服务痛点。

本方案将排队进度、操作日志和客户主动表达与情绪参考信息结合，把服务提示转化为进度解释、分步引导、服务修复和人工接手，并记录处理结果，用于识别流程堵点和优化服务安排。

**项目仓库**：https://github.com/JACKYwyj/bank-customer-experience

---

## 二、项目核心价值

### 六大核心价值

| 序号 | 价值维度 | 具体描述 |
|------|----------|----------|
| 1 | **客户满意度提升** | 减少无解释等待、重复询问、无效操作和重复叙述 |
| 2 | **现场响应优化** | 将提示关联到具体业务步骤、接手岗位和处理状态 |
| 3 | **持续运营改善** | 服务记录支持识别流程堵点，优化引导岗位和网点动线 |
| 4 | **分阶段实施** | 可分阶段投入和验证，降低一次性大范围改造的投入压力 |
| 5 | **个性化服务** | 在合规前提下完善客户画像，提供定向服务 |
| 6 | **降低客诉成本** | 有效前置处置显著降低客户投诉处理成本 |

---

## 三、系统架构

### 3.1 整体架构

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
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐                       │
│  │   空间优化   │ │   隐私保护   │ │   数据分析   │                       │
│  │  (8005)     │ │   (8006)     │ │             │                       │
│  └──────────────┘ └──────────────┘ └──────────────┘                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                           支撑层 (Supporting Services)                       │
│             Kafka消息队列 │ Redis缓存 │ PostgreSQL │ MongoDB                │
├─────────────────────────────────────────────────────────────────────────────┤
│                           隐私计算层 (Privacy Computing)                    │
│                  联邦学习 │ 差分隐私 │ 端侧加密                            │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 3.2 服务端口分配

| 服务 | 端口 | 核心功能 |
|------|------|----------|
| emotion-recognition | 8001 | 多模态情绪识别、告警生成 |
| empathy-ai | 8002 | 共情回应、服务修复话术 |
| journey-orchestrator | 8003 | 客户旅程记录、跨渠道事件管理 |
| service-flow | 8004 | 流程调整、服务修复、人工接手 |
| space-optimizer | 8005 | Z-AHP/Z-TOPSIS网点评价 |
| privacy-shield | 8006 | 隐私设置、数据删除请求 |

---

## 四、情绪识别技术细节

### 4.1 多模态融合权重

根据商业计划书研究设计，当前多模态融合权重如下：

| 模态 | 权重 | 说明 |
|------|------|------|
| 面部表情 | **0.40** | 置信度 > 0.5 时纳入 |
| 语音语调 | **0.35** | 置信度 > 0.5 时纳入 |
| 文本语义 | **0.25** | 基于正负向关键词计数 |

> **注意**：以上权重为原型初始参数，基于研究论文设计。实际网点验证前需通过人工标注、误报与漏报、响应时长、问题解决率和一线人员反馈进行校准。

### 4.2 告警规则

| 情绪标签 | 触发条件 | 建议响应 |
|----------|----------|----------|
| **焦虑 (anxiety)** | 分值 ≥ 0.5 且持续 ≥ 60秒 | 先解释进度并观察，避免过度干预 |
| **愤怒 (anger)** | 分值 ≥ 0.8 且持续 ≥ 30秒 | 建议人工接手或主管协调，快速响应 |
| **受挫 (frustration)** | 分值 ≥ 0.6 且持续 ≥ 90秒 | 建议服务修复与人工协助 |
| **未达条件** | 不满足上述条件 | 继续当前流程，保留人工求助入口 |

> **重要**：识别置信度不等于经过验证的心理强度，应作为业务参考分值，待校准后使用。

### 4.3 情绪识别技术流程

```
┌─────────────────────────────────────────────────────────────────┐
│                      多模态情绪融合处理流程                        │
│                                                                  │
│  ┌─────────┐    ┌─────────┐    ┌─────────┐                     │
│  │ 面部输入 │    │ 语音输入 │    │ 文本输入 │                     │
│  │ (预设:   │    │ (预设:   │    │ 关键词    │                     │
│  │ 焦虑0.85)│    │ 焦虑0.78)│    │ 计数判断)│                     │
│  └────┬────┘    └────┬────┘    └────┬────┘                     │
│       │              │              │                           │
│       └──────────────┼──────────────┘                           │
│                      ▼                                          │
│           ┌─────────────────┐                                   │
│           │ CrossModalFusion│                                   │
│           │ 融合引擎        │                                   │
│           │ (置信度>0.5纳入)│                                   │
│           └────────┬────────┘                                   │
│                    ▼                                           │
│           ┌─────────────────┐                                   │
│           │ 告警判断        │                                   │
│           │ (焦虑/愤怒/受挫)│                                   │
│           └────────┬────────┘                                   │
│                    ▼                                           │
│           ┌─────────────────┐                                   │
│           │ 响应建议生成    │                                   │
│           │ (进度解释/修复/ │                                   │
│           │  人工接手)      │                                   │
│           └─────────────────┘                                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## 五、应用场景

### 5.1 等候场景中的进度解释与分流

- 客户反复询问进度或持续表现焦虑时，系统先一步完成识别
- 提醒大堂人员核实原因，说明预计办理顺序
- 检查是否存在资料缺失或业务分流可能

### 5.2 自助操作场景中的分步引导

- 识别重复返回、同一步骤多次失败和主动求助
- 对于一般困难，界面先提供简短步骤说明和清晰的人工帮助入口
- 客户仍无法完成时，系统总结当前步骤与已完成事项并提交给大堂人员

### 5.3 复杂业务咨询与异常服务修复

- 先核实事实、明确可处理事项和办理时限
- 给出适度的理解与解释
- 涉及争议或紧急资金需求时，直接转交具备相应权限的人员处理

### 5.4 应用闭环

```
发现困难 → 系统提示 → 明确接手人员 → 响应时限 → 完成记录
     │                                        │
     ▼                                        ▼
  问题解决 ◄───────────────────────────── 未解决→更高一级处理
```

---

## 六、网点空间优化

### 6.1 评价指标

space-optimizer 接收以下九项数据：

| 指标类型 | 指标名称 | 优化方向 |
|----------|----------|----------|
| 等待数据 | 平均等待时间 | 越低越好 |
| | 平均服务时间 | 越低越好 |
| 业务数据 | 业务成功率 | 越高越好 |
| | 满意度评分 | 越高越好 |
| | 情绪积极率 | 越高越好 |
| | 投诉率 | 越低越好 |
| 空间数据 | 面积效率 | 越高越好 |
| | 功能布局评分 | 越高越好 |
| | 动线评分 | 越高越好 |

### 6.2 评价方法

采用 **Z-AHP** 与 **Z-TOPSIS** 评价方法：
1. 统一指标方向和量纲
2. 计算综合评价得分
3. 输出优化建议

---

## 七、技术栈

| 类别 | 技术选型 |
|------|----------|
| **语言** | Python 3.11+ |
| **框架** | FastAPI, PyTorch, Transformers |
| **数据库** | PostgreSQL, Redis |
| **消息队列** | Apache Kafka |
| **隐私计算** | PySyft (联邦学习), OpenDP (差分隐私) |
| **容器化** | Docker, Kubernetes |

---

## 八、快速开始

### 8.1 环境要求

- Python 3.11+
- PostgreSQL 14+ (可选，原型使用内存存储)
- Redis 7+ (可选)
- Kafka 3.5+ (可选)

### 8.2 安装依赖

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

### 8.3 启动服务

```bash
# 启动情绪识别服务 (端口 8001)
cd src/emotion_recognition && python service.py &

# 启动共情AI服务 (端口 8002)
cd src/empathy_ai && python service.py &

# 启动客户旅程编排服务 (端口 8003)
cd src/journey_orchestrator && python service.py &

# 启动服务流程引擎 (端口 8004)
cd src/service_flow && python service.py &

# 启动空间优化服务 (端口 8005)
cd src/space_optimizer && python service.py &

# 启动隐私保护服务 (端口 8006)
cd src/privacy_shield && python service.py &
```

### 8.4 API 调用示例

#### 情绪识别

```bash
# 创建会话
curl -X POST http://localhost:8001/emotion/sessions \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user_001",
    "session_type": "branch_service",
    "branch_id": "icbc_beijing_001"
  }'

# 多模态情绪识别
curl -X POST http://localhost:8001/emotion/recognize \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "emo_session_xxx",
    "text": "等太久了，我要投诉！",
    "context": {"wait_time": 25}
  }'
```

#### 共情交互

```bash
# 发送对话消息
curl -X POST http://localhost:8002/empathy/chat \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user_001",
    "message": "我要投诉！等了25分钟还没轮到！",
    "current_emotion": "angry",
    "emotion_intensity": 0.85
  }'
```

#### 网点空间评价

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
```

---

## 九、项目结构

```
bank-customer-experience/
├── src/                              # 源代码
│   ├── emotion_recognition/          # 情绪识别模块
│   │   ├── models.py                # 数据模型、融合规则
│   │   └── service.py               # FastAPI服务接口
│   ├── empathy_ai/                  # 共情交互模块
│   │   ├── models.py
│   │   └── service.py
│   ├── journey_orchestrator/        # 客户旅程编排
│   │   ├── models.py
│   │   └── service.py
│   ├── service_flow/                # 服务流程引擎
│   │   ├── models.py                # 告警规则定义
│   │   └── service.py
│   ├── space_optimizer/            # 空间优化评价
│   │   ├── models.py                # Z-AHP/Z-TOPSIS
│   │   └── service.py
│   ├── privacy_shield/              # 隐私保护模块
│   │   ├── models.py
│   │   └── service.py
│   └── common/                      # 公共配置
│       └── config.py
├── tests/                           # 测试代码
│   ├── unit/                        # 单元测试
│   └── integration/                  # 集成测试
├── docs/                            # 开发文档
│   ├── SYSTEM_DESIGN.md             # 系统设计文档
│   ├── API.md                       # API接口文档
│   ├── DEPLOYMENT.md                # 部署文档
│   └── DATABASE.md                   # 数据库设计
├── docker/                          # Docker配置
├── requirements.txt                  # Python依赖
├── pytest.ini                        # pytest配置
└── README.md                         # 项目文档
```

---

## 十、实施成本与效益

### 10.1 成本测算（示例）

| 建设项目 | 假设与计算方式 | 新增现金支出 |
|----------|----------------|--------------|
| 服务器硬件及内网复用 | 存量资产，待盘点确认 | 待定 |
| 系统运维与迭代 | 内部运维固定编制 | 0（内部投入）|
| 模型迭代优化 | 内部算法固定编制 | 0（内部投入）|
| 网点现场巡检维护 | 内部运维固定编制 | 0（内部投入）|

> 注："0（内部投入）"仅表示暂不发生新增现金支出，不代表没有成本。

### 10.2 效益评估指标

| 类别 | 指标 |
|------|------|
| **服务效率** | 首次响应时长、重复询问次数 |
| **业务完成** | 自助办理完成率、问题解决率 |
| **客户体验** | 客户满意度、持续使用意愿 |
| **运营成本** | 投诉升级率、人工工作量 |

---

## 十一、后续开发计划

| 阶段 | 内容 | 状态 |
|------|------|------|
| **第一阶段** | 设备盘点、接口梳理和离线模型评估 | ✅ 已完成 |
| **第二阶段** | 接入解释、求助与人工派单 | 🔄 进行中 |
| **第三阶段** | 接入真实模型，开展有限现场试用 | 📋 待开发 |
| **第四阶段** | 服务状态、处理结果和客户评价持久化回写 | 📋 待开发 |

---

## 十二、参考文献

[1] 中国银行业协会. 《2024年中国银行业服务报告》[EB/OL]. 2025-06-24.

[2] 中国银行业协会. 适老服务团体标准[EB/OL].

[3] Markovitch D G, et al. Consumer reactions to chatbot versus human service[J]. Journal of Retailing and Consumer Services, 2024.

[4] Guo Y, et al. Exploring the effect of empathic response in AI service recovery[J]. Journal of Retailing and Consumer Services, 2025.

[5] Juquelier A, et al. Empathic chatbots: A double-edged sword[J]. Journal of Business Research, 2025.

---

## 许可证

MIT License

---

**项目仓库**：https://github.com/JACKYwyj/bank-customer-experience
