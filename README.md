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

### 技术架构

```
┌─────────────────────────────────────────────────────────────┐
│                      表现层 (Presentation)                    │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │  Web Portal │  │ Mobile App  │  │  Physical Kiosk     │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
├─────────────────────────────────────────────────────────────┤
│                      服务层 (Services)                       │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │  Emotion AI │  │  Empathy AI │  │  Service Flow       │  │
│  │  Service    │  │  Service    │  │  Engine             │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
├─────────────────────────────────────────────────────────────┤
│                      核心层 (Core)                           │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │ Multimodal  │  │ Privacy     │  │ Journey             │  │
│  │ Recognition │  │ Protection  │  │ Orchestration       │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
├─────────────────────────────────────────────────────────────┤
│                      数据层 (Data)                           │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │ Edge Cache  │  │ Federated   │  │ Real-time           │  │
│  │             │  │ Learning    │  │ Event Stream        │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
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

### 快速开始

```bash
# 克隆项目
git clone https://github.com/your-org/bank-customer-experience.git
cd bank-customer-experience

# 安装依赖
pip install -r requirements.txt

# 配置环境
cp .env.example .env
# 编辑 .env 填写必要的配置

# 启动开发环境
docker-compose up -d

# 运行测试
pytest tests/
```

### 目录结构

```
bank-customer-experience/
├── docs/                    # 开发文档
├── src/                     # 源代码
│   ├── emotion-recognition/ # 情绪识别模块
│   ├── empathy-ai/          # 同理心AI模块
│   ├── privacy-shield/      # 隐私保护模块
│   ├── journey-orchestrator/# 旅程编排模块
│   ├── space-optimizer/     # 空间优化模块
│   └── service-flow/        # 服务流程模块
├── tests/                   # 测试代码
├── docker/                  # Docker配置
├── scripts/                 # 辅助脚本
└── configs/                 # 配置文件
```

### 技术栈

- **语言**: Python 3.11+, TypeScript
- **框架**: FastAPI, React, PyTorch
- **数据库**: PostgreSQL, Redis, MongoDB
- **消息队列**: Apache Kafka
- **隐私计算**: PySyft (联邦学习), OpenDP (差分隐私)
- **容器化**: Docker, Kubernetes

### 开发文档

- [系统设计文档](./docs/SYSTEM_DESIGN.md)
- [API接口文档](./docs/API.md)
- [数据库设计文档](./docs/DATABASE.md)
- [部署文档](./docs/DEPLOYMENT.md)
- [模块详细设计](./docs/modules/)

### 贡献指南

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

### 许可证

MIT License

