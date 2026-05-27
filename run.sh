#!/bin/bash
set -euo pipefail

source venv/bin/activate
source ./env.sh
python -m src.main

