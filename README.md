# Google ADK + A2A Protocol: 7 Agentes IA crean un IDP

> **Video completo:** [Google ADK + A2A Protocol: Cómo 7 Agentes IA crean un IDP](https://youtu.be/wB0ZMerDxN4)
> Canal: [@NicolasNeiraGarcia](https://youtube.com/@NicolasNeiraGarcia)

Genera un Internal Developer Platform completo con portal web en ~4.5 minutos usando 7 agentes IA especializados con Google ADK, SequentialAgent y A2A Protocol.

**→ Documentación completa: [nicolasneira.com/docs/google-adk](https://nicolasneira.com/docs/google-adk/)**

---

## Requisitos

- Docker
- [Gemini API Key](https://ai.google.dev/) (gratis)

## Setup

```bash
git clone https://github.com/nneira/google-adk-a2a-idp.git
cd google-adk-a2a-idp

export GEMINI_API_KEY="tu-api-key-aqui"
docker build -t adk-agents:hybrid .
```

## Demos

### Modo automático — pipeline end-to-end (7 agentes)

```bash
./start-demo-nicolasneira.sh "Build IDP for Python FastAPI apps"
```

Los 7 agentes corren en secuencia. Los 21 archivos generados aparecen en `test-outputs/`.

También disponible con otros prompts:

```bash
./start-demo-nicolasneira.sh "Build IDP for Go microservices with PostgreSQL"
./start-demo-nicolasneira.sh "Build IDP for Node.js apps, deploy to Google Cloud"
```

### Modo interactivo — interfaz web en localhost:8000

```bash
./start-interactive-nicolasneira.sh
# Abre http://localhost:8000
```

## Estructura

```
google-adk-a2a-idp/
├── agents_adk/
│   ├── orchestrator_adk.py           # Orquestador SequentialAgent
│   ├── platform_architect/           # Agente 1: Arquitecto
│   ├── infrastructure/               # Agente 2: Infraestructura
│   ├── security/                     # Agente 3: Seguridad
│   ├── cicd/                         # Agente 4: CI/CD
│   ├── observability/                # Agente 5: Observabilidad
│   ├── devex/                        # Agente 6: Developer Experience
│   └── web_portal/                   # Agente 7: Portal Web
├── start-demo-nicolasneira.sh
├── start-interactive-nicolasneira.sh
├── Dockerfile
└── requirements.txt
```

## Documentación

| Sección | Link |
|---|---|
| Visión general | [nicolasneira.com/docs/google-adk](https://nicolasneira.com/docs/google-adk/) |
| Inicio rápido | [/docs/google-adk/setup](https://nicolasneira.com/docs/google-adk/setup/) |
| Demo paso a paso | [/docs/google-adk/demo](https://nicolasneira.com/docs/google-adk/demo/) |
| Arquitectura | [/docs/google-adk/arquitectura](https://nicolasneira.com/docs/google-adk/arquitectura/) |
| Los 7 agentes | [/docs/google-adk/agentes](https://nicolasneira.com/docs/google-adk/agentes/) |
| A2A en este sistema | [/docs/google-adk/a2a-idp](https://nicolasneira.com/docs/google-adk/a2a-idp/) |

---

MIT · [nicolasneira.com](https://nicolasneira.com) · [hola@nicolasneira.com](mailto:hola@nicolasneira.com)
