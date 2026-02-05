# Arquitectura del Sistema
## Google ADK + A2A Protocol - IDP Auto-Provisioning

---

## Resumen

Este IDP (Internal Developer Platform) está construido usando **7 agentes IA especializados** que se comunican via el protocolo A2A (Agent-to-Agent) de Linux Foundation.

Cada agente es responsable de **un plano** del IDP, siguiendo el principio de **separación de responsabilidades**.

---

## Arquitectura del Sistema

```
┌─────────────────────────────────────────────────────────────────┐
│                      ORCHESTRATOR AGENT                         │
│                                                                 │
│  - Coordina los 7 agentes                                       │
│  - Gestiona el DAG de ejecución (grafo de dependencias)         │
│  - Maneja errores, reintentos, rollback                         │
│  - Cliente del protocolo A2A                                    │
└─────────────────────────────────────────────────────────────────┘
                            ↓ coordina ↓
        ┌───────────────────────────────────────────────┐
        │                                               │
        ↓                                               ↓
┌──────────────────┐                          ┌──────────────────┐
│ PLATFORM         │                          │ INFRASTRUCTURE   │
│ ARCHITECT        │────── architecture ─────→│ AGENT            │
│ AGENT            │        .yaml              │                  │
└──────────────────┘                          └──────────────────┘
                                                       ↓
                                              ┌──────────────────┐
                                              │ SECURITY         │
                                              │ AGENT            │
                                              └──────────────────┘
                                                       ↓
                                              ┌──────────────────┐
                                              │ CI/CD            │
                                              │ AGENT            │
                                              └──────────────────┘
                                                       ↓
                                              ┌──────────────────┐
                                              │ OBSERVABILITY    │
                                              │ AGENT            │
                                              └──────────────────┘
                                                       ↓
                                              ┌──────────────────┐
                                              │ DEVEX            │
                                              │ AGENT            │
                                              └──────────────────┘
                                                       ↓
                                              ┌──────────────────┐
                                              │ WEB PORTAL       │
                                              │ AGENT            │
                                              └──────────────────┘
```

---

## Los 7 Agentes en Detalle

### 1. Orchestrator Agent

**Rol:** Cerebro del sistema

**Responsabilidades:**
- Parsear la descripción de la tarea del usuario
- Construir el DAG de ejecución basado en dependencias
- Ejecutar agentes en orden topológico
- Recolectar outputs de cada agente
- Pasar outputs como contexto a agentes dependientes
- Manejar fallos con lógica de reintento (backoff exponencial)
- Rollback en fallos críticos

**Tecnología:**
- Python 3.11+
- Google ADK (`google-genai` package)
- Protocolo A2A para comunicación entre agentes

**Configuración:**
```python
MAX_RETRIES = 3
TIMEOUT_PER_AGENT = 300  # 5 minutos
BACKOFF_MULTIPLIER = 2   # Backoff exponencial
```

**Outputs:**
- `orchestration-report.json` - Reporte completo de ejecución
- Logs en formato JSON estructurado

---

### 2. Platform Architect Agent

**Rol:** Diseñador del IDP

**Responsabilidades:**
- Analizar requerimientos de la tarea
- Diseñar arquitectura del IDP
- Seleccionar tecnologías apropiadas
- Definir cómo se comunican los componentes
- Generar especificación de arquitectura

**Input:**
```json
{
  "task": "Build IDP for Python FastAPI apps",
  "deploy_mode": "local"
}
```

**Matriz de Decisiones:**

| Requerimiento | Elección Local | Elección Cloud |
|---------------|----------------|----------------|
| Deployment | Docker Compose | Terraform + Cloud Run |
| Base de datos | PostgreSQL container | Cloud SQL |
| Monitoring | Grafana + Prometheus | Grafana Cloud |
| Secrets | archivo .env | Secret Manager |
| CI/CD | Scripts Bash | GitHub Actions |

**Output:**
```yaml
# platform-config.yaml
version: "1.0"
deployment:
  mode: local
  orchestration: docker-compose

database:
  type: postgresql
  version: "15"

monitoring:
  metrics: prometheus
  visualization: grafana

security:
  scanner: trivy

cicd:
  build: docker
  test: pytest
  deploy: docker-compose
```

---

### 3. Infrastructure Agent

**Rol:** Provisionador de Recursos

**Responsabilidades:**
- Leer `platform-config.yaml`
- Generar infraestructura como código
  - Local: `docker-compose.yml`
  - Cloud: archivos Terraform `.tf`
- Validar configuraciones generadas

**Output (Modo Local):**
```yaml
# outputs/docker-compose/app-stack.yml
version: '3.8'

services:
  app:
    build: ./demo-app
    ports: ["8000:8000"]
    environment:
      DATABASE_URL: postgresql://user:pass@postgres:5432/db
    depends_on:
      - postgres

  postgres:
    image: postgres:15
    environment:
      POSTGRES_USER: user
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      POSTGRES_DB: db
    volumes:
      - postgres-data:/var/lib/postgresql/data

  redis:
    image: redis:alpine

  prometheus:
    image: prom/prometheus:latest

  grafana:
    image: grafana/grafana:latest
```

---

### 4. Security Agent

**Rol:** Guardián de Seguridad

**Responsabilidades:**
- Escanear Dockerfiles por problemas de seguridad
- Escanear imágenes de containers con Trivy
- Validar que no hay secrets hardcodeados
- Aplicar políticas de seguridad
- Puede BLOQUEAR deploys si encuentra issues críticos

**Tecnología:**
- Trivy (escáner de vulnerabilidades)
- Detección de secrets personalizada

**Reglas de Escaneo:**

| Severidad | Acción |
|-----------|--------|
| CRITICAL | Bloquear deploy |
| HIGH | Bloquear deploy (configurable) |
| MEDIUM | Warning (logueado) |
| LOW | Info (logueado) |

**Output:**
```json
{
  "status": "passed",
  "scan_results": {
    "dockerfile": {
      "issues": [],
      "score": 95
    },
    "image_scan": {
      "critical": 0,
      "high": 0,
      "medium": 2,
      "low": 15
    }
  },
  "recommendations": [
    "Considerar actualizar postgres a 15.2"
  ],
  "blocked": false
}
```

---

### 5. CI/CD Agent

**Rol:** Automatización de Deployment

**Responsabilidades:**
- Generar workflows de CI/CD
- Local: Scripts Bash
- Cloud: GitHub Actions, GitLab CI, etc.
- Integración de tests automatizados
- Procedimientos de rollback

**Output (Modo Local):**

```bash
#!/bin/bash
# outputs/cicd/deploy.sh

set -e

echo "🔨 Building Docker image..."
docker build -t app:latest ./demo-app

echo "🧪 Running tests..."
docker run --rm app:latest pytest tests/ -v

echo "🔍 Security scan..."
trivy image --severity CRITICAL,HIGH app:latest

echo "🚀 Deploying..."
docker-compose -f outputs/docker-compose/app-stack.yml up -d

echo "✅ Deployment completo"
echo "📊 App: http://localhost:8000"
echo "📈 Grafana: http://localhost:3000"
```

---

### 6. Observability Agent

**Rol:** Configuración de Monitoring

**Responsabilidades:**
- Provisionar Grafana + Prometheus
- Generar dashboards pre-configurados
- Configurar reglas de alertas
- Recolección de métricas

**Tecnología:**
- Prometheus (métricas)
- Grafana (visualización)
- AlertManager (alertas)

**Dashboards Generados:**
- API Latency (p50, p95, p99)
- Error Rate
- Request Throughput
- System Metrics (CPU, Memory, Disk)

**Configuración Prometheus:**
```yaml
# outputs/observability/prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'fastapi-app'
    static_configs:
      - targets: ['app:8000']
    metrics_path: '/metrics'
```

---

### 7. DevEx Agent

**Rol:** Herramientas para Developers

**Responsabilidades:**
- Generar CLI tool para developers
- Crear templates de proyectos
- Auto-generar documentación
- Simplificar operaciones complejas

**CLI Tool Generado:**

```bash
#!/bin/bash
# outputs/cli-tool/idp

case "$1" in
  init)
    echo "🎨 Inicializando nuevo proyecto..."
    ;;
  build)
    echo "🔨 Building..."
    docker build -t app:latest .
    ;;
  test)
    echo "🧪 Running tests..."
    docker run --rm app:latest pytest
    ;;
  deploy)
    echo "🚀 Deploying..."
    docker-compose up -d
    ;;
  status)
    echo "📊 Status..."
    docker-compose ps
    ;;
  logs)
    docker-compose logs -f
    ;;
  *)
    echo "Usage: idp {init|build|test|deploy|status|logs}"
    ;;
esac
```

---

### 8. Web Portal Agent

**Rol:** Generador de Portal Web Self-Service

**Responsabilidades:**
- Generar portal web COMPLETO con FastAPI + Jinja2 + HTMX + TailwindCSS
- Dashboard con servicios running (conectado a Docker API)
- Service Catalog con templates
- Form para crear nuevos servicios
- Integración con Grafana para monitoring
- Visualización de security reports

**Output:**
```
portal/
├── main.py                    # FastAPI app
├── routes/
│   ├── dashboard.py          # Dashboard overview
│   ├── catalog.py            # Service catalog
│   └── services.py           # CRUD servicios
├── templates/
│   ├── base.html             # Layout con TailwindCSS
│   ├── dashboard.html        # Dashboard principal
│   ├── catalog.html          # Templates disponibles
│   └── create_service.html   # Form crear servicio
├── services/
│   ├── docker_manager.py     # Docker API client
│   └── template_manager.py   # Generador de proyectos
├── static/
│   ├── css/
│   └── js/htmx.min.js
├── requirements.txt
└── Dockerfile
```

**Features del Portal:**
- Dashboard con servicios running (conectado a Docker API)
- Service Catalog con templates (FastAPI, Flask, Node, Go)
- Form para crear nuevos servicios con 1 click
- Monitoring con Grafana embebido
- Security reports visualizados
- UI profesional con TailwindCSS
- Interactividad con HTMX (sin JS complejo)

---

## Flujo de Ejecución Completo

```
┌─────────────────────────────────────────────────────────────┐
│ 1. INPUT DEL USUARIO                                        │
│    "Build IDP for Python FastAPI apps"                      │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 2. ORCHESTRATOR                                             │
│    - Parsea tarea                                           │
│    - Construye DAG de ejecución                             │
│    - Inicializa contexto global                             │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 3. PLATFORM ARCHITECT AGENT (~12s)                          │
│    Input: Descripción de la tarea                           │
│    Output: platform-config.yaml                             │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 4. INFRASTRUCTURE AGENT (~18s)                              │
│    Input: platform-config.yaml                              │
│    Output: docker-compose.yml                               │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 5. SECURITY AGENT (~14s)                                    │
│    Input: docker-compose.yml, Dockerfiles                   │
│    Output: security-report.json                             │
│    Decisión: APPROVED (sin issues bloqueantes)              │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 6. CI/CD AGENT (~16s)                                       │
│    Input: platform-config.yaml, security validation         │
│    Output: build.sh, test.sh, deploy.sh                     │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 7. OBSERVABILITY AGENT (~19s)                               │
│    Input: platform-config.yaml                              │
│    Output: prometheus.yml, dashboards Grafana               │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 8. DEVEX AGENT (~15s)                                       │
│    Input: Todos los outputs anteriores                      │
│    Output: idp CLI, templates, docs                         │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 9. WEB PORTAL AGENT (~45s)                                  │
│    Input: Todos los outputs anteriores                      │
│    Output: Portal web completo (FastAPI + HTMX)             │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 10. ORCHESTRATOR - RESUMEN FINAL                            │
│    Tiempo total: ~140s (~2.5 min)                           │
│    Costo: ~$0.01 USD                                        │
│    Status: SUCCESS                                          │
│    Output: orchestration-report.json                        │
└─────────────────────────────────────────────────────────────┘
```

---

## Comunicación via Protocolo A2A

### Formato de Mensaje

```json
{
  "agent_id": "infrastructure-agent",
  "timestamp": "2026-01-29T10:30:00Z",
  "action": "generate_infrastructure",
  "payload": {
    "platform_config": "...",
    "deploy_mode": "local"
  }
}
```

### Formato de Respuesta

```json
{
  "agent_id": "infrastructure-agent",
  "timestamp": "2026-01-29T10:30:15Z",
  "status": "success",
  "result": {
    "files_generated": [
      "docker-compose/app-stack.yml"
    ],
    "decisions": {
      "database": "PostgreSQL 15 - robusto y compatible con FastAPI"
    }
  }
}
```

---

## Manejo de Errores

### Lógica de Reintento

```python
for attempt in range(MAX_RETRIES):
    try:
        result = await agent.execute()
        break
    except TimeoutError:
        wait_time = BACKOFF_MULTIPLIER ** attempt
        await asyncio.sleep(wait_time)
    except AgentError as e:
        if e.severity == "critical":
            raise
        else:
            continue
```

### Estrategia de Rollback

Si un agente falla críticamente:

1. **Orchestrator detecta el fallo**
2. **Invoca rollback para agentes completados** (en orden inverso)
3. **Limpia archivos generados**
4. **Reporta fallo al usuario**

---

## Análisis de Costos

### Uso de API Gemini

| Agente | Tokens Promedio | Costo por Ejecución |
|--------|-----------------|---------------------|
| Platform Architect | 3,000 | $0.001 |
| Infrastructure | 5,000 | $0.002 |
| Security | 4,000 | $0.001 |
| CI/CD | 3,500 | $0.001 |
| Observability | 4,000 | $0.001 |
| DevEx | 3,000 | $0.001 |
| Web Portal | 8,000 | $0.003 |
| **Total** | **~30,000** | **~$0.01** |

(Basado en Gemini 2.5 Flash pricing)

---

## Consideraciones de Seguridad

### Gestión de Secrets

- **Local:** Variables de entorno (archivo `.env`, gitignored)
- **Cloud:** Google Secret Manager

### Aislamiento de Red

- **Local:** Redes internas de Docker
- **Cloud:** VPC con subnets privadas

### Mínimo Privilegio

Los agentes corren con permisos mínimos:
- Infrastructure Agent: Puede crear recursos, no puede eliminar
- Security Agent: Acceso solo lectura
- CI/CD Agent: Solo permisos de deploy

---

## Conclusión

Esta arquitectura demuestra:

- **Separación de Responsabilidades** - Cada agente tiene una responsabilidad
- **Orquestación de Agentes** - Protocolo A2A para comunicación
- **Resiliencia a Errores** - Lógica de reintento, capacidad de rollback
- **Production-Ready** - Escaneo de seguridad, monitoring, docs
- **Costo-Efectivo** - ~$0.01 por ejecución

El sistema está diseñado para ser:
- **Mantenible** - Límites claros entre agentes
- **Extensible** - Fácil agregar nuevos agentes
- **Observable** - Logging estructurado, métricas
- **Seguro** - Escaneo de seguridad integrado
