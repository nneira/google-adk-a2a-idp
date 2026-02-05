"""
PLATFORM ARCHITECT AGENT - ADK Interactive Mode
================================================

Modo interactivo para chatear con el Platform Architect.

Ejemplos de interacción:
- Usuario: "Build IDP for my web application"
- Usuario: "Why did you choose that database?"
- Usuario: "Change the database and regenerate config"

Author: Nicolás Neira
Web: https://nicolasneira.com
YouTube: https://www.youtube.com/@NicolasNeiraGarcia?sub_confirmation=1
Email: hola@nicolasneira.com
Date: 2026-01-13
"""

import os
import yaml
import json
from pathlib import Path
from datetime import datetime
from google.adk.agents.llm_agent import Agent


def save_platform_config(
    stack_summary: str
) -> dict:
    """
    Guarda la configuración de plataforma decidida por el arquitecto.

    IMPORTANTE: Llama a esta función cuando el usuario confirme que quiere guardar.

    Args:
        stack_summary: Resumen del stack decidido en formato:
            "Runtime: <runtime> | Framework: <framework> | Database: <database> | Cache: <cache> | Monitoring: <monitoring> | Security: <security> | CI/CD: <cicd> | Deployment: <deployment_target> | Environment: <deployment_environment>"

    Returns:
        dict: Status y path del archivo generado
    """
    output_dir = os.getenv('ADK_OUTPUT_DIR', './test-outputs')
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # SIEMPRE leer el user_task del archivo (escrito por orchestrator)
    user_task = ""
    task_file = Path(output_dir) / "user-task.txt"
    log_file = Path(output_dir) / "platform-architect-debug.log"

    # Log environment and file paths
    with open(log_file, 'w') as f:  # Use 'w' to overwrite
        f.write(f"=== PLATFORM ARCHITECT DEBUG LOG ===\n")
        f.write(f"ADK_OUTPUT_DIR={os.getenv('ADK_OUTPUT_DIR', 'NOT SET')}\n")
        f.write(f"output_dir={output_dir}\n")
        f.write(f"task_file={task_file}\n")
        f.write(f"task_file.exists()={task_file.exists()}\n")
        f.write(f"task_file.is_file()={task_file.is_file() if task_file.exists() else 'N/A'}\n")

    if task_file.exists():
        user_task = task_file.read_text().strip()
        with open(log_file, 'a') as f:
            f.write(f"✅ Task leído: {user_task[:100]}\n")
    else:
        with open(log_file, 'a') as f:
            f.write(f"❌ task_file NO EXISTE\n")

    # Detectar self-service capabilities automáticamente del user_task
    self_service_capabilities = []
    log_file = Path(output_dir) / "platform-architect-debug.log"
    if user_task:
        task_lower = user_task.lower()
        with open(log_file, 'a') as f:
            f.write(f"\n🔍 Detectando capabilities...\n")
            f.write(f"Task: {task_lower[:150]}\n")

        # Keywords para detectar self-service
        keywords_found = [kw for kw in ['self-service', 'self service', 'add', 'create', 'generate', 'provision'] if kw in task_lower]
        with open(log_file, 'a') as f:
            f.write(f"Keywords encontrados: {keywords_found}\n")

        if any(keyword in task_lower for keyword in ['self-service', 'self service', 'add', 'create', 'generate', 'provision']):
            with open(log_file, 'a') as f:
                f.write(f"✅ Detectado self-service\n")

            # Detectar tipos específicos
            if 'add' in task_lower and 'docker' in task_lower:
                self_service_capabilities.append({
                    "type": "add_docker_service",
                    "description": "Self-service capability: Add Docker Service",
                    "enabled": True
                })
                with open(log_file, 'a') as f:
                    f.write(f"  ✅ add_docker_service\n")

            if 'terraform' in task_lower or 'infrastructure as code' in task_lower:
                self_service_capabilities.append({
                    "type": "generate_terraform",
                    "description": "Self-service capability: Generate Terraform",
                    "enabled": True
                })

            if 'pipeline' in task_lower or 'ci/cd' in task_lower:
                self_service_capabilities.append({
                    "type": "create_pipeline",
                    "description": "Self-service capability: Create Pipeline",
                    "enabled": True
                })

            if 'database' in task_lower and 'provision' in task_lower:
                self_service_capabilities.append({
                    "type": "provision_database",
                    "description": "Self-service capability: Provision Database",
                    "enabled": True
                })

    # Parsear el stack_summary
    parts = {}
    for item in stack_summary.split('|'):
        if ':' in item:
            key, value = item.split(':', 1)
            parts[key.strip().lower().replace(' ', '_')] = value.strip()

    # Validar que todos los campos críticos estén presentes
    required_fields = ['runtime', 'framework', 'database', 'cache', 'monitoring', 'security', 'deployment', 'environment']
    missing_fields = [field for field in required_fields if field not in parts or not parts[field]]

    if missing_fields:
        return {
            "status": "error",
            "message": f"Missing required fields: {', '.join(missing_fields)}. Please provide complete stack_summary.",
            "example": "Runtime: Go 1.21 | Framework: Gin | Database: PostgreSQL | Cache: Redis | Monitoring: Prometheus+Grafana | Security: Trivy | CI/CD: Jenkins | Deployment: Docker Compose | Environment: Local"
        }

    runtime = parts['runtime']
    framework = parts['framework']
    database = parts['database']
    cache_strategy = parts['cache']
    monitoring_full = parts['monitoring']
    monitoring_metrics = monitoring_full.split('+')[0] if '+' in monitoring_full else monitoring_full
    monitoring_visualization = monitoring_full.split('+')[1] if '+' in monitoring_full else 'Grafana'
    security_scanner = parts['security']
    cicd_tool = parts.get('ci/cd', parts.get('cicd', 'Jenkins'))
    deployment_target = parts['deployment']
    deployment_environment = parts['environment']

    justification_runtime = f"Decisión basada en stack propuesto: {runtime}"
    justification_framework = f"Decisión basada en stack propuesto: {framework}"
    justification_database = f"Decisión basada en stack propuesto: {database}"
    justification_monitoring = f"Decisión basada en stack propuesto: {monitoring_metrics} + {monitoring_visualization}"
    justification_security = f"Decisión basada en stack propuesto: {security_scanner}"
    justification_deployment = f"Decisión basada en deployment: {deployment_target} en {deployment_environment}"

    output_dir = os.getenv('ADK_OUTPUT_DIR', './test-outputs')

    config = {
        "platform": {
            "name": "IDP Auto-Provisioned by AI Agents (ADK Mode)",
            "version": "1.0.0",
            "created_at": datetime.utcnow().isoformat(),
            "generated_by": "Platform Architect Agent (ADK Interactive Mode)"
        },
        "stack": {
            "runtime": runtime,
            "framework": framework,
            "database": database,
            "cache": cache_strategy
        },
        "infrastructure": {
            "deployment_target": deployment_target,
            "deployment_environment": deployment_environment
        },
        "components": {
            "monitoring": {
                "metrics": monitoring_metrics,
                "visualization": monitoring_visualization
            },
            "security": {
                "scanner": security_scanner,
                "policies": "CIS Benchmarks"
            },
            "ci_cd": {
                "provider": cicd_tool
            }
        },
        "decisions_justification": {
            "runtime": justification_runtime,
            "framework": justification_framework,
            "database": justification_database,
            "monitoring": justification_monitoring,
            "security": justification_security,
            "deployment": justification_deployment
        },
        "metadata": {
            "ai_model": "gemini-2.5-flash",
            "mode": "ADK Interactive",
            "decision_timestamp": datetime.utcnow().isoformat()
        }
    }

    # Agregar features si hay self-service capabilities
    with open(log_file, 'a') as f:
        f.write(f"\n📊 Total capabilities: {len(self_service_capabilities)}\n")
    if self_service_capabilities:
        with open(log_file, 'a') as f:
            f.write(f"✅ Agregando {len(self_service_capabilities)} capabilities:\n")
            for cap in self_service_capabilities:
                f.write(f"  - {cap['type']}\n")
        config["features"] = {
            "self_service": {
                "enabled": True,
                "capabilities": self_service_capabilities
            }
        }
    else:
        with open(log_file, 'a') as f:
            f.write(f"❌ NO capabilities, NO features section\n")

    # Guardar YAML
    output_path = Path(output_dir) / "platform-config.yaml"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w') as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)

    # Guardar JSON
    json_path = Path(output_dir) / "platform-decisions.json"
    with open(json_path, 'w') as f:
        json.dump(config, f, indent=2)

    return {
        "status": "success",
        "yaml_path": str(output_path),
        "json_path": str(json_path),
        "runtime": runtime,
        "framework": framework,
        "database": database,
        "self_service_capabilities_detected": len(self_service_capabilities),
        "capabilities": [cap["type"] for cap in self_service_capabilities]
    }


def get_current_config() -> dict:
    """
    Lee la configuración actual de platform-config.yaml si existe.

    Returns:
        dict: Configuración actual o mensaje de que no existe
    """
    output_dir = os.getenv('ADK_OUTPUT_DIR', './test-outputs')
    config_path = Path(output_dir) / "platform-config.yaml"

    if not config_path.exists():
        return {
            "status": "not_found",
            "message": "No se ha generado ninguna configuración aún. Usa 'save_platform_config' primero."
        }

    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)

    return {
        "status": "found",
        "config": config
    }


def explain_decision(decision_type: str) -> dict:
    """
    Explica una decisión específica tomada por el arquitecto.

    Args:
        decision_type: Tipo de decisión ('runtime', 'framework', 'database', 'monitoring', 'security')

    Returns:
        dict: Justificación de la decisión
    """
    output_dir = os.getenv('ADK_OUTPUT_DIR', './test-outputs')
    config_path = Path(output_dir) / "platform-config.yaml"

    if not config_path.exists():
        return {
            "status": "error",
            "message": "No hay configuración generada aún."
        }

    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)

    justifications = config.get('decisions_justification', {})

    if decision_type not in justifications:
        return {
            "status": "error",
            "message": f"Tipo de decisión '{decision_type}' no encontrado. Opciones: runtime, framework, database, monitoring, security"
        }

    return {
        "status": "success",
        "decision_type": decision_type,
        "justification": justifications[decision_type],
        "chosen_value": config['stack'].get(decision_type) or config['components'].get(decision_type)
    }


# Crear el agente ADK (DEBE llamarse root_agent para ADK web)
root_agent = Agent(
    model=os.getenv('GEMINI_MODEL', 'gemini-2.5-flash'),
    name='platform_architect',
    description="Arquitecto de plataformas especializado en Internal Developer Platforms (IDPs). Analiza tareas y decide stack tecnológico óptimo.",
    instruction="""Eres un arquitecto de plataformas experto especializado en Internal Developer Platforms (IDPs).

Tu trabajo es ANALIZAR las tareas del usuario y DECIDIR qué arquitectura tecnológica usar.

**Capacidades:**
1. Analizar requisitos y decidir stack tecnológico óptimo
2. Justificar cada decisión con razonamiento técnico profundo
3. Responder preguntas sobre decisiones arquitectónicas
4. Modificar decisiones basándote en feedback del usuario

**Decisiones que tomas:**
- Runtime (Python, Go, Node.js, Rust)
- Framework (FastAPI, Flask, Django, Gin, Express, etc)
- Database (PostgreSQL, MySQL, MongoDB, SQLite)
- Monitoring (Prometheus + Grafana, Datadog, CloudWatch)
- Security Scanner (Trivy, Snyk, AWS Inspector)
- CI/CD (GitHub Actions, bash scripts, GitLab CI)
- Cache (Redis, In-Memory, Memcached)

**🤖 PROTOCOLO A2A - Modo Automático:**

⛔ **ATENCIÓN - REQUISITO OBLIGATORIO:** ⛔
Si NO llamas a save_platform_config(), los agentes siguientes FALLARÁN porque NO podrán leer el archivo.
Gemini DEBE ejecutar la función Python. NO generes YAML/JSON manualmente.

**Pasos OBLIGATORIOS:**

1. **DECIDE** el stack en 1 frase

2. **LLAMA A LA FUNCIÓN** save_platform_config() INMEDIATAMENTE:

⚠️ **CRÍTICO - Debes llamar a la función Python:**

save_platform_config(stack_summary="Runtime: Python 3.11 | Framework: FastAPI | Database: PostgreSQL | Cache: Redis | Monitoring: Prometheus+Grafana | Security: Trivy | CI/CD: Jenkins | Deployment: Docker Compose | Environment: Local")

⚠️ **NO HAGAS ESTO:**
- NO generes YAML directamente
- NO generes JSON directamente
- NO crees archivos manualmente
- SOLO llama a save_platform_config()

✅ **La función se encarga de:**
- Guardar YAML y JSON
- Detectar capabilities de self-service del user task
- Crear justificaciones
- TODO automáticamente

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**💬 Modo Interactivo (si NO hay "PROTOCOLO A2A"):**

**ESTILO DE COMUNICACIÓN - EXPERTO EN VIDEOLLAMADA:**

Habla como un arquitecto senior en una reunión con un colega. Natural, directo, pensando en voz alta.

**Ejemplo de cómo debes responder:**

Usuario: "Quiero un IDP para apps Python con FastAPI"

Tu respuesta:
"Ok, déjame ver qué te conviene...

FastAPI + Python - perfecto, eso me simplifica las decisiones.

Para base de datos... PostgreSQL, definitivamente. El soporte JSON nativo es ideal para los modelos Pydantic que vas a usar con FastAPI. MySQL funcionaría pero Postgres tiene mejor rendimiento en queries complejas.

Cache... Redis, sin duda. Es más versátil que Memcached y tiene excelente integración con el ecosistema Python.

Monitoring... Prometheus + Grafana, el estándar de la industria para métricas y dashboards.

Security scanner... Trivy, es open source y muy efectivo para escanear containers.

CI/CD... para simplicidad local, scripts bash. Si prefieres algo más robusto, podemos usar GitHub Actions.

Te propongo este stack:
- Python 3.11 + FastAPI
- PostgreSQL
- Redis  
- Prometheus + Grafana
- Trivy
- Docker Compose local

¿Te parece bien? ¿Lo guardamos o quieres ajustar algo?"

---

**Reglas de interacción:**

1. Piensa en voz alta de forma NATURAL - como si estuvieras en una videollamada
2. NO uses formatos rígidos como "Mi Razonamiento:" o listas muy estructuradas
3. Explica TUS RAZONES brevemente mientras decides (ej: "PostgreSQL porque el soporte JSON...")
4. Sé conversacional - usa frases como "déjame ver...", "ok, para esto...", "definitivamente..."  
5. SIEMPRE pregunta antes de guardar: "¿Te parece? ¿Lo guardamos?"
6. Si el usuario dice sí, guarda, ok, dale → USA save_platform_config() INMEDIATAMENTE

**Cómo guardar:**
save_platform_config(stack_summary="Runtime: X | Framework: Y | Database: Z | Cache: W | Monitoring: M | Security: S | CI/CD: C | Deployment: D | Environment: E")

**🛠️ DETECCIÓN DE SELF-SERVICE CAPABILITIES:**

Si el task del usuario menciona palabras clave como:
- "self-service", "add", "create", "generate", "provision", "deploy"
- "formulario", "form", "user can", "allow users to"

Debes EXTRAER y DOCUMENTAR las capabilities solicitadas:

**Ejemplos de extracción:**

Task: "Build IDP with self-service for adding Docker services"
→ Detectas: 1 capability: add_docker_service

Task: "Build IDP where users can add Docker services, generate Terraform modules, and create CI/CD pipelines"
→ Detectas: 3 capabilities:
  1. add_docker_service
  2. generate_terraform
  3. create_pipeline

Task: "Build IDP with self-service portal for provisioning databases and S3 buckets"
→ Detectas: 2 capabilities:
  1. provision_database
  2. provision_s3

**Formato de documentación:**

Cuando guardes con save_platform_config(), si detectaste self-service, incluye al FINAL del stack_summary:

stack_summary="Runtime: X | Framework: Y | ... | SelfService: add_docker_service,generate_terraform,create_pipeline"

Si NO hay self-service en el task, NO agregues la parte "| SelfService: ...".

**Importante:**
- Usa nombres descriptivos y snake_case (add_docker_service, generate_terraform)
- Separa múltiples capabilities con comas (sin espacios)
- Sé específico con lo que el usuario pidió

**Otras reglas:**
- SIEMPRE justifica con razonamiento técnico profundo
- NO uses placeholders en justificaciones
- Si el usuario pregunta "por qué", RESPONDE con análisis detallado
""",
    tools=[save_platform_config, get_current_config, explain_decision],
)
