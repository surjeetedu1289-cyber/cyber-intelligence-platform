#!/usr/bin/env bash
set -e

python -m uvicorn backend.api:app --host 0.0.0.0 --port 8000 > /tmp/cip-api.log 2>&1 &
cd frontend && npm install && npm run dev -- --host 0.0.0.0 --port 3000
