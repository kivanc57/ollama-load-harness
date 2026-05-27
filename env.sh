#!/bin/bash
set -euo pipefail

# Ollama concurrency settings
# Docs: https://docs.ollama.com/faq

# Maximum number of parallel requests each loaded model can process
export OLLAMA_NUM_PARALLEL=4

# Maximum number of models loaded concurrently, if memory/VRAM allows
export OLLAMA_MAX_LOADED_MODELS=2

# Maximum number of queued requests before Ollama rejects new ones
export OLLAMA_MAX_QUEUE=128

#=====================================================================

# Project env variables

export API_URL="http://localhost:11434/api/generate"

export HOST_ID="${HOSTNAME}"

export MONITORING_SCOPE="ollama_host_local"

export USER_AMOUNT=5

export LLM_MODEL="llama3.1:8b"

