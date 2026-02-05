# Google ADK + A2A Protocol: 7 Agentes IA crean un IDP

**Genera un Internal Developer Platform completo con portal web en ~3 minutos usando 7 agentes IA especializados.**

[![YouTube](https://img.shields.io/badge/YouTube-Ver%20Video-red?logo=youtube)](https://youtube.com/@nicolasneiragarcia)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## Qué hace este sistema

Ejecutas **UN comando** y la IA genera:

- `platform-config.yaml` - Stack tecnológico decidido por IA
- `docker-compose/app-stack.yml` - Infraestructura completa
- `security-report.json` - Análisis de vulnerabilidades
- `cicd/` - Scripts (build.sh, test.sh, deploy.sh)
- `grafana-dashboards/` - Dashboards pre-configurados
- `cli-tool/idp` - CLI para developers
- `portal/` - Portal web completo (FastAPI + HTMX + TailwindCSS)

---

## Los 7 Agentes

| # | Agente | Qué hace |
|---|--------|----------|
| 1 | **Platform Architect** | Analiza y DECIDE el stack tecnológico |
| 2 | **Infrastructure** | Genera docker-compose.yml |
| 3 | **Security** | Analiza vulnerabilidades |
| 4 | **CI/CD** | Genera scripts de deployment |
| 5 | **Observability** | Configura Prometheus + Grafana |
| 6 | **DevEx** | Genera CLI tool para developers |
| 7 | **Web Portal** | Genera portal web self-service |

---

## Quick Start

### Prerequisitos

- Docker
- Gemini API Key ([Obtener gratis](https://ai.google.dev/))

### 1. Clonar y configurar

```bash
git clone https://github.com/nneira/google-adk-a2a-idp.git
cd google-adk-a2a-idp

# Configurar API Key
export GEMINI_API_KEY="tu-api-key-aqui"
```

### 2. Build de la imagen

```bash
docker build -t adk-agents:hybrid .
```

### 3. Ejecutar los 7 agentes

**Opción A: Usando script (recomendado)**

```bash
./start-demo-nicolasneira.sh "Build IDP for Python FastAPI apps"
```

**Opción B: Modo interactivo (UI Web)**

```bash
./start-interactive-nicolasneira.sh
# Abre http://localhost:8000 y chatea con los agentes
```

**Duración:** ~3 minutos

### 4. Ver lo que generó la IA

```bash
ls -la test-outputs/
```

---

## Scripts de Demo

| Script | Modo | Descripción |
|--------|------|-------------|
| `start-demo-nicolasneira.sh` | Automático | Ejecuta los 7 agentes secuencialmente (usado en el video) |
| `start-interactive-nicolasneira.sh` | Interactivo | UI web para chatear con agentes |

### Modo Automático (Demo del Video)

```bash
./start-demo-nicolasneira.sh "Build IDP for Go microservices"
```

### Modo Interactivo (UI Web)

```bash
./start-interactive-nicolasneira.sh
# Abre http://localhost:8000
```

---

## Archivos Generados

```
test-outputs/
├── platform-config.yaml          # Decisiones del Platform Architect
├── platform-decisions.json       # Justificaciones (la IA razona)
├── docker-compose/
│   └── app-stack.yml             # Infraestructura completa
├── security-report.json          # Análisis de seguridad
├── cicd/
│   ├── build.sh
│   ├── test.sh
│   └── deploy.sh
├── grafana-dashboards/
│   ├── app-metrics.json
│   └── system-metrics.json
├── cli-tool/
│   └── idp                       # CLI bash tool
├── portal/                       # Portal web completo
│   ├── main.py
│   ├── routes/
│   ├── templates/
│   ├── services/
│   └── Dockerfile
└── *-decisions.json              # Justificaciones de cada agente
```

---

## Levantar lo generado

### 1. Infraestructura (PostgreSQL, Redis, Prometheus, Grafana)

```bash
cd test-outputs/docker-compose
docker-compose -f app-stack.yml up -d
```

### 2. Portal Web

```bash
cd test-outputs/portal
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 3000 --reload
```

### 3. Acceder

- **Portal:** http://localhost:3000
- **Grafana:** http://localhost:3000 (admin/admin)
- **Prometheus:** http://localhost:9090

---

## Personalizar la tarea

Cambia el `--task` para generar IDPs diferentes:

```bash
# Para Node.js
--task "Build IDP for real-time chat with Node.js and MongoDB"

# Para Go microservices
--task "Build IDP for high-performance microservices with Go"

# Para ML
--task "Build IDP for ML model serving with Python and TensorFlow"
```

La IA decidirá el stack óptimo para cada caso.

---

## Stack Tecnológico

- **AI Model:** Gemini 2.5 Flash
- **Framework:** Google ADK (Agent Development Kit)
- **Protocol:** A2A (Agent-to-Agent) - Linux Foundation
- **Portal:** FastAPI + Jinja2 + HTMX + TailwindCSS

---

## Costo por ejecución

~$0.01 USD (1 centavo) usando Gemini 2.5 Flash

---

## Estructura del Repo

```
google-adk-a2a-idp/
├── agents_adk/                       # Los 7 agentes (Google ADK)
│   ├── orchestrator_adk.py           # Orquestador SequentialAgent
│   ├── platform_architect/           # Agente 1: Arquitecto
│   ├── infrastructure/               # Agente 2: Infraestructura
│   ├── security/                     # Agente 3: Seguridad
│   ├── cicd/                         # Agente 4: CI/CD
│   ├── observability/                # Agente 5: Observabilidad
│   ├── devex/                        # Agente 6: Developer Experience
│   └── web_portal/                   # Agente 7: Portal Web
├── docs/
│   └── ARCHITECTURE.md               # Documentación técnica
├── test-outputs/                     # Donde la IA genera todo
├── start-demo-nicolasneira.sh        # Script modo automático (usado en video)
├── start-interactive-nicolasneira.sh         # Script modo interactivo (UI web)
├── Dockerfile
├── requirements.txt
├── .env.example
└── README.md
```

---

## Documentación

Ver [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) para:
- Cómo funcionan los 7 agentes
- Protocolo A2A
- Flujo de ejecución
- Manejo de errores

---

## Video

Mira el video completo donde construyo este sistema:

**[Google ADK + A2A Protocol: Cómo 7 Agentes IA crean un IDP](https://youtube.com/@nicolasneiragarcia)**

---

## Licencia

MIT

---

## Autor

**Nicolás Neira**

- Web: [nicolasneira.com](https://nicolasneira.com)
- YouTube: [@nicolasneiragarcia](https://youtube.com/@nicolasneiragarcia)
- Email: hola@nicolasneira.com

---

**Sin humo. Solo sistemas reales.**
