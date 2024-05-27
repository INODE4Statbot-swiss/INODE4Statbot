#!/bin/bash
python3 prepareserver.py
python3 initserver.py
gunicorn server:app --bind :5000 --log-level=debug --workers=4 --timeout 300