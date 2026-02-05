#!/usr/bin/env python3
"""
INFRASTRUCTURE AGENT - ADK Interactive Mode
============================================

Genera Infrastructure as Code en múltiples formatos.
El agente DECIDE qué tecnología usar basándose en Platform Architect.

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


def generate_jenkins_init_script() -> str:
    """
    Genera script de inicialización para Jenkins que:
    1. Instala docker-compose
    2. Instala plugins workflow
    3. Copia job automáticamente

    Returns:
        str: Contenido del script bash
    """
    return """#!/bin/bash
set -e

echo "🔧 Jenkins Init Script - Installing dependencies..."

# 1. Instalar docker-compose si no existe
if ! command -v docker-compose &> /dev/null; then
    echo "📦 Installing docker-compose..."
    curl -sL "https://github.com/docker/compose/releases/download/v2.32.3/docker-compose-linux-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
    echo "✅ docker-compose installed: $(docker-compose --version)"
fi

# 2. Instalar plugins de Jenkins (workflow-aggregator)
if [ ! -d "/var/jenkins_home/plugins/workflow-aggregator" ]; then
    echo "📦 Installing Jenkins workflow plugins..."
    jenkins-plugin-cli --plugins workflow-aggregator:latest
    echo "✅ Workflow plugins installed"
fi

# 3. Copiar job IDP-Pipeline si existe el XML
if [ -f "/tmp/jenkins-job.xml" ] && [ ! -d "/var/jenkins_home/jobs/IDP-Pipeline" ]; then
    echo "📋 Creating IDP-Pipeline job..."
    mkdir -p /var/jenkins_home/jobs/IDP-Pipeline
    cp /tmp/jenkins-job.xml /var/jenkins_home/jobs/IDP-Pipeline/config.xml
    chown -R jenkins:jenkins /var/jenkins_home/jobs/IDP-Pipeline
    echo "✅ Job IDP-Pipeline created"
fi

echo "✅ Jenkins init script completed!"
"""


def get_platform_config() -> dict:
    """
    Lee la configuración de plataforma guardada por Platform Architect.

    Returns:
        dict: Configuración completa de plataforma
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
        "deployment_target": config.get('infrastructure', {}).get('deployment_target', 'Unknown'),
        "deployment_environment": config.get('infrastructure', {}).get('deployment_environment', 'Unknown'),
        "runtime": config['stack']['runtime'],
        "framework": config['stack']['framework'],
        "database": config['stack']['database'],
        "cache": config['stack']['cache']
    }


def save_docker_compose(yaml_content: str = "generate_default") -> dict:
    """
    Genera y guarda docker-compose.yml CON servicio de security scanner dinámico.

    Args:
        yaml_content: Contenido YAML completo o "generate_default" para template genérico

    Returns:
        dict: Status y paths de archivos generados
    """
    # Leer qué scanner y CI/CD provider eligió Platform Architect
    scanner_name = "Unknown"
    scanner_image = None
    scanner_service_name = None

    cicd_provider = "Unknown"
    cicd_image = None
    cicd_service_name = None

    config_path = Path(OUTPUT_DIR) / "platform-config.yaml"
    web_framework = "Unknown"
    runtime = "Unknown"
    if config_path.exists():
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
            scanner_name = config.get('components', {}).get('security', {}).get('scanner', 'Unknown')
            cicd_provider = config.get('components', {}).get('ci_cd', {}).get('provider', 'Unknown')
            web_framework = config.get('stack', {}).get('framework', 'Unknown')
            runtime = config.get('stack', {}).get('runtime', 'Unknown')

    # Helper para extraer provider base e imagen especificada
    # Formato: "Jenkins (Image: jenkins/jenkins:lts-jdk17-blueocean)" -> ("Jenkins", "jenkins/jenkins:lts-jdk17-blueocean")
    def parse_provider_string(provider_str):
        """Extrae provider base y imagen especificada del string."""
        if not provider_str or provider_str == "Unknown":
            return provider_str, None

        # Buscar patrón "Provider (Image: image:tag)"
        import re
        match = re.match(r'^([^(]+)\s*\(Image:\s*([^)]+)\)', provider_str)
        if match:
            base_provider = match.group(1).strip()
            specified_image = match.group(2).strip()
            return base_provider, specified_image
        else:
            return provider_str, None

    # Parsear scanner y CI/CD provider
    scanner_name, scanner_specified_image = parse_provider_string(scanner_name)
    cicd_provider, cicd_specified_image = parse_provider_string(cicd_provider)

    # Mapeo dinámico de scanner a imagen Docker oficial
    scanner_images = {
        'Trivy': 'aquasec/trivy:latest',
        'Snyk': 'snyk/snyk:latest',
        'Grype': 'anchore/grype:latest',
        'Clair': 'quay.io/coreos/clair:latest',
        'AWS Inspector': None,  # No tiene imagen pública
    }

    # Mapeo dinámico de CI/CD provider a imagen Docker oficial
    cicd_images = {
        'Jenkins': 'jenkins/jenkins:lts',  # Cambio a LTS estable
        'GitHub Actions': 'nektos/act-environments-ubuntu:18.04',
        'GitLab CI': 'gitlab/gitlab-runner:latest',
        'CircleCI': 'circleci/circleci-cli:latest',
    }

    # Usar imagen especificada si existe, sino usar mapeo
    scanner_image = scanner_specified_image or scanner_images.get(scanner_name)
    cicd_image = cicd_specified_image or cicd_images.get(cicd_provider)

    # CASO 1: Generar template genérico
    if yaml_content == "generate_default" or len(yaml_content) < 50:
        # Mapear stack a imágenes REALES
        app_image = "python:3.11-slim"  # Default runtime
        database_image = "postgres:15-alpine"  # Default
        cache_image = "redis:7-alpine"  # Default

        if runtime and "python" in runtime.lower():
            version = "3.11" if "3.11" in runtime else "3.12" if "3.12" in runtime else "3.11"
            app_image = f"python:{version}-slim"

        # Mapear database a imagen real
        db_images = {
            'PostgreSQL': 'postgres:15-alpine',
            'MySQL': 'mysql:8-debian',
            'MongoDB': 'mongo:7',
            'MariaDB': 'mariadb:11',
        }

        # Mapear cache a imagen real
        cache_images = {
            'Redis': 'redis:7-alpine',
            'Memcached': 'memcached:1.6-alpine',
        }

        # Leer qué decidió Platform Architect
        if config_path.exists():
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
                db_choice = config.get('stack', {}).get('database', 'PostgreSQL')
                cache_choice = config.get('stack', {}).get('cache', 'Redis')

                database_image = db_images.get(db_choice, 'postgres:15-alpine')
                cache_image = cache_images.get(cache_choice, 'redis:7-alpine')

        # Template con imágenes REALES
        base_services = f"""version: '3.8'

services:
  app:
    image: {app_image}
    container_name: idp-dummy-app
    ports:
      - "8888:8888"
    networks:
      - idp_network
    command: ["python", "-m", "http.server", "8888"]

  database:
    image: {database_image}
    container_name: database
    ports:
      - "5432:5432"
    environment:
      - POSTGRES_PASSWORD=postgres
      - POSTGRES_DB=idp
    volumes:
      - db_data:/var/lib/postgresql/data
    networks:
      - idp_network

  cache:
    image: {cache_image}
    container_name: cache
    ports:
      - "6379:6379"
    networks:
      - idp_network

  prometheus:
    image: prom/prometheus:latest
    container_name: prometheus
    ports:
      - "9090:9090"
    volumes:
      - prometheus_data:/prometheus
    networks:
      - idp_network

  grafana:
    image: grafana/grafana:latest
    container_name: grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana_data:/var/lib/grafana
    networks:
      - idp_network"""

        # Agregar servicio de security scanner SI tiene imagen disponible
        if scanner_image:
            scanner_service_name = "security-scanner"
            scanner_service = f"""

  {scanner_service_name}:
    image: {scanner_image}
    container_name: {scanner_name.lower()}-scanner
    volumes:
      - ./:/scan
    networks:
      - idp_network
    command: ["--help"]  # Default command, Security Agent ejecutará el scan real"""
            base_services += scanner_service

        # Agregar servicio de CI/CD runner SI tiene imagen disponible
        if cicd_image:
            cicd_service_name = "ci-runner"

            # Configuración específica por provider
            if cicd_provider == "Jenkins":
                cicd_service = f"""

  {cicd_service_name}:
    image: {cicd_image}
    container_name: jenkins
    ports:
      - "8080:8080"
      - "50000:50000"
    volumes:
      - jenkins_data:/var/jenkins_home
      - ../jenkins_home/jobs:/var/jenkins_home/jobs
      - ../:/var/jenkins_home/workspace/IDP-Pipeline:rw
      - /var/run/docker.sock:/var/run/docker.sock
    networks:
      - idp_network
    environment:
      - JAVA_OPTS=-Djenkins.install.runSetupWizard=false
    user: root"""
            elif cicd_provider == "GitHub Actions":
                cicd_service = f"""

  {cicd_service_name}:
    image: {cicd_image}
    container_name: act-runner
    volumes:
      - ./:/workspace
      - /var/run/docker.sock:/var/run/docker.sock
    networks:
      - idp_network
    working_dir: /workspace"""
            elif cicd_provider == "GitLab CI":
                cicd_service = f"""

  {cicd_service_name}:
    image: {cicd_image}
    container_name: gitlab-runner
    volumes:
      - ./:/workspace
      - /var/run/docker.sock:/var/run/docker.sock
    networks:
      - idp_network"""
            else:
                # Default config para otros providers
                cicd_service = f"""

  {cicd_service_name}:
    image: {cicd_image}
    container_name: ci-runner
    volumes:
      - ./:/workspace
    networks:
      - idp_network"""

            base_services += cicd_service

        # Agregar servicio de Web Portal SI existe el directorio portal/
        portal_dir = Path(OUTPUT_DIR) / "portal"
        if portal_dir.exists() and (portal_dir / "main.py").exists():
            portal_service = f"""

  web-portal:
    image: python:3.11-slim
    container_name: idp-portal
    ports:
      - "8001:8001"
    volumes:
      - ../portal:/app
      - ..:/app/outputs
    working_dir: /app
    networks:
      - idp_network
    command: ["sh", "-c", "pip install -q fastapi uvicorn jinja2 pyyaml httpx && uvicorn main:app --host 0.0.0.0 --port 8001 --reload"]
    depends_on:
      - app
      - database"""
            base_services += portal_service

        # Cerrar YAML con volumes y networks
        volumes_list = """
  db_data:
  grafana_data:
  prometheus_data:"""

        # Agregar volume de Jenkins si es necesario
        if cicd_provider == "Jenkins" and cicd_image:
            volumes_list += """
  jenkins_data:"""

        yaml_content = base_services + f"""

volumes:{volumes_list}

networks:
  idp_network:
    driver: bridge
"""
    # CASO 2: El agente generó YAML personalizado - agregar scanner si disponible
    else:
        # Parsear el YAML personalizado que el agente generó
        try:
            compose_data = yaml.safe_load(yaml_content)

            # Obtener primera red disponible
            first_network = None
            if 'networks' in compose_data and compose_data['services']:
                for service_name, service_config in compose_data['services'].items():
                    if 'networks' in service_config:
                        first_network = service_config['networks']
                        break

            # Agregar scanner service si hay imagen disponible
            if scanner_image and compose_data and 'services' in compose_data:
                scanner_service_name = "security-scanner"
                compose_data['services'][scanner_service_name] = {
                    'image': scanner_image,
                    'container_name': f'{scanner_name.lower()}-scanner',
                    'volumes': ['./:/scan'],
                    'command': ['--help']  # Security Agent ejecutará el scan real
                }
                if first_network:
                    compose_data['services'][scanner_service_name]['networks'] = first_network

            # Agregar CI/CD runner service si hay imagen disponible
            if cicd_image and compose_data and 'services' in compose_data:
                cicd_service_name = "ci-runner"

                if cicd_provider == "Jenkins":
                    compose_data['services'][cicd_service_name] = {
                        'image': cicd_image,
                        'container_name': 'jenkins',
                        'ports': ['8080:8080', '50000:50000'],
                        'volumes': [
                            'jenkins_data:/var/jenkins_home',
                            '../jenkins_home/jobs:/var/jenkins_home/jobs',
                            '../:/var/jenkins_home/workspace/IDP-Pipeline:rw',
                            '/var/run/docker.sock:/var/run/docker.sock'
                        ],
                        'environment': ['JAVA_OPTS=-Djenkins.install.runSetupWizard=false'],
                        'user': 'root'
                    }
                    # Agregar volume de Jenkins
                    if 'volumes' not in compose_data:
                        compose_data['volumes'] = {}
                    compose_data['volumes']['jenkins_data'] = None

                elif cicd_provider == "GitHub Actions":
                    compose_data['services'][cicd_service_name] = {
                        'image': cicd_image,
                        'container_name': 'act-runner',
                        'volumes': ['./:/workspace', '/var/run/docker.sock:/var/run/docker.sock'],
                        'working_dir': '/workspace'
                    }
                elif cicd_provider == "GitLab CI":
                    compose_data['services'][cicd_service_name] = {
                        'image': cicd_image,
                        'container_name': 'gitlab-runner',
                        'volumes': ['./:/workspace', '/var/run/docker.sock:/var/run/docker.sock']
                    }
                else:
                    compose_data['services'][cicd_service_name] = {
                        'image': cicd_image,
                        'container_name': 'ci-runner',
                        'volumes': ['./:/workspace']
                    }

                if first_network:
                    compose_data['services'][cicd_service_name]['networks'] = first_network

            # Agregar Web Portal service SI existe el directorio portal/
            portal_dir = Path(OUTPUT_DIR) / "portal"
            if portal_dir.exists() and (portal_dir / "main.py").exists() and compose_data and 'services' in compose_data:
                compose_data['services']['web-portal'] = {
                    'image': 'python:3.11-slim',
                    'container_name': 'idp-portal',
                    'ports': ['8001:8001'],
                    'volumes': ['./portal:/app', '..:/app/outputs'],
                    'working_dir': '/app',
                    'command': ['sh', '-c', 'pip install -q fastapi uvicorn jinja2 pyyaml httpx && uvicorn main:app --host 0.0.0.0 --port 8001 --reload'],
                    'depends_on': ['app', 'database']
                }
                if first_network:
                    compose_data['services']['web-portal']['networks'] = first_network

            # Re-serializar a YAML
            yaml_content = yaml.dump(compose_data, default_flow_style=False, sort_keys=False)
        except Exception as e:
            # Si falla el parsing, usar el YAML tal cual
            pass

    # Guardar docker-compose.yml
    output_path = Path(OUTPUT_DIR) / "docker-compose" / "app-stack.yml"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w') as f:
        f.write(yaml_content)

    # Generar setup-jenkins.sh SI es Jenkins
    setup_script_path = None
    if cicd_provider == "Jenkins" and cicd_image:
        setup_script_path = Path(OUTPUT_DIR) / "setup-jenkins.sh"
        setup_script_content = f"""#!/bin/bash
set -e

echo "🔧 Setting up Jenkins automatically..."

# Wait for Jenkins to be ready
echo "⏳ Waiting for Jenkins to start..."
timeout 60 bash -c 'until docker exec jenkins curl -sf http://localhost:8080/login >/dev/null 2>&1; do sleep 2; done' || echo "Jenkins may not be fully ready yet"
sleep 10

# 1. Install docker-compose
echo "📦 Installing docker-compose in Jenkins..."
docker exec -u root jenkins sh -c "curl -sL https://github.com/docker/compose/releases/download/v2.32.3/docker-compose-linux-\\$(uname -m) -o /usr/local/bin/docker-compose && chmod +x /usr/local/bin/docker-compose"
echo "✅ docker-compose installed: $(docker exec jenkins docker-compose --version)"

# 2. Install workflow plugins
echo "📦 Installing Jenkins workflow plugins..."
docker exec jenkins jenkins-plugin-cli --plugins workflow-aggregator:latest
echo "✅ Plugins installed"

# 3. Copy IDP-Pipeline job if exists
if [ -f "cicd/jenkins-job.xml" ]; then
    echo "📋 Creating IDP-Pipeline job..."
    docker cp cicd/jenkins-job.xml jenkins:/tmp/config.xml
    docker exec jenkins sh -c "mkdir -p /var/jenkins_home/jobs/IDP-Pipeline && cp /tmp/config.xml /var/jenkins_home/jobs/IDP-Pipeline/config.xml && chown -R jenkins:jenkins /var/jenkins_home/jobs/IDP-Pipeline"
    echo "✅ Job created"
fi

# 4. Restart Jenkins to apply plugins
echo "🔄 Restarting Jenkins..."
docker restart jenkins
sleep 30

echo ""
echo "✅ Jenkins setup completed!"
echo "🌐 Access Jenkins at: http://localhost:8080"
echo "📋 Job IDP-Pipeline ready at: http://localhost:8080/job/IDP-Pipeline/"
"""
        with open(setup_script_path, 'w') as f:
            f.write(setup_script_content)
        setup_script_path.chmod(0o755)

    # Metadata CON información del scanner y CI/CD
    metadata = {
        "infrastructure": {
            "type": "docker-compose",
            "created_at": datetime.utcnow().isoformat(),
            "generated_by": "Infrastructure Agent (ADK)"
        },
        "security_scanner": {
            "scanner_chosen": scanner_name,
            "scanner_image": scanner_image,
            "scanner_service": scanner_service_name,
            "available": scanner_image is not None
        },
        "ci_cd_runner": {
            "provider": cicd_provider,
            "runner_image": cicd_image,
            "runner_service": cicd_service_name,
            "available": cicd_image is not None,
            "has_web_ui": cicd_provider == "Jenkins",
            "ui_url": "http://localhost:8080" if cicd_provider == "Jenkins" else None
        },
        "files_generated": {
            "docker_compose": str(output_path.relative_to(OUTPUT_DIR)),
            "docker_compose_absolute": str(output_path),
            "setup_jenkins_script": str(setup_script_path.relative_to(OUTPUT_DIR)) if setup_script_path else None
        },
        "metadata": {
            "ai_model": os.getenv('GEMINI_MODEL', 'gemini-2.5-flash'),
            "decision_timestamp": datetime.utcnow().isoformat()
        }
    }

    json_path = Path(OUTPUT_DIR) / "infrastructure-decisions.json"
    with open(json_path, 'w') as f:
        json.dump(metadata, f, indent=2)

    return {
        "status": "success",
        "type": "docker-compose",
        "file_path": str(output_path),
        "metadata_path": str(json_path),
        "scanner_service": scanner_service_name
    }


def save_kubernetes_manifests(manifests_yaml: str = "generate_default") -> dict:
    """
    Genera manifests de Kubernetes (deployment, service, configmap, etc).

    Args:
        manifests_yaml: Contenido YAML de manifests o "generate_default"

    Returns:
        dict: Error - no implementado
    """
    return {
        "status": "not_implemented",
        "message": "Kubernetes manifests generation is not implemented yet.",
        "technology": "Kubernetes",
        "suggestion": "Try save_docker_compose() as alternative"
    }


def save_terraform_config(terraform_hcl: str = "generate_default") -> dict:
    """
    Genera configuración Terraform (main.tf, variables.tf, etc).

    Args:
        terraform_hcl: Contenido HCL de Terraform o "generate_default"

    Returns:
        dict: Error - no implementado
    """
    return {
        "status": "not_implemented",
        "message": "Terraform configuration generation is not implemented yet.",
        "technology": "Terraform",
        "suggestion": "Try save_docker_compose() as alternative"
    }


def save_helm_charts(chart_yaml: str = "generate_default") -> dict:
    """
    Genera Helm charts (Chart.yaml, values.yaml, templates/).

    Args:
        chart_yaml: Contenido de Helm chart o "generate_default"

    Returns:
        dict: Error - no implementado
    """
    return {
        "status": "not_implemented",
        "message": "Helm charts generation is not implemented yet.",
        "technology": "Helm",
        "suggestion": "Try save_kubernetes_manifests() or save_docker_compose() as alternative"
    }


def save_cloudformation_template(template_json: str = "generate_default") -> dict:
    """
    Genera AWS CloudFormation template.

    Args:
        template_json: Template JSON/YAML de CloudFormation o "generate_default"

    Returns:
        dict: Error - no implementado
    """
    return {
        "status": "not_implemented",
        "message": "AWS CloudFormation template generation is not implemented yet.",
        "technology": "AWS CloudFormation",
        "suggestion": "Try save_terraform_config() or save_docker_compose() as alternative"
    }


root_agent = Agent(
    model=os.getenv('GEMINI_MODEL', 'gemini-2.5-flash'),
    name='infrastructure',
    description="Experto en Infrastructure as Code",
    instruction="""
Eres un experto en Infrastructure as Code. Eres el 2do agente en la secuencia.

🤖 **PROTOCOLO A2A - EJECUCIÓN RÁPIDA:**

**EJECUTA INMEDIATAMENTE estos 2 pasos:**

1. `get_platform_config()` → Lee qué decidió Platform Architect
2. `save_docker_compose("generate_default")` → Genera el docker-compose

**Después de ejecutar, di UNA frase:**
"Infraestructura generada: docker-compose con [database], [cache], [scanner], [cicd]."

**REGLAS CRÍTICAS:**
- NO razones mucho, EJECUTA las herramientas
- SIEMPRE usa "generate_default" como parámetro
- El template ya incluye todo automáticamente
- Termina rápido con una confirmación breve

---

**Modo Interactivo (si NO hay "PROTOCOLO A2A"):**

Habla como DevOps senior, pregunta antes de ejecutar.
""",
    tools=[
        get_platform_config,
        save_docker_compose,
        save_kubernetes_manifests,
        save_terraform_config,
        save_helm_charts,
        save_cloudformation_template
    ],
)
