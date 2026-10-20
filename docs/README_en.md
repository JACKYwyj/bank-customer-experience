# Bank Customer Experience Enhancement System
## AI-Empowered and Emotion-Aware Banking Branch Service Improvement Solution

[![GitHub Stars](https://img.shields.io/github/stars/JACKYwyj/bank-customer-experience)](https://github.com/JACKYwyj/bank-customer-experience)
[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/Tests-127%20passed-brightgreen)](https://github.com/JACKYwyj/bank-customer-experience/tree/main/tests/unit)
[![Pages](https://img.shields.io/badge/GitHub%20Pages-Live-green)](https://jackywyj.github.io/bank-customer-experience/)

---

## 🌐 Live Demo

| Link | Description |
|------|------------|
| **🔗 Live Demo** | https://jackywyj.github.io/bank-customer-experience/demo/ |
| **🇨🇳 Chinese Version** | https://jackywyj.github.io/bank-customer-experience/zh/ |
| **🇺🇸 English Version** | https://jackywyj.github.io/bank-customer-experience/en/ |

---

## Language / 语言

| [🇨🇳 中文](./README_zh.md) | [🇺🇸 English](./README_en.md) |

---

## Table of Contents

| # | Section | Description |
|---|---------|-------------|
| 1 | [Project Overview](#1-project-overview) | Executive summary, core values, tech stack |
| 2 | [Core Modules](#2-core-modules) | 6 microservice modules |
| 3 | [Project Structure](#3-project-structure) | Directory layout |
| 4 | [Quick Start](#4-quick-start) | Installation, testing, launch |
| 5 | [Simulation Tests](#5-simulation-tests) | 6 preset scenarios |
| 6 | [Deployment](#6-deployment) | Docker, Kubernetes |
| 7 | [Development Guide](#7-development-guide) | Code standards |
| 8 | [Roadmap](#8-roadmap) | Four-phase plan |
| 9 | [References](#9-references) | Citations |
| 10 | [License](#10-license) | MIT License |

---

## 1. Project Overview

### 1.1 Executive Summary

Bank branch intelligentization aims to improve operational efficiency while addressing service pain points: difficulties not being detected in time, help not arriving promptly, and issues not being handed over continuously.

This solution combines queue progress, operation logs, and customer expressions with emotional references to transform service prompts into progress explanations, step-by-step guidance, service recovery, and human takeover—effectively reducing customer complaint handling costs.

### 1.2 Core Values

| Value | Description |
|-------|-------------|
| Satisfaction | Reduce unexplained waiting, repeated inquiries, invalid operations |
| Timely Response | Link prompts to specific business steps and handlers |
| Continuous Improvement | Identify process bottlenecks from service records |
| Phased Implementation | Validate in phases, reduce risk |
| Personalized Service | Build customer profiles within compliance |
| Cost Reduction | Proactive handling reduces complaints |

### 1.3 Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           Presentation Layer                                 │
│        Web Portal │ Mobile App │ Kiosk │ Third-party Integration            │
├─────────────────────────────────────────────────────────────────────────────┤
│                           Service Layer                                      │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐      │
│  │   Emotion    │ │   Empathy    │ │   Service    │ │   Journey    │      │
│  │ Recognition  │ │      AI      │ │     Flow     │ │ Orchestrator │      │
│  │    :8001     │ │    :8002    │ │    :8004    │ │    :8003    │      │
│  └──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘      │
│  ┌──────────────┐ ┌──────────────┐                                       │
│  │    Space     │ │    Privacy   │                                       │
│  │  Optimizer   │ │    Shield   │                                       │
│  │    :8005     │ │    :8006    │                                       │
│  └──────────────┘ └──────────────┘                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                           Data Layer                                        │
│             PostgreSQL │ Redis │ Kafka                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                      Privacy Computing Layer                                │
│              Federated Learning │ Differential Privacy                      │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Core Modules

### 2.1 Emotion Recognition (Port 8001)

**Location**: [src/emotion_recognition/](src/emotion_recognition/)

**Features**: Multi-modal emotion recognition (facial, vocal, text).

**Fusion Weights** (Prototype Parameters):

| Modality | Weight | Threshold |
|----------|--------|-----------|
| Facial | 0.40 | confidence > 0.5 |
| Vocal | 0.35 | confidence > 0.5 |
| Text | 0.25 | confidence > 0.5 |

**Alert Rules**:

| Emotion | Trigger | Recommendation |
|---------|---------|----------------|
| Anxiety | score ≥ 0.5, duration ≥ 60s | Explain progress, monitor |
| Anger | score ≥ 0.8, duration ≥ 30s | Human takeover |
| Frustration | score ≥ 0.6, duration ≥ 90s | Service recovery |

**Files**: [models.py](src/emotion_recognition/models.py) | [service.py](src/emotion_recognition/service.py)

---

### 2.2 Empathy AI (Port 8002)

**Location**: [src/empathy_ai/](src/empathy_ai/)

**Features**: Context-aware empathy response and service recovery scripts.

**Files**: [models.py](src/empathy_ai/models.py) | [service.py](src/empathy_ai/service.py)

---

### 2.3 Journey Orchestrator (Port 8003)

**Location**: [src/journey_orchestrator/](src/journey_orchestrator/)

**Features**: Cross-channel service event recording, online-offline integration.

**Files**: [models.py](src/journey_orchestrator/models.py) | [service.py](src/journey_orchestrator/service.py)

---

### 2.4 Service Flow (Port 8004)

**Location**: [src/service_flow/](src/service_flow/)

**Features**: Intervention decisions, alert-based flow adjustments, human-machine collaboration.

**Files**: [models.py](src/service_flow/models.py) | [service.py](src/service_flow/service.py)

---

### 2.5 Space Optimizer (Port 8005)

**Location**: [src/space_optimizer/](src/space_optimizer/)

**Features**: Z-AHP/Z-TOPSIS evaluation for branch space optimization.

**Files**: [models.py](src/space_optimizer/models.py) | [service.py](src/space_optimizer/service.py)

---

### 2.6 Privacy Shield (Port 8006)

**Location**: [src/privacy_shield/](src/privacy_shield/)

**Features**: Privacy protection with federated learning support.

**Files**: [models.py](src/privacy_shield/models.py) | [service.py](src/privacy_shield/service.py)

---

## 3. Project Structure

```
bank-customer-experience/
├── src/                              # Source code
│   ├── emotion_recognition/          # [Module 1] Emotion recognition
│   ├── empathy_ai/                  # [Module 2] Empathy AI
│   ├── journey_orchestrator/         # [Module 3] Journey orchestrator
│   ├── service_flow/                 # [Module 4] Service flow
│   ├── space_optimizer/              # [Module 5] Space optimizer
│   ├── privacy_shield/              # [Module 6] Privacy shield
│   └── common/                       # Common config
├── tests/                            # Tests
│   ├── unit/                         # Unit tests (127 tests)
│   ├── test_simulation.py            # Simulation tests
│   └── conftest.py                   # Pytest config
├── docs/                             # Documentation
│   ├── README_en.md                  # English version
│   ├── README_zh.md                 # Chinese version
│   ├── demo/                        # Interactive demo
│   ├── SYSTEM_DESIGN.md              # System design
│   ├── API.md                       # API reference
│   ├── DEPLOYMENT.md                # Deployment guide
│   └── DATABASE.md                  # Database design
├── docker/                           # Docker configs
│   ├── Dockerfile.*                  # Service Dockerfiles
│   └── docker-compose.yml
├── requirements.txt                  # Dependencies
├── pytest.ini                        # Pytest config
└── README.md                         # This file
```

---

## 4. Quick Start

### 4.1 Requirements

- Python 3.11+
- PostgreSQL 14+ (optional)
- Redis 7+ (optional)
- Kafka 3.5+ (optional)

### 4.2 Installation

```bash
# Clone repository
git clone https://github.com/JACKYwyj/bank-customer-experience.git
cd bank-customer-experience

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 4.3 Run Tests

```bash
# Run all unit tests
pytest tests/unit/ -v

# Run simulation tests
python tests/test_simulation.py --scenario all

# Generate coverage report
pytest tests/unit/ --cov=src --cov-report=html
```

### 4.4 Start Services

```bash
# Using Docker Compose
docker-compose up -d

# Or start services individually
cd src/emotion_recognition && python service.py &  # Port 8001
cd src/empathy_ai && python service.py &             # Port 8002
cd src/journey_orchestrator && python service.py & # Port 8003
cd src/service_flow && python service.py &           # Port 8004
cd src/space_optimizer && python service.py &         # Port 8005
cd src/privacy_shield && python service.py &         # Port 8006
```

---

## 5. Simulation Tests

6 preset scenarios for testing:

```bash
# Run all scenarios
python tests/test_simulation.py --scenario all

# Run single scenario
python tests/test_simulation.py --scenario waiting_anxiety
```

| Scenario | Description | Expected Alert |
|----------|-------------|----------------|
| waiting_anxiety | Customer waiting anxiety | long_term_anxiety |
| self_service_failure | Self-service failure | negative_emotion_escalation |
| complaint_escalation | Complaint escalation | conflict_risk |
| normal_service | Normal service | None |
| elderly_service | Elderly customer | long_term_anxiety |
| vip_urgent | VIP urgent business | conflict_risk |

**Test Results**: 127 unit tests + 6 simulation scenarios ✅

---

## 6. Deployment

### Docker Compose

```bash
docker-compose up -d
```

### Kubernetes

```bash
kubectl apply -f k8s/ -n bank-customer-experience
```

---

## 7. Development Guide

### Tech Stack

| Category | Technology |
|----------|------------|
| Language | Python 3.11+ |
| Framework | FastAPI, PyTorch, Transformers |
| Database | PostgreSQL, Redis |
| Message Queue | Apache Kafka |
| Privacy | PySyft, OpenDP |
| Testing | pytest, pytest-asyncio, pytest-cov |

---

## 8. Roadmap

| Phase | Content | Status |
|-------|---------|--------|
| Phase 1 | Equipment inventory, offline evaluation | ✅ Complete |
| Phase 2 | Connect explanation, help request | 🔄 In Progress |
| Phase 3 | Real models, field trial | 📋 To Do |
| Phase 4 | Service state persistence | 📋 To Do |

---

## 9. References

[1] China Banking Association. "2024 China Banking Service Report". 2025.

[2] Markovitch D G, et al. Consumer reactions to chatbot versus human service. Journal of Retailing and Consumer Services, 2024.

[3] Guo Y, et al. Exploring the effect of empathic response in AI service recovery. Journal of Retailing and Consumer Services, 2025.

[4] Juquelier A, et al. Empathic chatbots: A double-edged sword. Journal of Business Research, 2025.

---

## 10. License

MIT License

---

## Contact

- **Email**: [1230009401@student.must.edu.mo](mailto:1230009401@student.must.edu.mo)
- **Repository**: https://github.com/JACKYwyj/bank-customer-experience
- **Live Demo**: https://jackywyj.github.io/bank-customer-experience/demo/
