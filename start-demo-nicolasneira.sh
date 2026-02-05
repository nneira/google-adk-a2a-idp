#!/bin/bash
# Demo Mode Simple - Sin tmux, tú controlas las terminales
# Uso: ./start-demo-simple.sh ["TASK"]

set -e

# Cargar variables de entorno
set -a
source .env 2>/dev/null || true
set +a

TASK="${1:-Build complete IDP with CI/CD, monitoring, security, and self-service}"
GEMINI_MODEL="${GEMINI_MODEL:-gemini-2.5-flash}"
OUTPUT_DIR="test-outputs/idp-adk-sequential"
LOGS_DIR="$OUTPUT_DIR/logs"


# Limpiar outputs anteriores
rm -rf "$OUTPUT_DIR"
mkdir -p "$LOGS_DIR"

# Crear archivos de log vacíos
touch "$LOGS_DIR/a2a-messages.log"
touch "$LOGS_DIR/output.log"
touch "$LOGS_DIR/platform-architect.log"
touch "$LOGS_DIR/infrastructure.log"
touch "$LOGS_DIR/security.log"
touch "$LOGS_DIR/cicd.log"
touch "$LOGS_DIR/observability.log"
touch "$LOGS_DIR/devex.log"
touch "$LOGS_DIR/web-portal.log"

echo ""
echo "============================================================"
echo ""
echo "  Suscribete aqui:"
echo "  https://www.youtube.com/@NicolasNeiraGarcia?sub_confirmation=1"
echo ""
echo "============================================================"
echo ""
echo "Para ver los logs en tiempo real, abre otra terminal y ejecuta:"
echo ""
echo "  tail -f test-outputs/idp-adk-sequential/logs/*.log"
echo ""
echo "============================================================"
echo ""
read -p "Presiona ENTER para iniciar los 7 agentes..."

echo "🚀 Iniciando ejecución de agentes..."
echo ""

docker run --rm \
  --user root \
  -e GEMINI_API_KEY="$GEMINI_API_KEY" \
  -e GEMINI_MODEL="$GEMINI_MODEL" \
  -e ADK_OUTPUT_DIR="/app/outputs" \
  -v "$(pwd)/$OUTPUT_DIR:/app/outputs" \
  -v "$(pwd)/agents_adk:/app/agents_adk" \
  -v /var/run/docker.sock:/var/run/docker.sock \
  adk-agents:hybrid \
  python agents_adk/orchestrator_adk.py "$TASK"

echo ""
echo "✅ COMPLETADO"
