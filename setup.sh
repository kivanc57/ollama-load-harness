#!/bin/bash
set -euo pipefail

if [ ! -d "venv" ]; then
    python -m venv venv
fi

python -m venv venv
source venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

