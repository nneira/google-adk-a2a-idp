#!/bin/bash
# ============================================================
# MODO INTERACTIVO - IDP Multi-Agente con ADK
# ============================================================
#
# Uso: ./start-interactive-nicolasneira.sh [MODEL]
#
# Ejemplos:
#   ./start-interactive-nicolasneira.sh                      # Usa gemini-2.5-flash (default)
#   ./start-interactive-nicolasneira.sh gemini-2.5-flash     # Modelo recomendado
#
# Qué hace:
#   - Levanta la UI web de ADK en http://localhost:8000
#   - Muestra los 7 agentes en el sidebar
#   - Los archivos se guardan en test-outputs/idp-fastapi/
#
# ============================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

GEMINI_MODEL="${1:-gemini-2.5-flash}"

# Leer API key desde .env
if [ -f ".env" ]; then
    API_KEY=$(grep GEMINI_API_KEY .env | cut -d'=' -f2)
else
    echo "❌ Error: .env no encontrado"
    echo "💡 Copia .env.example a .env y configura GEMINI_API_KEY"
    exit 1
fi

if [ -z "$API_KEY" ]; then
    echo "❌ Error: GEMINI_API_KEY no configurada en .env"
    exit 1
fi

# Detener contenedor existente si está corriendo
docker stop platform_architect_interactive 2>/dev/null || true
docker rm platform_architect_interactive 2>/dev/null || true

echo "============================================================"
echo "🚀 MODO INTERACTIVO - IDP Multi-Agente"
echo "============================================================"
echo ""
echo "📁 Output:    test-outputs/idp-fastapi/"
echo "🌐 URL:       http://localhost:8000"
echo "🤖 Model:     $GEMINI_MODEL"
echo ""
echo "============================================================"

# Iniciar contenedor
docker run --rm -d \
  --name platform_architect_interactive \
  -e GOOGLE_API_KEY="$API_KEY" \
  -e GEMINI_API_KEY="$API_KEY" \
  -e GEMINI_MODEL="$GEMINI_MODEL" \
  -e ADK_OUTPUT_DIR="/app/outputs" \
  -v "$(pwd)/test-outputs/idp-fastapi:/app/outputs" \
  -p 8000:8000 \
  adk-agents:hybrid \
  adk web --host 0.0.0.0 --port 8000 /app/agents_adk

echo ""
echo "✅ Contenedor iniciado!"
echo ""
echo "💡 Abre http://localhost:8000 en tu navegador"
echo ""
echo "📝 Comandos útiles:"
echo "   docker logs -f platform_architect_interactive    # Ver logs"
echo "   docker exec -it platform_architect_interactive bash  # Entrar al contenedor"
echo "   docker stop platform_architect_interactive       # Detener"
echo ""
echo "============================================================"
echo ""
echo "  Suscribete aqui:"
echo "  https://www.youtube.com/@NicolasNeiraGarcia?sub_confirmation=1"
echo ""
echo "============================================================"
