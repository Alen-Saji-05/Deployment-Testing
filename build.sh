#!/usr/bin/env bash
# Render build script
set -o errexit

pip install -r requirements.txt

# Initialize/upgrade database
python -c "from app import app, db; app.app_context().push(); db.create_all()"

echo "Build complete!"
