#!/usr/bin/env python3
"""
OBSERVABILITY AGENT - ADK Interactive Mode
===========================================

Genera configuración de monitoring usando el stack elegido por Platform Architect.
El agente DECIDE qué herramienta configurar basándose en la configuración.

Author: Nicolás Neira
Web: https://nicolasneira.com
YouTube: https://www.youtube.com/@NicolasNeiraGarcia?sub_confirmation=1
Email: hola@nicolasneira.com
Date: 2026-01-18 (ADK Version)
"""

import os
import json
import yaml
from pathlib import Path
from datetime import datetime
from google.adk.agents.llm_agent import Agent

OUTPUT_DIR = os.getenv('ADK_OUTPUT_DIR', '/app/outputs')


def get_platform_config() -> dict:
    """
    Lee la configuración de plataforma guardada por Platform Architect.

    Returns:
        dict: Configuración de plataforma
    """
    config_path = Path(OUTPUT_DIR) / "platform-config.yaml"

    if not config_path.exists():
        return {
            "error": "Platform config no encontrado. Platform Architect debe ejecutarse primero."
        }

    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)

    monitoring_config = config.get('components', {}).get('monitoring', {})

    # Handle both dict and string formats
    if isinstance(monitoring_config, dict):
        metrics = monitoring_config.get('metrics', 'Prometheus')
        visualization = monitoring_config.get('visualization', 'Grafana')
        monitoring_stack = f"{metrics}+{visualization}"
    else:
        monitoring_stack = monitoring_config if monitoring_config else "Prometheus+Grafana"

    return {
        "status": "success",
        "config": config,
        "monitoring_stack": monitoring_stack,
        "monitoring_metrics": metrics if isinstance(monitoring_config, dict) else monitoring_stack.split('+')[0],
        "monitoring_visualization": visualization if isinstance(monitoring_config, dict) else monitoring_stack.split('+')[1] if '+' in monitoring_stack else 'Grafana'
    }


def setup_prometheus_grafana(dashboards: str = "generate_default") -> dict:
    """
    Configura Prometheus + Grafana.

    Args:
        dashboards: Configuración de dashboards o "generate_default"

    Returns:
        dict: Status y paths de archivos generados
    """
    # Dashboards genéricos
    app_dashboard = """{
  "dashboard": {
    "title": "IDP Application Metrics",
    "panels": [
      {
        "title": "HTTP Request Rate",
        "targets": [{"expr": "rate(http_requests_total[5m])"}]
      },
      {
        "title": "Request Latency p95",
        "targets": [{"expr": "histogram_quantile(0.95, http_request_duration_seconds_bucket)"}]
      },
      {
        "title": "Error Rate",
        "targets": [{"expr": "rate(http_errors_total[5m])"}]
      }
    ]
  }
}"""

    system_dashboard = """{
  "dashboard": {
    "title": "IDP System Metrics",
    "panels": [
      {
        "title": "CPU Usage",
        "targets": [{"expr": "rate(process_cpu_seconds_total[5m])"}]
      },
      {
        "title": "Memory Usage",
        "targets": [{"expr": "process_resident_memory_bytes"}]
      },
      {
        "title": "Disk Usage",
        "targets": [{"expr": "node_filesystem_avail_bytes"}]
      }
    ]
  }
}"""

    prometheus_config = """global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'app'
    static_configs:
      - targets: ['app:8000']

  - job_name: 'database'
    static_configs:
      - targets: ['database:5432']

  - job_name: 'cache'
    static_configs:
      - targets: ['cache:6379']
"""

    # Guardar dashboards
    grafana_dir = Path(OUTPUT_DIR) / "grafana-dashboards"
    grafana_dir.mkdir(parents=True, exist_ok=True)

    app_path = grafana_dir / "app-metrics.json"
    with open(app_path, 'w') as f:
        f.write(app_dashboard)

    system_path = grafana_dir / "system-metrics.json"
    with open(system_path, 'w') as f:
        f.write(system_dashboard)

    # Guardar prometheus config
    prom_path = Path(OUTPUT_DIR) / "docker-compose" / "prometheus.yml"
    prom_path.parent.mkdir(parents=True, exist_ok=True)
    with open(prom_path, 'w') as f:
        f.write(prometheus_config)

    # Metadata
    metadata = {
        "observability": {
            "monitoring_stack": "Prometheus+Grafana",
            "dashboards_created": ["app-metrics.json", "system-metrics.json"],
            "configs_created": ["prometheus.yml"],
            "created_at": datetime.utcnow().isoformat(),
            "generated_by": "Observability Agent (ADK)"
        },
        "metadata": {
            "ai_model": os.getenv('GEMINI_MODEL', 'gemini-2.5-flash'),
            "decision_timestamp": datetime.utcnow().isoformat()
        }
    }

    json_path = Path(OUTPUT_DIR) / "observability-decisions.json"
    with open(json_path, 'w') as f:
        json.dump(metadata, f, indent=2)

    return {
        "status": "success",
        "monitoring_stack": "Prometheus+Grafana",
        "dashboards_dir": str(grafana_dir),
        "prometheus_config": str(prom_path),
        "metadata_path": str(json_path)
    }


def setup_datadog(config: str = "generate_default") -> dict:
    """
    Configura Datadog monitoring.

    Args:
        config: Configuración de Datadog o "generate_default"

    Returns:
        dict: Error - no implementado
    """
    return {
        "status": "not_implemented",
        "message": "Datadog monitoring setup is not implemented yet.",
        "monitoring_stack": "Datadog",
        "suggestion": "Try setup_prometheus_grafana() as alternative"
    }


def setup_cloudwatch(config: str = "generate_default") -> dict:
    """
    Configura AWS CloudWatch monitoring.

    Args:
        config: Configuración de CloudWatch o "generate_default"

    Returns:
        dict: Error - no implementado
    """
    return {
        "status": "not_implemented",
        "message": "AWS CloudWatch monitoring setup is not implemented yet.",
        "monitoring_stack": "CloudWatch",
        "suggestion": "Try setup_prometheus_grafana() as alternative"
    }


def setup_new_relic(config: str = "generate_default") -> dict:
    """
    Configura New Relic monitoring.

    Args:
        config: Configuración de New Relic o "generate_default"

    Returns:
        dict: Error - no implementado
    """
    return {
        "status": "not_implemented",
        "message": "New Relic monitoring setup is not implemented yet.",
        "monitoring_stack": "New Relic",
        "suggestion": "Try setup_prometheus_grafana() as alternative"
    }


root_agent = Agent(
    model=os.getenv('GEMINI_MODEL', 'gemini-2.5-flash'),
    name='observability',
    description="Experto en observability y monitoreo de sistemas",
    instruction="""
Eres un experto en observability y monitoreo de sistemas distribuidos.

🤖 **PROTOCOLO A2A:**

Eres el 5to agente. Platform Architect ya definió el monitoring stack.

**Tu trabajo:**
1. LEE las decisiones de Platform Architect usando get_platform_config()
2. RAZONA qué monitoring stack configurar
3. EJECUTA la función tool apropiada

**Funciones disponibles:**
- setup_prometheus_grafana() - configura Prometheus + Grafana
- setup_datadog() - configura Datadog (no implementado)
- setup_cloudwatch() - configura AWS CloudWatch (no implementado)
- setup_new_relic() - configura New Relic (no implementado)

**Importante:**
- Tú decides qué función usar basándote en el monitoring_stack
- Si la función retorna "not_implemented", razona una alternativa
- Documenta tus decisiones
""",
    tools=[
        get_platform_config,
        setup_prometheus_grafana,
        setup_datadog,
        setup_cloudwatch,
        setup_new_relic
    ],
)
