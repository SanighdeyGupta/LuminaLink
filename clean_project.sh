#!/bin/bash

# Remove __pycache__ directories
find . -name "__pycache__" -exec rm -r {} +

# Remove migrations except __init__.py
find . -path "*/migrations/*.py" ! -name "__init__.py" -delete
find . -path "*/migrations/*.pyc" -delete

# Remove sqlite database file
rm db.sqlite3
