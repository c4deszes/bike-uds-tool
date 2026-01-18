#!/bin/bash
set -e

echo "Upgrading pip..."
pip install --upgrade pip

echo "Installing Python package in development mode..."
cd python-lib
pip install -e ".[dev]"
cd ..

echo "Installing development tools"
pip install -r requirements.txt

echo "Installing documentation requirements..."
pip install -r docs/requirements.txt
