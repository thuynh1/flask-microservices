#!/bin/bash

# Configuration
APP_MODULE="app:create_app()" # Format: module:variable (e.g., app.py with 'app' Flask instance)
WORKERS=4                     # Number of Gunicorn worker processes
BIND_ADDRESS="[::]:6789"      # Address and port to bind

echo "Starting Gunicorn for $APP_MODULE on $BIND_ADDRESS with $WORKERS workers..."

exec gunicorn --workers="$WORKERS" --bind="$BIND_ADDRESS" "$APP_MODULE"