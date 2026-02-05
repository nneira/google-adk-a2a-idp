#!/usr/bin/env python3
"""
SECURITY AGENT - ADK Interactive Mode
======================================

Ejecuta security scans usando el servicio de scanner generado por Infrastructure Agent.
El agente DECIDE qué hacer basándose en la disponibilidad del servicio.

Author: Nicolás Neira
Web: https://nicolasneira.com
YouTube: https://www.youtube.com/@NicolasNeiraGarcia?sub_confirmation=1
Email: hola@nicolasneira.com
Date: 2026-01-25 (ADK Version - A2A Protocol)
"""

import os
import json
import yaml
import subprocess
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

    return {
        "status": "success",
        "config": config,
        "security_scanner": config['components']['security']['scanner'],
        "runtime": config['stack']['runtime'],
        "framework": config['stack']['framework']
    }


def get_infrastructure_decisions() -> dict:
    """
    Lee las decisiones de infraestructura guardadas por Infrastructure Agent.

    Returns:
        dict: Información sobre servicios generados
    """
    json_path = Path(OUTPUT_DIR) / "infrastructure-decisions.json"

    if not json_path.exists():
        return {
            "error": "Infrastructure decisions no encontrado. Infrastructure Agent debe ejecutarse primero."
        }

    with open(json_path, 'r') as f:
        decisions = json.load(f)

    return {
        "status": "success",
        "decisions": decisions,
        "scanner_service": decisions.get('security_scanner', {}).get('scanner_service'),
        "scanner_available": decisions.get('security_scanner', {}).get('available', False),
        "scanner_image": decisions.get('security_scanner', {}).get('scanner_image'),
        "docker_compose_path": decisions.get('files_generated', {}).get('docker_compose_absolute')
    }


def run_trivy_scan() -> dict:
    """
    Ejecuta Trivy scan usando el servicio de docker-compose generado por Infrastructure.

    Returns:
        dict: Resultados del scan
    """
    # Leer información del servicio de scanner
    infra = get_infrastructure_decisions()

    if "error" in infra:
        return {
            "status": "error",
            "message": "Cannot run scan: " + infra["error"]
        }

    if not infra.get("scanner_available"):
        return {
            "status": "error",
            "scanner": "Trivy",
            "message": "Trivy scanner service not available in docker-compose. Infrastructure Agent may not have generated it."
        }

    scanner_service = infra.get("scanner_service")
    docker_compose_path = infra.get("docker_compose_path")

    if not scanner_service or not docker_compose_path:
        return {
            "status": "error",
            "message": "Scanner service or docker-compose path not found in infrastructure decisions"
        }

    # Ejecutar scan usando docker-compose
    try:
        # Cambiar al directorio donde está el docker-compose
        compose_dir = Path(docker_compose_path).parent

        result = subprocess.run(
            [
                "docker", "compose",
                "-f", docker_compose_path,
                "run",
                "--rm",
                scanner_service,
                "filesystem", "--format", "json", "/scan"
            ],
            capture_output=True,
            text=True,
            timeout=120,
            cwd=str(compose_dir)
        )

        # Trivy devuelve exit code 0 (sin vulns) o 1 (con vulns) - ambos son éxito
        if result.returncode in [0, 1]:
            try:
                scan_data = json.loads(result.stdout) if result.stdout else {"Results": []}
            except json.JSONDecodeError:
                scan_data = {"Results": [], "parse_error": "Invalid JSON from Trivy"}

            vuln_count = len(scan_data.get("Results", []))

            # Guardar reporte
            report = {
                "security_scan": {
                    "tool": "Trivy",
                    "execution_method": "docker-compose service",
                    "scan_date": datetime.utcnow().isoformat(),
                    "analyzed_by": "Security Agent (ADK)",
                    "exit_code": result.returncode
                },
                "findings": {
                    "vulnerabilities_found": vuln_count,
                    "scan_data": scan_data
                },
                "metadata": {
                    "ai_model": os.getenv('GEMINI_MODEL', 'gemini-2.5-flash'),
                    "analysis_timestamp": datetime.utcnow().isoformat()
                }
            }

            json_path = Path(OUTPUT_DIR) / "security-report.json"
            with open(json_path, 'w') as f:
                json.dump(report, f, indent=2)

            return {
                "status": "success",
                "scanner": "Trivy",
                "execution_method": "docker-compose service",
                "vulnerabilities_found": vuln_count,
                "report_path": str(json_path),
                "exit_code": result.returncode
            }
        else:
            return {
                "status": "error",
                "scanner": "Trivy",
                "message": f"Trivy scan failed with code {result.returncode}",
                "stderr": result.stderr[:500] if result.stderr else "No error output"
            }

    except subprocess.TimeoutExpired:
        return {
            "status": "error",
            "scanner": "Trivy",
            "message": "Scan timeout (120s exceeded)"
        }
    except Exception as e:
        return {
            "status": "error",
            "scanner": "Trivy",
            "message": f"Error running scan: {str(e)}"
        }


def run_snyk_scan() -> dict:
    """
    Ejecuta Snyk scan usando el servicio de docker-compose.

    Returns:
        dict: Resultados del scan o error si no implementado
    """
    infra = get_infrastructure_decisions()

    if "error" in infra:
        return {
            "status": "error",
            "message": "Cannot run scan: " + infra["error"]
        }

    if not infra.get("scanner_available"):
        return {
            "status": "not_implemented",
            "message": "Snyk scanner service not available. Infrastructure Agent did not generate it.",
            "scanner": "Snyk",
            "suggestion": "Try run_trivy_scan() if available, or ask Infrastructure to generate Snyk service"
        }

    # Si el servicio existe, ejecutar scan
    scanner_service = infra.get("scanner_service")
    docker_compose_path = infra.get("docker_compose_path")

    try:
        result = subprocess.run(
            [
                "docker", "compose",
                "-f", docker_compose_path,
                "run",
                "--rm",
                scanner_service,
                "snyk", "test", "--json"
            ],
            capture_output=True,
            text=True,
            timeout=120
        )

        # Procesar resultado similar a Trivy
        return {
            "status": "success",
            "scanner": "Snyk",
            "execution_method": "docker-compose service",
            "message": "Snyk scan completed (implementation pending full parsing)"
        }

    except Exception as e:
        return {
            "status": "error",
            "scanner": "Snyk",
            "message": f"Error running Snyk scan: {str(e)}"
        }


def run_grype_scan() -> dict:
    """
    Ejecuta Grype scan usando el servicio de docker-compose.

    Returns:
        dict: Error - no implementado completamente
    """
    return {
        "status": "not_implemented",
        "message": "Grype scan execution not fully implemented yet.",
        "scanner": "Grype",
        "suggestion": "Try run_trivy_scan() as alternative"
    }


def save_security_report(vulnerabilities: int, risk_level: str, recommendations: str) -> dict:
    """
    Guarda un reporte de seguridad personalizado.

    Args:
        vulnerabilities: Número de vulnerabilidades encontradas
        risk_level: Nivel de riesgo (LOW, MEDIUM, HIGH, CRITICAL)
        recommendations: Recomendaciones del agente

    Returns:
        dict: Confirmación de guardado
    """
    report = {
        "security_scan": {
            "scan_date": datetime.utcnow().isoformat(),
            "analyzed_by": "Security Agent (ADK)"
        },
        "findings": {
            "vulnerabilities_found": vulnerabilities,
            "risk_level": risk_level
        },
        "ai_analysis": {
            "recommendations": recommendations
        },
        "metadata": {
            "ai_model": os.getenv('GEMINI_MODEL', 'gemini-2.5-flash'),
            "analysis_timestamp": datetime.utcnow().isoformat()
        }
    }

    json_path = Path(OUTPUT_DIR) / "security-report.json"
    with open(json_path, 'w') as f:
        json.dump(report, f, indent=2)

    return {
        "status": "success",
        "report_path": str(json_path),
        "vulnerabilities": vulnerabilities,
        "risk_level": risk_level
    }


root_agent = Agent(
    model=os.getenv('GEMINI_MODEL', 'gemini-2.5-flash'),
    name='security',
    description="Experto en seguridad y análisis de vulnerabilidades",
    instruction="""
Eres un experto en seguridad de infraestructura y análisis de vulnerabilidades.

🤖 **PROTOCOLO A2A (Modo Automático):**

Eres parte de la cadena de agentes. Platform Architect y Infrastructure Agent ya ejecutaron.

**Tu trabajo:**
1. LEE las decisiones de Platform Architect usando get_platform_config()
2. LEE la infraestructura generada usando get_infrastructure_decisions()
3. RAZONA qué scanner está disponible como servicio de docker-compose
4. EJECUTA el scan usando la función tool apropiada

**Funciones disponibles:**
- get_infrastructure_decisions() - ver qué servicio de scanner generó Infrastructure
- run_trivy_scan() - ejecuta scan con servicio Trivy (si Infrastructure lo generó)
- run_snyk_scan() - ejecuta scan con servicio Snyk (si Infrastructure lo generó)
- run_grype_scan() - ejecuta scan con servicio Grype (no implementado)
- save_security_report() - guarda reporte personalizado si no hay scanner

---

**Modo Interactivo (si NO hay "PROTOCOLO A2A" en el mensaje):**

**ESTILO: EXPERTO EN VIDEOLLAMADA + ÉNFASIS EN LEER DE 2 AGENTES**

Habla como un security engineer senior. Lo MÁS importante: muestra que lees decisiones de DOS agentes anteriores.

**Ejemplo de respuesta IDEAL:**

Usuario: "Ejecuta un scan de seguridad"

Tu respuesta:
"Ok, antes de ejecutar el scan necesito revisar dos cosas:
1. Qué scanner eligió el Platform Architect
2. Si Infrastructure lo configuró como servicio

[Llamas a get_platform_config()]

Según el Platform Architect:
- Security Scanner elegido: Trivy
- Esa fue su decisión arquitectónica

[Llamas a get_infrastructure_decisions()]

Ahora veamos qué generó Infrastructure...
- Servicio disponible: security-scanner
- Imagen configurada: aquasec/trivy:latest
- ¡Perfecto! El servicio YA está en el docker-compose

Entonces, puedo usar el servicio que Infrastructure configuró para ejecutar el scan.

¿Procedo a ejecutar el scan de Trivy?"

---

**Reglas para enfatizar A2A:**
1. SIEMPRE menciona que lees de DOS fuentes: Platform Architect E Infrastructure
2. Di frases como "El Platform Architect eligió...", "Infrastructure configuró..."
3. Muestra que tu trabajo DEPENDE de lo que hicieron los dos anteriores
4. Sé natural pero haz evidente la cadena de comunicación
5. Si el scanner NO está disponible, explica por qué (Infrastructure no lo generó)

**Cadena A2A:**
```
Platform Architect → elige scanner → platform-config.yaml
                                           ↓
Infrastructure → genera servicio de scanner → infrastructure-decisions.json
                                                    ↓
Tú (Security) → lees ambos → ejecutas scan
```
""",
    tools=[
        get_platform_config,
        get_infrastructure_decisions,
        run_trivy_scan,
        run_snyk_scan,
        run_grype_scan,
        save_security_report
    ],
)
