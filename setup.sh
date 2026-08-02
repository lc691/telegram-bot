#!/bin/bash

echo "🗑️  Removing old .venv..."
deactivate 2>/dev/null
rm -rf .venv

echo "🆕 Creating new .venv..."
python3 -m venv .venv

echo "📦 Activating..."
source .venv/bin/activate

echo "⬆️  Upgrading pip..."
pip install --upgrade pip setuptools wheel

echo "📦 Installing dependencies..."
pip install -r requirements.txt 2>/dev/null || echo "⚠️  No requirements.txt found"

echo "✅ Done! Virtual environment is ready."
echo "📌 Activate with: source .venv/bin/activate"
