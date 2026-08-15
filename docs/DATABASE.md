# 数据库设计文档 (Database Design)

## 1. 设计原则

- **规范化**：遵循第三范式(3NF)，减少数据冗余
- **分区化**：按时间或业务进行表分区，提升查询性能
- **审计化**：关键操作记录审计日志
- **隐私化**：敏感数据加密存储

---

## 2. ER图概览

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Customer  │────▶│   Session   │────▶│   Emotion   │
└─────────────┘     └─────────────┘     └─────────────┘
       │                   │                   │
       │                   ▼                   ▼
       │            ┌─────────────┐     ┌─────────────┐
       │            │ Interaction │     │   Alert     │
       │            └─────────────┘     └─────────────┘
       │                   │
       ▼                   ▼
┌─────────────┐     ┌─────────────┐
│  Journey    │     │   Flow      │
│  Event      │     │  Instance   │
└─────────────┘     └─────────────┘
```

---

## 3. 表结构设计

### 3.1 客户表 (customers)

```sql
CREATE TABLE customers (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         VARCHAR(64) NOT NULL UNIQUE,
    name            VARCHAR(128),
    phone           VARCHAR(32) ENCRYPTED,
    email           VARCHAR(256) ENCRYPTED,
    tier            VARCHAR(32) DEFAULT 'standard',  -- standard, silver, gold, platinum
    segments        TEXT[],                           -- 客户分群标签
    risk_level      VARCHAR(16) DEFAULT 'low',
    status          VARCHAR(16) DEFAULT 'active',
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deleted_at      TIMESTAMP
);

CREATE INDEX idx_customers_user_id ON customers(user_id);
CREATE INDEX idx_customers_tier ON customers(tier);
CREATE INDEX idx_customers_status ON customers(status);
```

### 3.2 情绪识别会话表 (emotion_sessions)

```sql
CREATE TABLE emotion_sessions (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id          VARCHAR(64) NOT NULL UNIQUE,
    user_id             VARCHAR(64) NOT NULL,
    channel             VARCHAR(32) NOT NULL,  -- web, mobile, kiosk, branch
    device_id           VARCHAR(128),
    branch_id           VARCHAR(64),
    window_id           VARCHAR(64),
    started_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ended_at            TIMESTAMP,
    expires_at          TIMESTAMP NOT NULL,
    final_emotion       VARCHAR(32),
    emotion_history     JSONB,                  -- 存储情绪变化历史
    metadata            JSONB,
    status              VARCHAR(16) DEFAULT 'active',
    
    FOREIGN KEY (user_id) REFERENCES customers(user_id)
);

CREATE INDEX idx_sessions_session_id ON emotion_sessions(session_id);
CREATE INDEX idx_sessions_user_id ON emotion_sessions(user_id);
CREATE INDEX idx_sessions_branch_time ON emotion_sessions(branch_id, started_at);
CREATE INDEX idx_sessions_status ON emotion_sessions(status);

-- 分区：按月分区
CREATE TABLE emotion_sessions_2024_01 PARTITION OF emotion_sessions
    FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');
```

### 3.3 情绪记录表 (emotion_records)

```sql
CREATE TABLE emotion_records (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id          VARCHAR(64) NOT NULL,
    user_id             VARCHAR(64),
    timestamp           TIMESTAMP NOT NULL,
    
    -- 多模态情绪数据
    primary_emotion     VARCHAR(32) NOT NULL,
    primary_confidence  DECIMAL(5,4),
    secondary_emotion   VARCHAR(32),
    secondary_confidence DECIMAL(5,4),
    
    -- 情绪维度
    valence             DECIMAL(5,4),           -- 效价: -1~1
    arousal             DECIMAL(5,4),           -- 唤醒度: 0~1
    
    -- 各模态结果
    facial_data         JSONB,                  -- {"emotion": "xxx", "confidence": 0.92, ...}
    vocal_data          JSONB,                  -- {"emotion": "xxx", "confidence": 0.85, ...}
    text_data           JSONB,                  -- {"emotion": "xxx", "confidence": 0.78, ...}
    
    -- 融合信息
    modalities          VARCHAR(32)[],          -- 使用的模态
    fused_confidence    DECIMAL(5,4),
    
    -- 告警信息
    alert_triggered     BOOLEAN DEFAULT FALSE,
    alert_type          VARCHAR(64),
    alert_recommendation TEXT,
    
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (session_id) REFERENCES emotion_sessions(session_id)
);

CREATE INDEX idx_emotion_session ON emotion_records(session_id);
CREATE INDEX idx_emotion_user_time ON emotion_records(user_id, timestamp);
CREATE INDEX idx_emotion_primary ON emotion_records(primary_emotion);
CREATE INDEX idx_emotion_timestamp ON emotion_records(timestamp);
```

### 3.4 同理心对话表 (empathy_conversations)

```sql
CREATE TABLE empathy_conversations (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id          VARCHAR(64) NOT NULL,
    user_id             VARCHAR(64) NOT NULL,
    agent_id            VARCHAR(64) NOT NULL,
    
    user_message        TEXT NOT NULL,
    user_emotion        VARCHAR(32),
    user_emotion_intensity DECIMAL(5,4),
    
    agent_response      TEXT,
    empathy_level       VARCHAR(16),            -- low, medium, high
    empathy_score       DECIMAL(5,4),
    
    action_recommendations JSONB,
    escalation_required BOOLEAN DEFAULT FALSE,
    escalation_reason   TEXT,
    
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (session_id) REFERENCES emotion_sessions(session_id)
);

CREATE INDEX idx_conversation_session ON empathy_conversations(session_id);
CREATE INDEX idx_conversation_user ON empathy_conversations(user_id);
CREATE INDEX idx_conversation_time ON empathy_conversations(created_at);
```

### 3.5 服务流程定义表 (flow_processes)

```sql
CREATE TABLE flow_processes (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    process_code    VARCHAR(64) NOT NULL UNIQUE,
    name            VARCHAR(256) NOT NULL,
    category        VARCHAR(32) NOT NULL,       -- complaint, inquiry, transaction
    version         VARCHAR(16) DEFAULT '1.0',
    status          VARCHAR(16) DEFAULT 'active',
    
    -- 流程定义(JSON)
    definition      JSONB NOT NULL,             -- 完整的流程定义
    stages          JSONB NOT NULL,             -- 流程阶段定义
    transition_rules JSONB,                     -- 状态转换规则
    
    -- 统计信息
    avg_duration_minutes INTEGER,
    success_rate    DECIMAL(5,4),
    satisfaction_score DECIMAL(5,4),
    
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_flow_code ON flow_processes(process_code);
CREATE INDEX idx_flow_category ON flow_processes(category);
```

### 3.6 流程实例表 (flow_instances)

```sql
CREATE TABLE flow_instances (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    instance_id         VARCHAR(64) NOT NULL UNIQUE,
    process_id          UUID NOT NULL,
    process_code        VARCHAR(64) NOT NULL,
    
    user_id             VARCHAR(64) NOT NULL,
    session_id          VARCHAR(64),
    
    trigger_type        VARCHAR(32),            -- emotion_alert, manual, automatic
    trigger_data        JSONB,
    
    current_stage       VARCHAR(64) NOT NULL,
    status              VARCHAR(16) DEFAULT 'active',  -- active, paused, completed, cancelled
    
    -- 流程上下文
    context             JSONB,                  -- 存储流程执行中的动态数据
    
    -- 情绪追踪
    emotion_at_entry    VARCHAR(32),
    emotion_current     VARCHAR(32),
    emotion_improvement DECIMAL(5,4),
    
    -- 时间戳
    started_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at        TIMESTAMP,
    
    -- 阶段完成记录
    stage_history       JSONB,
    
    FOREIGN KEY (process_id) REFERENCES flow_processes(id)
);

CREATE INDEX idx_instance_id ON flow_instances(instance_id);
CREATE INDEX idx_instance_process ON flow_instances(process_id);
CREATE INDEX idx_instance_user ON flow_instances(user_id);
CREATE INDEX idx_instance_status ON flow_instances(status);
```

### 3.7 客户旅程事件表 (journey_events)

```sql
CREATE TABLE journey_events (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         VARCHAR(64) NOT NULL,
    event_type      VARCHAR(64) NOT NULL,
    event_category  VARCHAR(32),               -- emotion, behavior, transaction, service
    
    -- 事件数据
    event_data      JSONB NOT NULL,
    
    -- 关联信息
    session_id      VARCHAR(64),
    channel         VARCHAR(32),
    branch_id       VARCHAR(64),
    
    -- 时间
    event_timestamp TIMESTAMP NOT NULL,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES customers(user_id)
);

-- 分区：按天分区
CREATE TABLE journey_events_2024_01_01 PARTITION OF journey_events
    FOR VALUES FROM ('2024-01-01') TO ('2024-01-02');

CREATE INDEX idx_journey_user_time ON journey_events(user_id, event_timestamp);
CREATE INDEX idx_journey_type ON journey_events(event_type);
CREATE INDEX idx_journey_session ON journey_events(session_id);
```

### 3.8 隐私设置表 (privacy_settings)

```sql
CREATE TABLE privacy_settings (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id             VARCHAR(64) NOT NULL UNIQUE,
    
    -- 数据收集设置
    emotion_data_collection BOOLEAN DEFAULT TRUE,
    biometric_storage       BOOLEAN DEFAULT FALSE,
    
    -- 数据保留
    data_retention_days     INTEGER DEFAULT 90,
    
    -- 数据使用
    third_party_sharing     BOOLEAN DEFAULT FALSE,
    marketing_use           BOOLEAN DEFAULT FALSE,
    research_use            BOOLEAN DEFAULT TRUE,
    
    -- 同意记录
    consent_history         JSONB,
    
    -- 权利行使
    deletion_requested      BOOLEAN DEFAULT FALSE,
    deletion_request_date   TIMESTAMP,
    
    created_at              TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at              TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES customers(user_id)
);

CREATE INDEX idx_privacy_user ON privacy_settings(user_id);
```

### 3.9 隐私审计日志表 (privacy_audit_logs)

```sql
CREATE TABLE privacy_audit_logs (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- 操作类型
    action_type     VARCHAR(64) NOT NULL,      -- access, delete, update, share
    action_category VARCHAR(32),               -- data_request, breach, audit
    
    -- 操作者
    operator_id     VARCHAR(64),
    operator_type   VARCHAR(32),               -- system, user, admin
    
    -- 涉及数据
    user_id         VARCHAR(64),
    data_types      VARCHAR(32)[],
    record_ids      UUID[],
    
    -- 请求信息
    request_id      VARCHAR(64),
    ip_address      VARCHAR(64),
    user_agent      TEXT,
    
    -- 结果
    status          VARCHAR(16),               -- success, failed, partial
    details         JSONB,
    
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_audit_user ON privacy_audit_logs(user_id);
CREATE INDEX idx_audit_action ON privacy_audit_logs(action_type);
CREATE INDEX idx_audit_time ON privacy_audit_logs(created_at);
```

### 3.10 网点信息表 (branches)

```sql
CREATE TABLE branches (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    branch_id       VARCHAR(64) NOT NULL UNIQUE,
    name            VARCHAR(256) NOT NULL,
    region          VARCHAR(64),
    city            VARCHAR(64),
    address         TEXT,
    
    -- 空间信息
    total_area      DECIMAL(10,2),             -- 平方米
    zones           JSONB,                     -- 功能区配置
    
    -- 设备信息
    devices         JSONB,                     -- 设备列表
    kiosk_count     INTEGER DEFAULT 0,
    
    -- 评价指标
    evaluation_scores JSONB,
    
    status          VARCHAR(16) DEFAULT 'active',
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_branch_id ON branches(branch_id);
CREATE INDEX idx_branch_region ON branches(region);
```

### 3.11 情绪分析报表表 (emotion_reports)

```sql
CREATE TABLE emotion_reports (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    report_type     VARCHAR(64) NOT NULL,      -- daily, weekly, monthly, custom
    branch_id       VARCHAR(64),
    
    -- 报表周期
    period_start    DATE NOT NULL,
    period_end      DATE NOT NULL,
    
    -- 汇总数据
    summary         JSONB NOT NULL,
    emotion_dist    JSONB,
    emotion_trend   JSONB,
    insights        JSONB,
    
    generated_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_report_branch_time ON emotion_reports(branch_id, period_start);
CREATE INDEX idx_report_type ON emotion_reports(report_type);
```

---

## 4. 索引策略

### 4.1 组合索引

```sql
-- 客户情绪历史查询
CREATE INDEX idx_emotion_user_session_time 
ON emotion_records(user_id, session_id, timestamp DESC);

-- 网点情绪统计
CREATE INDEX idx_emotion_branch_time 
ON emotion_records(branch_id, timestamp DESC) 
WHERE alert_triggered = TRUE;

-- 旅程事件分析
CREATE INDEX idx_journey_user_type_time 
ON journey_events(user_id, event_type, event_timestamp DESC);
```

### 4.2 部分索引

```sql
-- 仅索引活跃会话
CREATE INDEX idx_active_sessions ON emotion_sessions(branch_id, started_at)
WHERE status = 'active';

-- 仅索引负面情绪告警
CREATE INDEX idx_negative_alerts ON emotion_records(session_id, timestamp)
WHERE alert_triggered = TRUE;
```

---

## 5. 分区策略

### 5.1 时间分区

对以下表按月/天分区：
- `emotion_records`：按月分区
- `journey_events`：按天分区
- `emotion_reports`：按月分区

### 5.2 分区管理

```sql
-- 创建新分区
CREATE TABLE emotion_records_2024_02 PARTITION OF emotion_records
    FOR VALUES FROM ('2024-02-01') TO ('2024-03-01');

-- 分离旧分区为独立表
ALTER TABLE emotion_records DETACH PARTITION emotion_records_2023_01;
```

---

## 6. 数据保留策略

| 数据类型 | 保留期 | 归档策略 |
|----------|--------|----------|
| 情绪原始数据 | 90天 | 90天后聚合存储 |
| 客户旅程事件 | 2年 | 2年后归档到冷存储 |
| 流程实例 | 1年 | 完成后1年归档 |
| 隐私审计日志 | 5年 | 法定要求 |
| 客户基本信息 | 永久 | 账户存续期间 |

---

## 7. 安全策略

### 7.1 列级加密

```sql
-- 使用PostgreSQL的pgcrypto扩展
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- 加密敏感字段
ALTER TABLE customers 
ADD COLUMN phone_encrypted BYTEA,
ADD COLUMN email_encrypted BYTEA;

-- 加密函数
CREATE OR REPLACE FUNCTION encrypt_field(text)
RETURNS BYTEA AS $$
BEGIN
    RETURN pgp_sym_encrypt($1, current_setting('app.encryption_key'), 'compress-algo=1, cipher-algo=aes256');
END;
$$ LANGUAGE plpgsql;

-- 解密函数
CREATE OR REPLACE FUNCTION decrypt_field(bytea)
RETURNS TEXT AS $$
BEGIN
    RETURN pgp_sym_decrypt($1, current_setting('app.encryption_key'));
END;
$$ LANGUAGE plpgsql;
```

### 7.2 行级安全

```sql
-- 启用行级安全策略
ALTER TABLE customers ENABLE ROW LEVEL SECURITY;

-- 用户只能查看自己的数据
CREATE POLICY customer_own_data ON customers
    FOR ALL
    USING (user_id = current_user);

-- 管理员可以查看所有数据
CREATE POLICY admin_all_data ON customers
    FOR ALL
    USING (current_user = 'admin');
```

---

## 8. 监控指标

```sql
-- 表大小统计
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS total_size,
    pg_size_pretty(pg_relation_size(schemaname||'.'||tablename)) AS table_size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- 索引使用统计
SELECT 
    indexrelname,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch
FROM pg_stat_user_indexes
WHERE schemaname = 'public'
ORDER BY idx_scan DESC;

-- 慢查询日志配置
ALTER SYSTEM SET log_min_duration_statement = 1000;  -- 1秒
```

---

*文档版本：v1.0*
*最后更新：2024-01-15*
