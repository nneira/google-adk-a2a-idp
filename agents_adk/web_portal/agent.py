#!/usr/bin/env python3
"""
WEB PORTAL AGENT - ADK Interactive Mode
========================================

Genera web portal dinámicamente usando Gemini.
Lee la configuración del IDP y genera un portal completo con enlaces, health checks, y dashboard interactivo.

Author: Nicolás Neira
Web: https://nicolasneira.com
YouTube: https://www.youtube.com/@NicolasNeiraGarcia?sub_confirmation=1
Email: hola@nicolasneira.com
Date: 2026-01-27 (ADK Version - NO HARDCODED)
"""

import os
import json
import yaml
from pathlib import Path
from datetime import datetime
from google.adk.agents.llm_agent import Agent

OUTPUT_DIR = os.getenv('ADK_OUTPUT_DIR', '/app/outputs')


def read_idp_configuration() -> dict:
    """
    Lee toda la configuración del IDP para generar el portal.

    Extrae:
    - Platform config (stack, framework, database, etc.)
    - Docker compose services (nombres, puertos, imágenes)
    - Decisiones de todos los agentes

    Returns:
        dict: Configuración completa del IDP
    """
    output_path = Path(OUTPUT_DIR)

    # 1. Leer platform config
    platform_config_path = output_path / "platform-config.yaml"
    if not platform_config_path.exists():
        return {
            "error": "Platform config no encontrado. Platform Architect debe ejecutarse primero.",
            "status": "error"
        }

    with open(platform_config_path, 'r') as f:
        platform_config = yaml.safe_load(f)

    # 2. Leer docker-compose para extraer servicios y puertos
    docker_compose_path = output_path / "docker-compose" / "app-stack.yml"
    services = {}

    if docker_compose_path.exists():
        with open(docker_compose_path, 'r') as f:
            docker_compose = yaml.safe_load(f)

        # Extraer información de cada servicio
        if 'services' in docker_compose:
            for service_name, service_config in docker_compose['services'].items():
                ports = service_config.get('ports', [])
                image = service_config.get('image', 'unknown')
                container_name = service_config.get('container_name', service_name)

                # Extraer puerto expuesto (formato "8080:8080" o "host:container")
                exposed_port = None
                if ports:
                    port_mapping = str(ports[0]).replace('"', '')
                    if ':' in port_mapping:
                        exposed_port = port_mapping.split(':')[0]
                    else:
                        exposed_port = port_mapping

                services[service_name] = {
                    "name": service_name,
                    "container_name": container_name,
                    "image": image,
                    "port": exposed_port,
                    "url": f"http://localhost:{exposed_port}" if exposed_port else None
                }

    # 3. Leer decisiones de todos los agentes
    decisions = {}
    decision_files = [
        "platform-decisions.json",
        "infrastructure-decisions.json",
        "security-report.json",
        "cicd-decisions.json",
        "observability-decisions.json",
        "devex-decisions.json"
    ]

    for decision_file in decision_files:
        decision_path = output_path / decision_file
        if decision_path.exists():
            with open(decision_path, 'r') as f:
                decisions[decision_file.replace('.json', '')] = json.load(f)

    # 4. Extraer self-service capabilities del platform config
    self_service_capabilities = []
    if 'features' in platform_config and 'self_service' in platform_config['features']:
        if platform_config['features']['self_service'].get('enabled'):
            self_service_capabilities = platform_config['features']['self_service'].get('capabilities', [])

    return {
        "status": "success",
        "platform": platform_config.get('platform', {}),
        "stack": platform_config.get('stack', {}),
        "components": platform_config.get('components', {}),
        "platform_config": platform_config,
        "services": services,
        "decisions": decisions,
        "self_service_capabilities": self_service_capabilities,
        "total_services": len(services),
        "output_dir": str(output_path)
    }


def generate_portal(action: str = "generate_default") -> dict:
    """
    Genera el portal web completo del IDP.

    Args:
        action: Acción a realizar. Usa "generate_default" para generar el portal completo
               basándose en la configuración del IDP.

    Returns:
        dict: Status y paths de archivos creados
    """
    # Leer configuración del IDP
    idp_config = read_idp_configuration()
    if idp_config.get("status") == "error":
        return {"status": "error", "message": idp_config.get("error")}

    services = idp_config.get("services", {})
    stack = idp_config.get("stack", {})
    platform = idp_config.get("platform", {})

    portal_dir = Path(OUTPUT_DIR) / "portal"
    portal_dir.mkdir(parents=True, exist_ok=True)
    templates_dir = portal_dir / "templates"
    templates_dir.mkdir(parents=True, exist_ok=True)

    # Generar main.py dinámicamente basado en los servicios
    services_list = []
    for name, svc in services.items():
        port = svc.get("port", "N/A")
        # Usar container_name como host interno, salvo para 'app' que sabemos que
        # el pipeline lo despliega como 'idp-dummy-app' independiente del compose
        internal_host = svc.get("container_name", name)
        if name == "app":
            internal_host = "idp-dummy-app"
            
        services_list.append(f'    {{"name": "{name}", "host": "{internal_host}", "port": "{port}", "url": "http://localhost:{port}"}}')

    services_code = ",\n".join(services_list) if services_list else '    {"name": "app", "host": "idp-dummy-app", "port": "8888", "url": "http://localhost:8888"}'

    main_py_code = f'''"""
IDP Portal - Generated by Web Portal Agent
==========================================
"""
from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse
import yaml
import httpx
import socket
import os
from pathlib import Path
from datetime import datetime

app = FastAPI(title="IDP Portal", version="1.0.0")

# Detectar rutas según entorno (Docker vs Local)
BASE_DIR = Path(__file__).resolve().parent
if Path("/app/templates").exists():
    TEMPLATES_DIR = "/app/templates"
    CONFIG_PATH = "/app/outputs/platform-config.yaml"
    IS_DOCKER = True
else:
    TEMPLATES_DIR = str(BASE_DIR / "templates")
    CONFIG_PATH = str(BASE_DIR.parent / "platform-config.yaml")
    IS_DOCKER = False

templates = Jinja2Templates(directory=TEMPLATES_DIR)

# Services extracted from docker-compose
SERVICES = [
{services_code}
]

def load_config():
    """Load platform configuration."""
    config_path = Path(CONFIG_PATH)
    if config_path.exists():
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    return {{"stack": {{"runtime": "N/A", "framework": "N/A", "database": "N/A", "cache": "N/A"}},
            "infrastructure": {{"deployment_target": "N/A", "deployment_environment": "N/A"}},
            "components": {{"monitoring": {{"metrics": "N/A", "visualization": "N/A"}}}}}}

async def check_service_health(service_name: str, host: str, port: str) -> str:
    """Check if a service is healthy."""
    try:
        # Determinar host objetivo: si estamos en Docker usamos el nombre del contenedor,
        # si estamos en local usamos localhost
        target_host = host if IS_DOCKER else "localhost"

        # For databases/cache, use socket check
        if port in ["5432", "6379"]:
            try:
                # Resolver host primero
                host_ip = socket.gethostbyname(target_host)
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1)
                result = sock.connect_ex((host_ip, int(port)))
                sock.close()
                return "Healthy" if result == 0 else "Down"
            except:
                return "Down"
        
        # For HTTP services
        async with httpx.AsyncClient(timeout=2.0) as client:
            if port == "9090":  # Prometheus
                url = f"http://{{target_host}}:{{port}}/-/healthy"
            elif port == "3000":  # Grafana
                url = f"http://{{target_host}}:{{port}}/api/health"
            elif port == "8888":  # Dummy App
                url = f"http://{{target_host}}:{{port}}/health"
            elif port == "8080":  # Jenkins
                url = f"http://{{target_host}}:{{port}}/login"
            else:
                url = f"http://{{target_host}}:{{port}}/"

            response = await client.get(url)
            return "Healthy" if response.status_code < 500 else "Down"
    except Exception as e:
        print(f"Health check failed for {{service_name}} ({{target_host}}:{{port}}): {{str(e)}}")
        return "Down"

@app.get("/")
async def index(request: Request):
    """Dashboard principal."""
    config = load_config()
    services_status = []
    for svc in SERVICES:
        status = await check_service_health(svc["name"], svc["host"], str(svc["port"]))
        services_status.append({{**svc, "status": status, "healthy": status == "Healthy"}})
    
    return templates.TemplateResponse("index.html", {{
        "request": request,
        "config": config,
        "services": services_status
    }})

@app.get("/api/services")
async def api_services():
    """API para obtener estado de servicios."""
    services_status = []
    for svc in SERVICES:
        status = await check_service_health(svc["name"], svc["host"], str(svc["port"]))
        services_status.append({{**svc, "status": status, "healthy": status == "Healthy"}})
    return {{"services": services_status, "timestamp": datetime.utcnow().isoformat()}}

@app.get("/health")
async def health():
    return {{"status": "healthy"}}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
'''

    # Generar index.html dinámicamente
    runtime = stack.get("runtime", "N/A")
    framework = stack.get("framework", "N/A")
    database = stack.get("database", "N/A")
    cache = stack.get("cache", "N/A")

    index_html_code = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>IDP Portal</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        .sidebar {{ background: linear-gradient(180deg, #1e3a5f 0%, #0f2744 100%); }}
        .service-card {{ transition: all 0.2s ease; }}
        .service-card:hover {{ transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,0.15); }}
        .status-healthy {{ color: #22c55e; }}
        .status-down {{ color: #ef4444; }}
    </style>
</head>
<body class="bg-gray-100 min-h-screen">
    <div class="flex">
        <aside class="sidebar w-56 min-h-screen text-white fixed">
            <div class="p-4 border-b border-white/20">
                <h1 class="text-lg font-bold text-cyan-400">IDP Portal</h1>
            </div>
            <nav class="p-4 space-y-2">
                <a href="/" class="flex items-center gap-2 px-3 py-2 rounded-lg bg-white/10">⚡ Services</a>
                <a href="http://localhost:3000" target="_blank" class="flex items-center gap-2 px-3 py-2 rounded-lg hover:bg-white/10">📊 Grafana</a>
                <a href="http://localhost:9090" target="_blank" class="flex items-center gap-2 px-3 py-2 rounded-lg hover:bg-white/10">📈 Prometheus</a>
                <a href="http://localhost:8080" target="_blank" class="flex items-center gap-2 px-3 py-2 rounded-lg hover:bg-white/10">🔄 Jenkins</a>
            </nav>
        </aside>
        <main class="ml-56 flex-1 p-8">
            <h1 class="text-2xl font-bold text-gray-800 mb-2">Welcome to Your Internal Developer Platform</h1>
            <p class="text-gray-500 mb-8">Overview of your services and infrastructure</p>
            
            <section class="mb-8">
                <h2 class="text-lg font-semibold text-gray-700 mb-4">⚡ Services Overview</h2>
                <div class="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-4 gap-4">
                    {{% for service in services %}}
                    <div class="service-card bg-white rounded-lg p-4 shadow-sm border">
                        <h3 class="font-semibold text-blue-600 mb-2">🚀 {{{{ service.name }}}}</h3>
                        <p class="text-sm text-gray-500">Port: {{{{ service.port }}}}</p>
                        <p class="text-sm text-gray-500 mb-2">URL: <a href="{{{{ service.url }}}}" class="text-blue-500">{{{{ service.url }}}}</a></p>
                        <span class="{{% if service.healthy %}}status-healthy{{% else %}}status-down{{% endif %}}">● {{{{ service.status }}}}</span>
                        <a href="{{{{ service.url }}}}" target="_blank" class="block mt-2 bg-blue-600 text-white text-center py-1 rounded text-sm">Open</a>
                    </div>
                    {{% endfor %}}
                </div>
            </section>
            
            <section class="mb-8">
                <h2 class="text-lg font-semibold text-gray-700 mb-4">🔧 Platform Stack</h2>
                <div class="bg-white rounded-lg p-6 shadow-sm">
                    <div class="grid grid-cols-4 gap-4">
                        <div><p class="text-gray-500 text-sm">Runtime:</p><p class="font-medium">{runtime}</p></div>
                        <div><p class="text-gray-500 text-sm">Framework:</p><p class="font-medium">{framework}</p></div>
                        <div><p class="text-gray-500 text-sm">Database:</p><p class="font-medium">{database}</p></div>
                        <div><p class="text-gray-500 text-sm">Cache:</p><p class="font-medium">{cache}</p></div>
                    </div>
                </div>
            </section>
            
            <footer class="text-center text-gray-400 text-sm mt-12">
                <p>IDP Portal | Generated by ADK Multi-Agent System</p>
            </footer>
        </main>
    </div>
    <script>
        setInterval(async () => {{
            const res = await fetch('/api/services');
            const data = await res.json();
            console.log('Services refreshed:', data.services.length);
        }}, 30000);
    </script>
</body>
</html>'''

    # Guardar archivos
    (portal_dir / "main.py").write_text(main_py_code)
    (templates_dir / "index.html").write_text(index_html_code)

    requirements_txt = """fastapi==0.109.0
uvicorn==0.27.0
jinja2==3.1.3
pyyaml==6.0.1
httpx==0.26.0
"""
    (portal_dir / "requirements.txt").write_text(requirements_txt)

    dockerfile = """FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY main.py .
COPY templates/ ./templates/
EXPOSE 8001
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
"""
    (portal_dir / "Dockerfile").write_text(dockerfile)

    # Metadata
    metadata = {
        "web_portal": {
            "framework": "FastAPI + Jinja2",
            "files_created": ["main.py", "templates/index.html", "Dockerfile", "requirements.txt"],
            "services_count": len(services),
            "created_at": datetime.utcnow().isoformat(),
            "generated_by": "Web Portal Agent (ADK)"
        }
    }

    json_path = Path(OUTPUT_DIR) / "web-portal-decisions.json"
    with open(json_path, 'w') as f:
        json.dump(metadata, f, indent=2)
        
    # Generate run-portal.sh script for easy Docker execution
    run_script = """#!/bin/bash
set -e
echo "🚀 Building Portal Docker Image..."
docker build -t idp-portal-local .

echo "🌐 Starting Portal..."
# Stop if exists
docker rm -f idp-portal-local 2>/dev/null || true

# Dynamic network detection
NETWORK_NAME=$(docker network ls --format "{{.Name}}" | grep "idp_network" | head -n 1)
if [ -z "$NETWORK_NAME" ]; then
    echo "⚠️  Network 'idp_network' not found. Using 'bridge'"
    NETWORK_NAME="bridge"
else
    echo "✅ Found network: $NETWORK_NAME"
fi

docker run -d --rm \\
    --name idp-portal-local \\
    --network "$NETWORK_NAME" \\
    -p 8001:8001 \\
    idp-portal-local

echo ""
echo "✅ Portal running at http://localhost:8001"
"""
    with open(portal_dir / "run-portal.sh", "w") as f:
        f.write(run_script)
    (portal_dir / "run-portal.sh").chmod(0o755)

    return {
        "status": "success",
        "portal_dir": str(portal_dir),
        "files_created": ["main.py", "templates/index.html", "Dockerfile", "requirements.txt", "run-portal.sh"],
        "services_count": len(services),
        "message": f"Portal generated with {len(services)} services"
    }



root_agent = Agent(
    model=os.getenv('GEMINI_MODEL', 'gemini-2.5-flash'),
    name='web_portal',
    description="Experto en desarrollo web y generación de dashboards interactivos",
    instruction="""
Eres un experto en desarrollo web y creación de dashboards para Internal Developer Platforms.

🤖 **PROTOCOLO A2A:**

Eres el 7mo (último) agente. Todos los agentes anteriores ya ejecutaron y generaron:
- Platform Architect → definió stack tecnológico
- Infrastructure Agent → generó docker-compose con todos los servicios
- Security Agent → escaneó vulnerabilidades
- CI/CD Agent → generó pipeline de Jenkins
- Observability Agent → configuró Prometheus + Grafana
- DevEx Agent → generó CLI tool

**Tu trabajo es simple:**

1. **LEE la configuración del IDP** usando `read_idp_configuration()`
   - Verás: servicios, puertos, stack tecnológico, decisiones de agentes

2. **GENERA el portal** usando `generate_portal("generate_default")`
   - Esto crea automáticamente:
     * main.py con FastAPI, health checks, endpoints para servicios
     * templates/index.html con dashboard TailwindCSS, cards de servicios
     * Dockerfile y requirements.txt
   - El portal se guarda en /app/outputs/portal/

3. **CONFIRMA** brevemente qué se generó (1-2 frases)

**IMPORTANTE:**
- Solo usa las herramientas disponibles: `read_idp_configuration` y `generate_portal`
- NO intentes generar código manualmente
- NO uses herramientas que no están listadas arriba

**Flujo exacto:**
1. Llama a read_idp_configuration()
2. Llama a generate_portal("generate_default")
3. Responde confirmando que el portal fue generado

Eso es todo. Mantén tu respuesta breve.
""",
    tools=[read_idp_configuration, generate_portal],
)

