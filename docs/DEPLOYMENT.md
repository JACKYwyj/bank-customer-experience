# 部署文档 (Deployment Guide)

## 1. 环境准备

### 1.1 系统要求

| 组件 | 版本 | 说明 |
|------|------|------|
| Kubernetes | 1.28+ | 容器编排 |
| Docker | 24.0+ | 容器运行时 |
| Helm | 3.14+ | 包管理器 |
| PostgreSQL | 15+ | 主数据库 |
| Redis | 7.0+ | 缓存 |
| Kafka | 3.6+ | 消息队列 |

### 1.2 基础设施准备

```bash
# 创建命名空间
kubectl create namespace bank-customer-experience

# 创建镜像拉取密钥（私有仓库需要）
kubectl create secret docker-registry regcred \
  --docker-server=registry.example.com \
  --docker-username=your-username \
  --docker-password=your-password \
  --namespace=bank-customer-experience

# 创建配置密钥
kubectl create secret generic app-config \
  --from-file=config.yaml=./configs/config.yaml \
  --namespace=bank-customer-experience

# 创建数据库密钥
kubectl create secret generic db-credentials \
  --from-literal=POSTGRES_PASSWORD=xxx \
  --from-literal=REDIS_PASSWORD=xxx \
  --namespace=bank-customer-experience
```

---

## 2. 镜像构建

### 2.1 构建所有服务镜像

```bash
# 在项目根目录执行
./scripts/build-images.sh

# 或者分别构建
docker build -t registry.example.com/bank-customer-experience/emotion-recognition:v1.0 ./src/emotion-recognition
docker build -t registry.example.com/bank-customer-experience/empathy-ai:v1.0 ./src/empathy-ai
docker build -t registry.example.com/bank-customer-experience/privacy-shield:v1.0 ./src/privacy-shield
docker build -t registry.example.com/bank-customer-experience/journey-orchestrator:v1.0 ./src/journey-orchestrator
docker build -t registry.example.com/bank-customer-experience/service-flow:v1.0 ./src/service-flow
docker build -t registry.example.com/bank-customer-experience/space-optimizer:v1.0 ./src/space-optimizer
docker build -t registry.example.com/bank-customer-experience/gateway:v1.0 ./docker/gateway
```

### 2.2 推送到镜像仓库

```bash
docker push registry.example.com/bank-customer-experience/emotion-recognition:v1.0
docker push registry.example.com/bank-customer-experience/empathy-ai:v1.0
docker push registry.example.com/bank-customer-experience/privacy-shield:v1.0
docker push registry.example.com/bank-customer-experience/journey-orchestrator:v1.0
docker push registry.example.com/bank-customer-experience/service-flow:v1.0
docker push registry.example.com/bank-customer-experience/space-optimizer:v1.0
docker push registry.example.com/bank-customer-experience/gateway:v1.0
```

---

## 3. Helm部署

### 3.1 添加Helm仓库

```bash
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo update
```

### 3.2 部署基础设施

```bash
# PostgreSQL
helm upgrade --install postgresql bitnami/postgresql \
  --namespace bank-customer-experience \
  --set auth.database=bank_customer_experience \
  --set persistence.size=100Gi

# Redis
helm upgrade --install redis bitnami/redis \
  --namespace bank-customer-experience \
  --set auth.password=xxx \
  --set persistence.size=10Gi

# Kafka
helm upgrade --install kafka bitnami/kafka \
  --namespace bank-customer-experience \
  --set replicaCount=3 \
  --set persistence.size=50Gi
```

### 3.3 部署应用服务

```bash
# 复制并修改配置
cp values.yaml.example values.yaml
# 编辑 values.yaml 配置镜像地址、副本数等

# 部署所有服务
helm upgrade --install bank-customer-experience ./helm/bank-customer-experience \
  --namespace bank-customer-experience \
  --values values.yaml

# 或者分服务部署
helm upgrade --install emotion-recognition ./helm/emotion-recognition \
  --namespace bank-customer-experience

helm upgrade --install empathy-ai ./helm/empathy-ai \
  --namespace bank-customer-experience

helm upgrade --install privacy-shield ./helm/privacy-shield \
  --namespace bank-customer-experience
```

---

## 4. Kubernetes资源配置

### 4.1 服务部署示例 (emotion-recognition)

```yaml
# emotion-recognition-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: emotion-recognition
  namespace: bank-customer-experience
  labels:
    app: emotion-recognition
spec:
  replicas: 3
  selector:
    matchLabels:
      app: emotion-recognition
  template:
    metadata:
      labels:
        app: emotion-recognition
    spec:
      containers:
      - name: emotion-recognition
        image: registry.example.com/bank-customer-experience/emotion-recognition:v1.0
        ports:
        - containerPort: 8000
        env:
        - name: MODEL_PATH
          value: /models/emotion_model
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: db-credentials
              key: DATABASE_URL
        resources:
          requests:
            memory: "2Gi"
            cpu: "1000m"
            nvidia.com/gpu: "1"
          limits:
            memory: "4Gi"
            cpu: "2000m"
            nvidia.com/gpu: "1"
        volumeMounts:
        - name: model-volume
          mountPath: /models
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 5
      volumes:
      - name: model-volume
        persistentVolumeClaim:
          claimName: emotion-model-pvc
---
apiVersion: v1
kind: Service
metadata:
  name: emotion-recognition-service
  namespace: bank-customer-experience
spec:
  selector:
    app: emotion-recognition
  ports:
  - protocol: TCP
    port: 8000
    targetPort: 8000
  type: ClusterIP
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: emotion-recognition-hpa
  namespace: bank-customer-experience
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: emotion-recognition
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

### 4.2 Ingress配置

```yaml
# ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: bank-customer-experience-ingress
  namespace: bank-customer-experience
  annotations:
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    nginx.ingress.kubernetes.io/proxy-body-size: "50m"
    nginx.ingress.kubernetes.io/proxy-connect-timeout: "30"
    nginx.ingress.kubernetes.io/proxy-read-timeout: "300"
    nginx.ingress.kubernetes.io/proxy-send-timeout: "300"
spec:
  ingressClassName: nginx
  tls:
  - hosts:
    - api.bank-customer-experience.com
    secretName: api-tls-secret
  rules:
  - host: api.bank-customer-experience.com
    http:
      paths:
      - path: /emotion
        pathType: Prefix
        backend:
          service:
            name: emotion-recognition-service
            port:
              number: 8000
      - path: /empathy
        pathType: Prefix
        backend:
          service:
            name: empathy-ai-service
            port:
              number: 8000
      - path: /privacy
        pathType: Prefix
        backend:
          service:
            name: privacy-shield-service
            port:
              number: 8000
```

---

## 5. 配置管理

### 5.1 ConfigMap

```yaml
# configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
  namespace: bank-customer-experience
data:
  APP_ENV: "production"
  LOG_LEVEL: "info"
  API_TIMEOUT: "30"
  MAX_UPLOAD_SIZE: "10485760"
  KAFKA_BOOTSTRAP_SERVERS: "kafka-headless:9092"
  REDIS_HOST: "redis-master"
  REDIS_PORT: "6379"
```

### 5.2 环境变量配置

| 变量名 | 说明 | 示例值 |
|--------|------|--------|
| `APP_ENV` | 运行环境 | production |
| `DATABASE_URL` | 数据库连接 | postgresql://... |
| `REDIS_URL` | Redis连接 | redis://... |
| `KAFKA_BOOTSTRAP_SERVERS` | Kafka地址 | kafka:9092 |
| `MODEL_PATH` | 模型路径 | /models |
| `JWT_SECRET` | JWT密钥 | (base64编码) |
| `ENCRYPTION_KEY` | 数据加密密钥 | (base64编码) |

---

## 6. 监控与告警

### 6.1 Prometheus配置

```yaml
# prometheus-config.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: prometheus-config
  namespace: monitoring
data:
  prometheus.yml: |
    global:
      scrape_interval: 15s
    scrape_configs:
    - job_name: 'bank-customer-experience'
      kubernetes_sd_configs:
      - role: pod
      relabel_configs:
      - source_labels: [__meta_kubernetes_pod_label_app]
        action: keep
        regex: emotion-recognition|empathy-ai|privacy-shield|journey-orchestrator
```

### 6.2 Grafana仪表盘

导入预配置的仪表盘JSON文件：`./configs/grafana-dashboards/`

---

## 7. 运维操作

### 7.1 滚动更新

```bash
# 更新镜像版本
kubectl set image deployment/emotion-recognition \
  emotion-recognition=registry.example.com/bank-customer-experience/emotion-recognition:v1.1 \
  -n bank-customer-experience

# 查看更新进度
kubectl rollout status deployment/emotion-recognition -n bank-customer-experience
```

### 7.2 回滚

```bash
# 回滚到上一版本
kubectl rollout undo deployment/emotion-recognition -n bank-customer-experience

# 回滚到指定版本
kubectl rollout undo deployment/emotion-recognition --to-revision=2 -n bank-customer-experience
```

### 7.3 扩缩容

```bash
# 手动扩缩容
kubectl scale deployment emotion-recognition --replicas=5 -n bank-customer-experience

# 使用HPA自动扩缩容（已配置）
# 系统会根据CPU/内存使用率自动调整副本数
```

### 7.4 日志查看

```bash
# 查看Pod日志
kubectl logs -f deployment/emotion-recognition -n bank-customer-experience

# 查看特定Pod
kubectl logs -f emotion-recognition-5d8b7c4d6f-x2k9p -n bank-customer-experience

# 查看历史日志
kubectl logs --tail=1000 deployment/emotion-recognition -n bank-customer-experience > logs.txt
```

### 7.5 数据库迁移

```bash
# 执行数据库迁移
kubectl exec -it postgresql-primary-0 -n bank-customer-experience -- psql -U postgres

# 或者使用迁移脚本
kubectl exec -it emotion-recognition-5d8b7c4d6f-x2k9p -n bank-customer-experience -- python -m alembic upgrade head
```

---

## 8. 灾难恢复

### 8.1 备份策略

```bash
# PostgreSQL备份
kubectl exec postgresql-primary-0 -n bank-customer-experience -- pg_dump -U postgres bank_customer_experience > backup.sql

# Redis备份
kubectl exec redis-master-0 -n bank-customer-experience -- redis-cli SAVE
```

### 8.2 恢复流程

```bash
# 恢复PostgreSQL
kubectl exec -i postgresql-primary-0 -n bank-customer-experience -- psql -U postgres bank_customer_experience < backup.sql
```

---

## 9. 环境配置对照表

| 环境 | 副本数 | CPU限制 | 内存限制 | GPU |
|------|--------|---------|----------|-----|
| Dev | 1 | 500m | 1Gi | 0 |
| Test | 2 | 1000m | 2Gi | 1 |
| Staging | 3 | 2000m | 4Gi | 1 |
| Prod | 5-10 | 4000m | 8Gi | 1-2 |

---

## 10. 健康检查

```bash
# 检查所有Pod状态
kubectl get pods -n bank-customer-experience

# 检查服务健康
curl https://api.bank-customer-experience.com/emotion/health

# 检查数据库连接
kubectl exec -it emotion-recognition-xxx -n bank-customer-experience -- python -c "from app.database import engine; print(engine.execute('SELECT 1'))"
```

---

*文档版本：v1.0*
*最后更新：2024-01-15*
