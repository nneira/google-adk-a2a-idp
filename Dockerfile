# Dockerfile for IDP Multi-Agent System
# 7 AI Agents using Google ADK + A2A Protocol

FROM python:3.11-slim

LABEL maintainer="Nicolas Neira <hola@nicolasneira.com>"
LABEL description="IDP Multi-Agent System - 7 AI Agents (Google ADK + Gemini 2.5 Flash)"

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN useradd -m -u 1000 agent && \
    mkdir -p /app /app/outputs && \
    chown -R agent:agent /app

WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy ADK agents
COPY agents_adk/ ./agents_adk/

# Fix permissions
RUN chown -R agent:agent /app

# Switch to non-root user
USER agent

# Expose port for ADK Dev UI
EXPOSE 8000

# Default: ADK web UI
CMD ["adk", "web", "--host", "0.0.0.0", "--port", "8000", "/app/agents_adk"]
