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
    runtime: str,
    framework: str,
    database: str,
    monitoring_metrics: str,
    monitoring_visualization: str,
    security_scanner: str,
    cicd_tool: str,
    cache_strategy: str,
    deployment_target: str,
    deployment_environment: str,
    justification_runtime: str,
    justification_framework: str,
    justification_database: str,
    justification_monitoring: str,
    justification_security: str,
    justification_deployment: str,
) -> dict:
    """
    Guarda la configuración de plataforma decidida por el arquitecto.

    Args:
        runtime: Runtime elegido (ej: 'Python 3.11', 'Go 1.21')
        framework: Framework elegido (ej: 'FastAPI', 'Flask')
        database: Base de datos (ej: 'PostgreSQL', 'MongoDB')
        monitoring_metrics: Sistema de métricas (ej: 'Prometheus')
        monitoring_visualization: Visualización (ej: 'Grafana')
        security_scanner: Scanner de seguridad (ej: 'Trivy')
        cicd_tool: Herramienta CI/CD (ej: 'Jenkins')
        cache_strategy: Estrategia de cache (ej: 'Redis')
        deployment_target: Infrastructure as Code tool (ej: 'Docker Compose', 'Kubernetes', 'Terraform', 'AWS CloudFormation')
        deployment_environment: Deployment environment (ej: 'Local', 'AWS', 'GCP', 'Azure')
        justification_runtime: Por qué eligió este runtime (mínimo 50 palabras)
        justification_framework: Por qué eligió este framework (mínimo 50 palabras)
        justification_database: Por qué eligió esta base de datos (mínimo 50 palabras)
        justification_monitoring: Por qué esta estrategia de monitoring (mínimo 50 palabras)
        justification_security: Por qué este scanner de seguridad (mínimo 50 palabras)
        justification_deployment: Por qué este deployment target y environment (mínimo 50 palabras)

    Returns:
        dict: Status y path del archivo generado
    """
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
        "database": database
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


def get_user_preferences() -> dict:
    """
    Lee las preferencias del usuario desde user-preferences.yaml.

    Este archivo define las preferencias por defecto del usuario para:
    - CI/CD tool (ej: Jenkins con imagen BlueOcean)
    - Security scanner (ej: Trivy)
    - Deployment strategy (Docker Compose, Kubernetes, etc.)
    - Monitoring tools (Prometheus, Grafana)

    Returns:
        dict: Preferencias del usuario o valores por defecto si el archivo no existe
    """
    # Buscar user-preferences.yaml en el directorio del proyecto
    # Primero intenta desde /app (dentro del container)
    preferences_paths = [
        Path('/app/user-preferences.yaml'),
        Path('./user-preferences.yaml'),
        Path('../user-preferences.yaml'),
    ]

    preferences_file = None
    for path in preferences_paths:
        if path.exists():
            preferences_file = path
            break

    # Si no existe el archivo, devolver defaults
    if not preferences_file:
        return {
            "status": "not_found",
            "message": "No se encontró user-preferences.yaml. Usando valores por defecto del agente.",
            "defaults": {
                "cicd_tool": "Jenkins",
                "security_scanner": "Trivy",
                "deployment_target": "Docker Compose",
                "deployment_environment": "Local"
            }
        }

    # Leer preferencias
    try:
        with open(preferences_file, 'r') as f:
            data = yaml.safe_load(f)

        prefs = data.get('preferences', {})

        return {
            "status": "found",
            "file_path": str(preferences_file),
            "preferences": {
                "cicd_tool": prefs.get('cicd_tool'),
                "security_scanner": prefs.get('security_scanner'),
                "deployment_target": prefs.get('deployment_target'),
                "deployment_environment": prefs.get('deployment_environment'),
                "monitoring_metrics": prefs.get('monitoring_metrics'),
                "monitoring_visualization": prefs.get('monitoring_visualization'),
                "cache": prefs.get('cache'),
                "database": prefs.get('database'),
                "runtime": prefs.get('runtime')
            }
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error leyendo user-preferences.yaml: {str(e)}"
        }


# Crear el agente ADK
agent = Agent(
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
- CI/CD (Jenkins, GitHub Actions, GitLab CI, bash scripts)
  **IMPORTANTE**: Usa Jenkins si el deployment es local/Kubernetes porque tiene UI web en localhost:8080
- Cache (Redis, In-Memory, Memcached)
- **Deployment Target** (Docker Compose, Kubernetes, Terraform, AWS CloudFormation, Pulumi, Helm)
- **Deployment Environment** (Local, AWS, GCP, Azure, On-Premise)

**Cómo funcionar:**

1. **SIEMPRE** empieza llamando `get_user_preferences()` para conocer las preferencias del usuario

2. Cuando el usuario te pida construir un IDP en modo autónomo (sin chat):
   - Lee las preferencias del usuario con `get_user_preferences()`
   - **RESPETA las preferencias como REQUISITOS OBLIGATORIOS**
   - Si una preferencia está definida (no es None), **DEBES usarla exactamente como está**
   - **NO modifiques ni "mejores" las preferencias del usuario** (ej: si dice Docker Compose, NO cambies a Kubernetes)
   - Cuando una preferencia especifica una herramienta (ej: "Jenkins", "Trivy"), **TÚ debes razonar cuál es la mejor imagen oficial de Docker** para esa herramienta en 2026, considerando:
     * Imágenes oficiales vs comunitarias
     * Imágenes con plugins/herramientas pre-instaladas vs base
     * Estabilidad (latest vs versiones específicas)
     * Popularidad y mantenimiento activo
   - Solo puedes desviarte de una preferencia si es técnicamente incompatible con otra decisión
   - Si una preferencia está en None/vacía, decide tú basándote en el contexto

3. Cuando el usuario te pida construir un IDP en modo interactivo (con chat):
   - PRIMERO hazle preguntas para entender:
     * ¿Qué tipo de aplicaciones va a soportar?
     * ¿Deploy mode: local o cloud?
     * ¿Prioridades: performance, simplicidad, costo?

4. Luego RAZONA y DECIDE el stack óptimo

5. JUSTIFICA cada decisión con:
   - Por qué es la mejor opción
   - Qué alternativas consideraste
   - Trade-offs de la decisión
   - Mínimo 50 palabras por justificación

6. Usa la función 'save_platform_config' para guardar tus decisiones

7. Responde preguntas del usuario sobre tus decisiones

8. Si el usuario quiere cambiar algo, ANALIZA el impacto y regenera la configuración

**Tools disponibles:**
- get_user_preferences: **LLAMA ESTO PRIMERO** - Lee preferencias del usuario desde user-preferences.yaml
- save_platform_config: Guarda las decisiones de arquitectura
- get_current_config: Lee la configuración actual
- explain_decision: Explica una decisión específica en detalle

**IMPORTANTE:**
- SIEMPRE llama `get_user_preferences()` al inicio (especialmente en modo autónomo)
- Respeta las preferencias del usuario como DEFAULTS fuertes
- SIEMPRE justifica con razonamiento técnico profundo
- NO uses placeholders en justificaciones
- Si el usuario pregunta "por qué", RESPONDE con análisis detallado
- Puedes chatear libremente, no necesitas llamar tools inmediatamente
- Solo llama save_platform_config cuando el usuario esté de acuerdo con el stack
""",
    tools=[get_user_preferences, save_platform_config, get_current_config, explain_decision],
)
