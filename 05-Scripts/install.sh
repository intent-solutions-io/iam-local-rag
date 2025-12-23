#!/usr/bin/env bash
set -euo pipefail

echo "🔧 NEXUS installer starting…"

# Detect OS
OS="$(uname -s)"
PY="python3"
if ! command -v $PY >/dev/null 2>&1; then
  echo "❌ python3 not found. Please install Python 3.9+ and re-run."; exit 1
fi

# Create venv
$PY -m venv venv
if [ -f "venv/bin/activate" ]; then
  source venv/bin/activate
else
  source venv/Scripts/activate
fi

# Pip upgrade + deps
python -m pip install --upgrade pip
if [ -f "requirements.txt" ]; then
  pip install -r requirements.txt
else
  echo "⚠️ requirements.txt not found. Creating a minimal one…"
  cat > requirements.txt <<'REQ'
streamlit>=1.36.0
langchain>=0.2.16
chromadb>=0.5.5
pypdf>=4.3.1
requests>=2.32.3
REQ
  pip install -r requirements.txt
fi

# Ollama install (skip if present)
if ! command -v ollama >/dev/null 2>&1; then
  echo "⬇️ Installing Ollama…"
  curl -fsSL https://ollama.ai/install.sh | sh
fi

# Pull a default local model
ollama pull llama3 || true

echo "✅ Install complete."
echo "➡️ Start your app with: streamlit run app.py"