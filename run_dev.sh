#!/bin/bash
# Development server startup script for Crypto Quant Laboratory
./venv/Scripts/uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
