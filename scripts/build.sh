#!/usr/bin/env bash
# exit on error
set -o errexit

pip install -r requirements.txt

# Run database migration
python migrate_db.py 