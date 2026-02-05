#!/usr/bin/env python3
"""
ORCHESTRATOR - Google ADK Sequential Agent
===========================================

Coordina la ejecución secuencial de los 7 agentes usando Google ADK SequentialAgent:
1. Platform Architect → Decide arquitectura
2. Infrastructure → Genera docker-compose
3. Security → Analiza seguridad
4. CI/CD → Genera scripts
5. Observability → Genera dashboards
6. DevEx → Genera CLI tool
7. Web Portal → Genera portal web completo

Author: Nicolás Neira
Web: https://nicolasneira.com
YouTube: https://www.youtube.com/@NicolasNeiraGarcia?sub_confirmation=1
Email: hola@nicolasneira.com
Date: 2026-01-18 (V2 - ADK SequentialAgent)
"""

import os
import sys
from pathlib import Path
from datetime import datetime

# Add /app to Python path to find agents_adk module
sys.path.insert(0, '/app')

# ANSI Colors for demo mode
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    RESET = '\033[0m'

# Agent colors and emojis
AGENT_STYLES = {
    'platform_architect': {'emoji': '🏗️', 'color': Colors.CYAN, 'name': 'Platform Architect'},
    'infrastructure': {'emoji': '🐳', 'color': Colors.BLUE, 'name': 'Infrastructure'},
    'security': {'emoji': '🔐', 'color': Colors.RED, 'name': 'Security'},
    'cicd': {'emoji': '🔄', 'color': Colors.YELLOW, 'name': 'CI/CD'},
    'observability': {'emoji': '📊', 'color': Colors.GREEN, 'name': 'Observability'},
    'devex': {'emoji': '💻', 'color': Colors.CYAN, 'name': 'DevEx'},
    'web_portal': {'emoji': '🌐', 'color': Colors.HEADER, 'name': 'Web Portal'},
}

# Demo mode logging functions
def get_logs_dir():
    """Get logs directory path."""
    output_dir = os.getenv('ADK_OUTPUT_DIR', './test-outputs')
    logs_dir = Path(output_dir) / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    return logs_dir

def init_demo_logs():
    """Initialize all log files for demo mode."""
    logs_dir = get_logs_dir()
    
    # Create individual log files for each agent
    log_files = [
        'a2a-messages.log',
        'output.log',
        'platform-architect.log',
        'infrastructure.log',
        'security.log',
        'cicd.log',
        'observability.log',
        'devex.log',
        'web-portal.log',
        'files.log',
    ]
    
    for log_file in log_files:
        log_path = logs_dir / log_file
        with open(log_path, 'w') as f:
            f.write(f"# {log_file} - Started at {datetime.now().isoformat()}\n")
            f.write("=" * 60 + "\n\n")

def log_agent(agent_name: str, message: str, is_reasoning: bool = False):
    """Write to agent-specific log file."""
    logs_dir = get_logs_dir()
    
    # Map agent names to individual log files
    agent_log_map = {
        'platform_architect': 'platform-architect.log',
        'infrastructure': 'infrastructure.log',
        'security': 'security.log',
        'cicd': 'cicd.log',
        'observability': 'observability.log',
        'devex': 'devex.log',
        'web_portal': 'web-portal.log',
    }
    
    log_file = agent_log_map.get(agent_name, 'output.log')
    log_path = logs_dir / log_file
    
    style = AGENT_STYLES.get(agent_name, {'emoji': '🤖', 'color': Colors.RESET, 'name': agent_name})
    
    timestamp = datetime.now().strftime("%H:%M:%S")
    prefix = "🤔 " if is_reasoning else "📝 "
    
    with open(log_path, 'a') as f:
        f.write(f"[{timestamp}] {prefix}{message}\n")
        f.flush()

def log_a2a(from_agent: str, to_agent: str, message: str):
    """Write to A2A messages log."""
    logs_dir = get_logs_dir()
    log_path = logs_dir / 'a2a-messages.log'
    
    from_style = AGENT_STYLES.get(from_agent, {'emoji': '🤖', 'name': from_agent})
    to_style = AGENT_STYLES.get(to_agent, {'emoji': '🤖', 'name': to_agent})
    
    timestamp = datetime.now().strftime("%H:%M:%S")
    
    with open(log_path, 'a') as f:
        f.write(f"[{timestamp}] [{from_style['emoji']} {from_style['name']} → {to_style['emoji']} {to_style['name']}]\n")
        f.write(f"    📨 {message}\n\n")
        f.flush()

def log_output(message: str):
    """Write to output log."""
    logs_dir = get_logs_dir()
    log_path = logs_dir / 'output.log'
    
    timestamp = datetime.now().strftime("%H:%M:%S")
    
    with open(log_path, 'a') as f:
        f.write(f"[{timestamp}] {message}\n")
        f.flush()

# Google ADK imports
try:
    from google.adk.agents import SequentialAgent, Agent
    from google.adk.runners import Runner
    from google.adk.sessions import InMemorySessionService
    from google.genai import types
except ImportError as e:
    print(f"ERROR: Google ADK not installed. Run: pip install 'google-adk[a2a]>=1.22.0'")
    print(f"Details: {e}")
    sys.exit(1)

# Import the 7 agents
from agents_adk import platform_architect_adk
from agents_adk.infrastructure.agent import root_agent as infrastructure_agent
from agents_adk.security.agent import root_agent as security_agent
from agents_adk.cicd.agent import root_agent as cicd_agent
from agents_adk.observability.agent import root_agent as observability_agent
from agents_adk.devex.agent import root_agent as devex_agent
from agents_adk.web_portal.agent import root_agent as web_portal_agent


# Create the orchestrator using SequentialAgent
orchestrator = SequentialAgent(
    name="idp_orchestrator",  # Must be valid identifier (no spaces)
    description="Coordina 7 agentes especializados para construir un Internal Developer Platform completo usando Google ADK SequentialAgent con protocolo A2A",
    sub_agents=[
        platform_architect_adk.agent,  # 1. Platform Architect (decide arquitectura)
        infrastructure_agent,           # 2. Infrastructure (genera docker-compose)
        security_agent,                 # 3. Security (analiza vulnerabilidades)
        cicd_agent,                     # 4. CI/CD (genera scripts)
        observability_agent,            # 5. Observability (prometheus + grafana)
        devex_agent,                    # 6. DevEx (CLI tool)
        web_portal_agent,               # 7. Web Portal (FastAPI portal) - DEBE IR AL FINAL
    ],
    # SequentialAgent no acepta 'instruction', solo name, description, sub_agents
)


# Main execution function
async def run_orchestrator(task: str = "Build an Internal Developer Platform", demo_mode: bool = True):
    """
    Ejecuta el orchestrator con la tarea especificada.

    Args:
        task: Descripción de la tarea a realizar
        demo_mode: Si True, escribe logs separados para visualización

    Returns:
        Resultado de la ejecución de los 7 agentes
    """
    # Initialize demo logs if demo mode
    if demo_mode:
        init_demo_logs()
        log_output("🚀 ORCHESTRATOR INICIANDO")
        log_output(f"📋 Tarea: {task}")
    
    print(f"🚀 ORCHESTRATOR INICIANDO (LOCAL CODE LOADED - NO LOG LIMITS)")
    print(f"📋 Tarea: {task}")
    print(f"🤖 Modelo: {os.getenv('GEMINI_MODEL', 'gemini-2.5-flash')}")
    print(f"📁 Output: {os.getenv('ADK_OUTPUT_DIR', './test-outputs')}")
    print("=" * 80)

    # Guardar task en archivo para que Platform Architect pueda leerlo
    output_dir = os.getenv('ADK_OUTPUT_DIR', './test-outputs')
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    task_file = Path(output_dir) / "user-task.txt"
    with open(task_file, 'w') as f:
        f.write(task)

    # Enriquecer el task con contexto completo para ejecución autónoma
    enhanced_task = f"""{task}

🤖 **PROTOCOLO A2A (Agent-to-Agent) - Modo Colaborativo**

Eres parte de un SequentialAgent que ejecuta 7 agentes especializados en secuencia.
Cada agente puede ver las decisiones y outputs de los agentes anteriores en esta conversación.

**Lista de los 7 agentes (TODOS deben ejecutar):**
1. Platform Architect → Decide stack tecnológico
2. Infrastructure → Genera docker-compose
3. Security → Escanea vulnerabilidades
4. CI/CD → Genera scripts y Jenkins
5. Observability → Configura Prometheus + Grafana
6. DevEx → Genera CLI tool
7. Web Portal → Genera dashboard web (ÚLTIMO agente)

**Cómo funciona A2A:**
1. Cada agente LEE el contexto de agentes anteriores
2. RAZONA sobre qué hacer basándose en ese contexto
3. EXPLICA brevemente su razonamiento (1-2 frases)
4. EJECUTA las herramientas necesarias

**Herramientas disponibles:**
- Cada agente tiene funciones específicas para guardar sus decisiones
- Cada agente puede leer configuraciones de agentes anteriores usando get_platform_config()

**Reglas:**
- SÍ puedes razonar y explicar tu pensamiento
- NO preguntes al usuario (modo autónomo)
- Ejecuta tus herramientas después de razonar
- Sé breve: razonamiento en 1-2 frases, luego ejecuta

**CRÍTICO para Platform Architect:**
Llama a save_platform_config() con el stack_summary completo:

save_platform_config(stack_summary="Runtime: X | Framework: Y | Database: Z | Cache: W | Monitoring: M | Security: S | CI/CD: C | Deployment: D | Environment: E")

La función leerá automáticamente el user task del archivo para detectar capabilities de self-service.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Comienza ahora. El primer agente (Platform Architect) debe razonar sobre el task y decidir el stack."""

    # Setup session service and runner (official ADK pattern)
    APP_NAME = "idp_orchestrator_app"
    USER_ID = "idp_user"
    SESSION_ID = "idp_session_001"

    session_service = InMemorySessionService()

    # Create runner with correct parameters
    runner = Runner(
        agent=orchestrator,
        app_name=APP_NAME,
        session_service=session_service
    )

    # Create session
    session = await session_service.create_session(
        app_name=APP_NAME,
        user_id=USER_ID,
        session_id=SESSION_ID
    )

    print(f"✅ Session creada: {session.id}")
    print(f"🔄 Ejecutando SequentialAgent con 7 sub-agentes...")
    print()
    
    if demo_mode:
        log_output(f"✅ Session creada: {session.id}")
        log_output("🔄 Ejecutando SequentialAgent con 7 sub-agentes...")

    # Prepare user message with enhanced context
    user_message = types.Content(
        role="user",
        parts=[types.Part(text=enhanced_task)]
    )

    # Track agent order for A2A messages
    agent_order = ['platform_architect', 'infrastructure', 'security', 'cicd', 'observability', 'devex', 'web_portal']
    last_agent = None

    # Execute orchestrator
    final_result = None
    for event in runner.run(
        user_id=USER_ID,
        session_id=SESSION_ID,
        new_message=user_message
    ):
        # Print events from each sub-agent
        if hasattr(event, 'author') and hasattr(event, 'content'):
            current_agent = event.author
            
            if event.content and hasattr(event.content, 'parts') and event.content.parts:
                # Extract text and function_call parts separately
                text_parts = []
                function_calls = []
                
                for part in event.content.parts:
                    if hasattr(part, 'text') and part.text:
                        text_parts.append(part.text)
                    elif hasattr(part, 'function_call') and part.function_call:
                        fc = part.function_call
                        func_name = fc.name if hasattr(fc, 'name') else str(fc)
                        function_calls.append(func_name)

                # Log function calls (tool usage)
                if function_calls and demo_mode:
                    for func_name in function_calls:
                        log_agent(current_agent, f"🔧 Ejecutando: {func_name}()")
                        print(f"🔧 [{current_agent}]: Ejecutando {func_name}()")

                # SIEMPRE loggear texto, no solo cuando hay function_calls
                combined_text = " ".join(text_parts)
                if combined_text.strip():
                    print(f"📤 [{current_agent}]: {combined_text}")
                    
                    # Demo mode logging
                    if demo_mode:
                        # Detect type of message
                        text_lower = combined_text.lower()
                        if "razon" in text_lower or "anali" in text_lower or "leo" in text_lower or "leyendo" in text_lower:
                            log_agent(current_agent, combined_text, is_reasoning=True)
                        else:
                            log_agent(current_agent, combined_text)
                        
                        # Log A2A message when agent changes
                        if last_agent and last_agent != current_agent:
                            # Create A2A summary message
                            log_a2a(last_agent, current_agent, f"Pasando contexto: {combined_text}")
                        
                        last_agent = current_agent

        # Check if final response
        if hasattr(event, 'is_final_response') and event.is_final_response():
            if event.content:
                final_result = event.content
                print(f"\n✅ Respuesta final de [{event.author}]")
                
                if demo_mode:
                    log_agent(event.author, f"✅ COMPLETADO")
                    log_output(f"✅ Respuesta final de [{event.author}]")
                
                if event.content.parts:
                    # Extract text parts only
                    text_parts = []
                    for part in event.content.parts:
                        if hasattr(part, 'text') and part.text:
                            text_parts.append(part.text)
                    if text_parts:
                        print(f"📊 Output: {text_parts[0]}")
                        if demo_mode:
                            log_output(f"📊 Output: {text_parts[0]}")

        # Check for errors
        if hasattr(event, 'is_error') and event.is_error():
            error_msg = event.error_details if hasattr(event, 'error_details') else 'Unknown error'
            print(f"❌ Error: {error_msg}")
            if demo_mode:
                log_output(f"❌ Error: {error_msg}")

    print()
    print("=" * 80)
    print("✅ ORCHESTRATOR COMPLETADO")
    
    if demo_mode:
        log_output("=" * 60)
        log_output("✅ ORCHESTRATOR COMPLETADO")
        log_a2a('web_portal', 'orchestrator', "IDP generado exitosamente. Portal listo.")

    return final_result


# Export orchestrator for CLI usage
agent = orchestrator


if __name__ == "__main__":
    import asyncio

    # Get task from command line or use default
    task = sys.argv[1] if len(sys.argv) > 1 else "Build an Internal Developer Platform"

    # Run orchestrator
    result = asyncio.run(run_orchestrator(task))

    print("\n✅ IDP generado exitosamente!")
    print(f"📁 Revisa los archivos en: {os.getenv('ADK_OUTPUT_DIR', './test-outputs')}")
