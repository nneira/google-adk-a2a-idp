#!/usr/bin/env python3
"""
DEVEX AGENT - ADK Interactive Mode
===================================

Genera CLI tool para el IDP de forma conversacional.
Crea un comando `idp` que facilita el uso de la plataforma.

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


def save_cli_tool(cli_summary: str = "generate_default") -> dict:
    """
    Guarda el CLI tool generado.

    Args:
        cli_summary: Resumen en formato:
            "SCRIPT: [contenido script bash] | README: [contenido README.md] | COMMANDS: init,build,test,deploy,status,logs,help"
            O simplemente "generate_default" para generar CLI tool por defecto.

    Returns:
        dict: Confirmación de guardado
    """
    # Leer paths dinámicos desde JSON files
    docker_compose_path = "docker-compose.yml"  # default fallback
    cicd_dir = "cicd"  # default fallback

    infra_json = Path(OUTPUT_DIR) / "infrastructure-decisions.json"
    if infra_json.exists():
        with open(infra_json, 'r') as f:
            infra_data = json.load(f)
            files_gen = infra_data.get('files_generated', {})
            if 'docker_compose' in files_gen:
                docker_compose_path = files_gen['docker_compose']

    # Si pide default, generar CLI tool completo
    if cli_summary == "generate_default" or not cli_summary or len(cli_summary) < 100:
        cli_script = f"""#!/bin/bash
set -e

# Colors
GREEN='\\033[0;32m'
RED='\\033[0;31m'
YELLOW='\\033[1;33m'
NC='\\033[0;m'

case "$1" in
  init)
    echo -e "${{GREEN}}🚀 Initializing IDP project...${{NC}}"
    mkdir -p app tests config
    echo "IDP project initialized"
    ;;
  build)
    echo -e "${{GREEN}}🔨 Building IDP...${{NC}}"
    bash {cicd_dir}/build.sh
    ;;
  test)
    echo -e "${{GREEN}}🧪 Running tests...${{NC}}"
    bash {cicd_dir}/test.sh
    ;;
  deploy)
    echo -e "${{GREEN}}🚀 Deploying IDP...${{NC}}"
    bash {cicd_dir}/deploy.sh
    ;;
  status)
    echo -e "${{YELLOW}}📊 IDP Status:${{NC}}"
    docker-compose -f {docker_compose_path} ps
    ;;
  logs)
    if [ -z "$2" ]; then
      docker-compose -f {docker_compose_path} logs -f
    else
      docker-compose -f {docker_compose_path} logs -f "$2"
    fi
    ;;
  up)
    echo -e "${{GREEN}}⬆️  Starting services...${{NC}}"
    docker-compose -f {docker_compose_path} up -d
    ;;
  down)
    echo -e "${{YELLOW}}⬇️  Stopping services...${{NC}}"
    docker-compose -f {docker_compose_path} down
    ;;
  scan)
    echo -e "${{YELLOW}}🔍 Running security scan...${{NC}}"
    trivy fs --severity CRITICAL,HIGH,MEDIUM .
    ;;
  help)
    echo "IDP CLI Tool"
    echo ""
    echo "Usage: idp [command]"
    echo ""
    echo "Commands:"
    echo "  init    - Initialize new IDP project"
    echo "  build   - Build Docker images"
    echo "  test    - Run tests"
    echo "  deploy  - Deploy services"
    echo "  status  - Show service status"
    echo "  logs    - Show logs (optional: service name)"
    echo "  up      - Start all services"
    echo "  down    - Stop all services"
    echo "  scan    - Run security scan"
    echo "  help    - Show this help"
    ;;
  *)
    echo -e "${{RED}}Unknown command: $1${{NC}}"
    echo "Use 'idp help' for usage information"
    exit 1
    ;;
esac
"""
        readme = """# IDP CLI Tool

Command-line interface for managing your Internal Developer Platform.

## Installation

```bash
chmod +x cli-tool/idp
export PATH=$PATH:$(pwd)/cli-tool
```

## Commands

- `idp init` - Initialize new IDP project
- `idp build` - Build Docker images
- `idp test` - Run tests
- `idp deploy` - Deploy services
- `idp status` - Show service status
- `idp logs [service]` - Show logs (optional: filter by service)
- `idp up` - Start all services
- `idp down` - Stop all services
- `idp scan` - Run security scan with Trivy
- `idp help` - Show help

## Examples

```bash
# Deploy the platform
idp deploy

# Check status
idp status

# View app logs
idp logs app

# Run security scan
idp scan
```

## Troubleshooting

- If `docker-compose` commands fail, ensure Docker is running
- For permission errors, run `chmod +x cli-tool/idp`
- Check logs with `idp logs` to debug service issues
"""
        commands = "init,build,test,deploy,status,logs,help,up,down,scan"
    else:
        parts = {}
        sections = cli_summary.split('| ')
        for section in sections:
            if ':' in section:
                key, value = section.split(':', 1)
                parts[key.strip().upper()] = value.strip()

        cli_script = parts.get('SCRIPT', '#!/bin/bash\necho "IDP CLI"\n')
        readme = parts.get('README', '# IDP CLI Tool\n\nTODO: Add documentation\n')
        commands = parts.get('COMMANDS', 'init,build,test,deploy,help')

    cli_dir = Path(OUTPUT_DIR) / "cli-tool"
    cli_dir.mkdir(parents=True, exist_ok=True)

    # Guardar CLI script
    cli_path = cli_dir / "idp"
    with open(cli_path, 'w') as f:
        f.write(cli_script)
    cli_path.chmod(0o755)

    # Guardar README
    readme_path = cli_dir / "README.md"
    with open(readme_path, 'w') as f:
        f.write(readme)

    # Metadata
    metadata = {
        "devex": {
            "cli_tool": "idp",
            "created_at": datetime.utcnow().isoformat(),
            "generated_by": "DevEx Agent (ADK Interactive)"
        },
        "commands": {
            "description": commands
        },
        "metadata": {
            "ai_model": "gemini-2.5-flash",
            "decision_timestamp": datetime.utcnow().isoformat()
        }
    }

    json_path = Path(OUTPUT_DIR) / "devex-decisions.json"
    with open(json_path, 'w') as f:
        json.dump(metadata, f, indent=2)

    return {
        "status": "success",
        "cli_path": str(cli_path),
        "readme_path": str(readme_path),
        "commands": commands
    }


def get_platform_config() -> dict:
    """Lee la configuración de plataforma."""
    config_path = Path(OUTPUT_DIR) / "platform-config.yaml"

    if not config_path.exists():
        return {"error": "Platform config no encontrado"}

    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)

    return {
        "status": "success",
        "config": config,
        "framework": config['stack']['framework']
    }


root_agent = Agent(
    model=os.getenv('GEMINI_MODEL', 'gemini-2.5-flash'),
    name='devex',
    description="Experto en Developer Experience y diseño de herramientas CLI",
    instruction="""
Eres un experto en Developer Experience y diseño de herramientas CLI.

🤖 **PROTOCOLO A2A - Razonamiento Colaborativo:**

Eres el 6to agente en la cadena. Los agentes anteriores ya completaron:
- Platform Architect: decidió el stack
- Security, Infrastructure, CI/CD, Observability: generaron sus configuraciones y scripts

**Tu trabajo es simple:**

1. **LEE** la configuración usando `get_platform_config()` para entender el stack

2. **GENERA** el CLI tool ejecutando `save_cli_tool("generate_default")`
   - Esto crea automáticamente un CLI completo con comandos:
     * init, build, test, deploy, status, logs, up, down, scan, help
   - El CLI se guarda en /app/outputs/cli-tool/idp

3. **CONFIRMA** brevemente qué se generó (1-2 frases)

**IMPORTANTE:**
- Solo usa las herramientas disponibles: `get_platform_config` y `save_cli_tool`
- NO intentes crear scripts adicionales ni ejecutar código
- NO uses herramientas que no están listadas arriba
- Tu trabajo es generar el CLI tool, nada más

**Flujo exacto:**
1. Llama a get_platform_config()
2. Llama a save_cli_tool("generate_default")
3. Responde confirmando que el CLI fue creado

Eso es todo. Mantén tu respuesta breve.
""",
    tools=[save_cli_tool, get_platform_config],
)
