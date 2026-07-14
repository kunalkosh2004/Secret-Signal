# Secret Signal — Kubernetes Migration Guide

## When to Migrate to Kubernetes

Migrate to Kubernetes when you need:
- **Horizontal scaling** beyond what Railway/Vercel provide
- **Multi-region deployment** for global low-latency
- **Custom scaling logic** (e.g., scale WebSocket pods based on connection count)
- **On-premise deployment** for compliance or cost reasons
- **Advanced scheduling** (GPU nodes for ML inference)

**Do NOT migrate** if a managed service handles your current traffic. Kubernetes adds significant operational complexity.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                    Kubernetes Cluster                     │
│                                                           │
│  ┌─────────────────────────────────────────────────┐    │
│  │                Ingress Controller               │    │
│  │              (NGINX Ingress or Traefik)         │    │
│  │                                                  │    │
│  │   api.secret-signal.com → backend-svc:8000      │    │
│  │   secret-signal.com     → frontend-svc:80       │    │
│  └──────────────────────┬──────────────────────────┘    │
│                          │                                │
│  ┌──────────────────────▼──────────────────────────┐    │
│  │              Namespace: secret-signal            │    │
│  │                                                  │    │
│  │  ┌──────────────┐  ┌──────────────┐             │    │
│  │  │ Frontend     │  │ Backend      │             │    │
│  │  │ Deployment   │  │ Deployment   │             │    │
│  │  │ replicas: 2  │  │ replicas: 3  │             │    │
│  │  └──────────────┘  └──────────────┘             │    │
│  │                                                  │    │
│  │  ┌──────────────┐  ┌──────────────┐             │    │
│  │  │ Worker       │  │ ML Service   │             │    │
│  │  │ Deployment   │  │ Deployment   │             │    │
│  │  │ replicas: 1  │  │ replicas: 1  │             │    │
│  │  └──────────────┘  └──────────────┘             │    │
│  └─────────────────────────────────────────────────┘    │
│                                                           │
│  ┌─────────────────────────────────────────────────┐    │
│  │           Namespace: data                        │    │
│  │                                                  │    │
│  │  ┌──────────────┐  ┌──────────────┐             │    │
│  │  │ PostgreSQL   │  │ Redis        │             │    │
│  │  │ StatefulSet  │  │ StatefulSet  │             │    │
│  │  └──────────────┘  └──────────────┘             │    │
│  └─────────────────────────────────────────────────┘    │
│                                                           │
│  ┌─────────────────────────────────────────────────┐    │
│  │           Namespace: monitoring                   │    │
│  │                                                  │    │
│  │  Prometheus + Grafana + Loki + Tempo             │    │
│  └─────────────────────────────────────────────────┘    │
│                                                           │
└─────────────────────────────────────────────────────────┘
```

---

## Kubernetes Manifests

### Base Configuration (`kubernetes/base/`)

#### Frontend Deployment
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: frontend
  labels:
    app: secret-signal
    component: frontend
spec:
  replicas: 2
  selector:
    matchLabels:
      app: secret-signal
      component: frontend
  template:
    metadata:
      labels:
        app: secret-signal
        component: frontend
    spec:
      containers:
        - name: frontend
          image: secret-signal-frontend:latest
          ports:
            - containerPort: 80
          resources:
            requests:
              memory: "64Mi"
              cpu: "50m"
            limits:
              memory: "128Mi"
              cpu: "100m"
          readinessProbe:
            httpGet:
              path: /
              port: 80
            initialDelaySeconds: 5
            periodSeconds: 10
          livenessProbe:
            httpGet:
              path: /
              port: 80
            initialDelaySeconds: 10
            periodSeconds: 30
---
apiVersion: v1
kind: Service
metadata:
  name: frontend-svc
spec:
  selector:
    app: secret-signal
    component: frontend
  ports:
    - port: 80
      targetPort: 80
  type: ClusterIP
```

#### Backend Deployment
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: backend
  labels:
    app: secret-signal
    component: backend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: secret-signal
      component: backend
  template:
    metadata:
      labels:
        app: secret-signal
        component: backend
    spec:
      containers:
        - name: backend
          image: secret-signal-backend:latest
          ports:
            - containerPort: 8000
          envFrom:
            - secretRef:
                name: backend-secrets
            - configMapRef:
                name: backend-config
          resources:
            requests:
              memory: "256Mi"
              cpu: "200m"
            limits:
              memory: "512Mi"
              cpu: "500m"
          readinessProbe:
            httpGet:
              path: /readiness
              port: 8000
            initialDelaySeconds: 10
            periodSeconds: 10
          livenessProbe:
            httpGet:
              path: /health
              port: 8000
            initialDelaySeconds: 15
            periodSeconds: 30
          startupProbe:
            httpGet:
              path: /startup
              port: 8000
            failureThreshold: 30
            periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: backend-svc
spec:
  selector:
    app: secret-signal
    component: backend
  ports:
    - port: 8000
      targetPort: 8000
  type: ClusterIP
```

#### Ingress
```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: secret-signal-ingress
  annotations:
    nginx.ingress.kubernetes.io/proxy-read-timeout: "600"
    nginx.ingress.kubernetes.io/proxy-send-timeout: "600"
    nginx.ingress.kubernetes.io/websocket-services: "backend-svc"
    cert-manager.io/cluster-issuer: letsencrypt-prod
spec:
  ingressClassName: nginx
  tls:
    - hosts:
        - secret-signal.com
        - api.secret-signal.com
      secretName: secret-signal-tls
  rules:
    - host: secret-signal.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: frontend-svc
                port:
                  number: 80
    - host: api.secret-signal.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: backend-svc
                port:
                  number: 8000
```

---

## Horizontal Pod Autoscaler

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: backend-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: backend
  minReplicas: 2
  maxReplicas: 10
  metrics:
    # Scale on CPU usage
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
    # Scale on memory usage
    - type: Resource
      resource:
        name: memory
        target:
          type: Utilization
          averageUtilization: 80
    # Scale on WebSocket connections (custom metric)
    # Requires Prometheus Adapter to expose this metric
    - type: Pods
      pods:
        metric:
          name: active_websocket_connections
        target:
          type: AverageValue
          averageValue: "500"
```

---

## Secrets and ConfigMaps

```yaml
# Secret — never commit to git
apiVersion: v1
kind: Secret
metadata:
  name: backend-secrets
type: Opaque
stringData:
  DATABASE_URL: "postgresql+asyncpg://user:pass@postgres:5432/secret_signal"
  REDIS_URL: "redis://redis:6379/0"
  SECRET_KEY: "your-secret-key-here"
  GOOGLE_CLIENT_ID: ""
  GOOGLE_CLIENT_SECRET: ""

---
# ConfigMap — safe to commit
apiVersion: v1
kind: ConfigMap
metadata:
  name: backend-config
data:
  ENVIRONMENT: "production"
  LOG_LEVEL: "info"
  BACKEND_HOST: "0.0.0.0"
  BACKEND_PORT: "8000"
```

---

## Redis as StatefulSet

```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: redis
spec:
  serviceName: redis
  replicas: 1
  selector:
    matchLabels:
      app: secret-signal
      component: redis
  template:
    metadata:
      labels:
        app: secret-signal
        component: redis
    spec:
      containers:
        - name: redis
          image: redis:7-alpine
          command: ["redis-server", "--appendonly", "yes", "--maxmemory", "256mb"]
          ports:
            - containerPort: 6379
          volumeMounts:
            - name: redis-data
              mountPath: /data
          resources:
            requests:
              memory: "128Mi"
              cpu: "100m"
            limits:
              memory: "512Mi"
              cpu: "250m"
  volumeClaimTemplates:
    - metadata:
        name: redis-data
      spec:
        accessModes: ["ReadWriteOnce"]
        resources:
          requests:
            storage: 1Gi
```

---

## PostgreSQL as StatefulSet

```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: postgres
spec:
  serviceName: postgres
  replicas: 1
  selector:
    matchLabels:
      app: secret-signal
      component: postgres
  template:
    metadata:
      labels:
        app: secret-signal
        component: postgres
    spec:
      containers:
        - name: postgres
          image: postgres:15-alpine
          env:
            - name: POSTGRES_DB
              valueFrom:
                configMapKeyRef:
                  name: postgres-config
                  key: POSTGRES_DB
            - name: POSTGRES_USER
              valueFrom:
                secretKeyRef:
                  name: postgres-secrets
                  key: POSTGRES_USER
            - name: POSTGRES_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: postgres-secrets
                  key: POSTGRES_PASSWORD
          ports:
            - containerPort: 5432
          volumeMounts:
            - name: postgres-data
              mountPath: /var/lib/postgresql/data
          resources:
            requests:
              memory: "256Mi"
              cpu: "200m"
            limits:
              memory: "1Gi"
              cpu: "500m"
  volumeClaimTemplates:
    - metadata:
        name: postgres-data
      spec:
        accessModes: ["ReadWriteOnce"]
        resources:
          requests:
            storage: 10Gi
```

---

## Migration Steps (Managed → Kubernetes)

1. **Export data from managed services**
   ```bash
   pg_dump $DATABASE_URL > backup.sql
   redis-cli -u $REDIS_URL DUMP > redis_dump.rdb
   ```

2. **Create Kubernetes cluster** (GKE, EKS, AKS, or k3s for dev)

3. **Install NGINX Ingress Controller**
   ```bash
   helm install nginx-ingress ingress-nginx/ingress-nginx
   ```

4. **Install cert-manager** for automatic TLS
   ```bash
   helm install cert-manager jetstack/cert-manager --set installCRDs=true
   ```

5. **Apply manifests in order**
   ```bash
   kubectl apply -f kubernetes/base/namespace.yaml
   kubectl apply -f kubernetes/base/secrets.yaml
   kubectl apply -f kubernetes/base/configmap.yaml
   kubectl apply -f kubernetes/base/postgres.yaml
   kubectl apply -f kubernetes/base/redis.yaml
   kubectl apply -f kubernetes/base/backend.yaml
   kubectl apply -f kubernetes/base/frontend.yaml
   kubectl apply -f kubernetes/base/ingress.yaml
   kubectl apply -f kubernetes/base/hpa.yaml
   ```

6. **Run migrations** from a one-off pod
   ```bash
   kubectl run migrate --rm -it --image=secret-signal-backend:latest -- alembic upgrade head
   ```

7. **Verify**
   ```bash
   kubectl get pods -n secret-signal
   kubectl logs -f deployment/backend -n secret-signal
   curl https://api.secret-signal.com/health
   ```

---

## Environment Overlays

Use Kustomize for environment-specific configuration:

- `kubernetes/overlays/dev/` — 1 replica, debug logging, no HPA
- `kubernetes/overlays/staging/` — 2 replicas, info logging
- `kubernetes/overlays/prod/` — 3+ replicas, warning logging, HPA enabled

```bash
# Deploy to production
kubectl apply -k kubernetes/overlays/prod/
```

---

## When NOT to Use Kubernetes

Stick with managed services (Railway, Vercel, Neon) if:
- You have fewer than 10K concurrent users
- You are a single developer or small team
- You don't need custom scaling logic
- You want to focus on product, not infrastructure

Kubernetes is worth it when:
- You need multi-region deployment
- You have DevOps expertise on the team
- You need custom scheduling (GPU for ML, high-memory for caches)
- Cost optimization at scale matters (managed services get expensive)
