import requests
import os
import sys
import json

def check_step(name, status, details=""):
    symbol = "✅" if status else "❌"
    print(f"{symbol} {name}: {details}")

print("\n🚀 ORBIS ETHICA - PROGRESS CHECK\n" + "="*40)

# 1. Check Server
try:
    r = requests.get("http://localhost:8000/health", timeout=2)
    check_step("Backend Server", r.status_code == 200, f"Running (Status: {r.json().get('status')})")
except:
    check_step("Backend Server", False, "Not responding (Is ./start.sh running?)")

# 2. Check Data
if os.path.exists("data/training_data.jsonl"):
    count = sum(1 for line in open("data/training_data.jsonl"))
    check_step("Training Data", count > 0, f"Ready ({count} examples unified)")
else:
    check_step("Training Data", False, "File not found")

# 3. Check SDK
try:
    sys.path.append(os.getcwd())
    from sdk.orbis import Orbis
    check_step("SDK Client", True, "Importable (Ready for integration)")
except ImportError as e:
    check_step("SDK Client", False, f"Import Failed: {e}")

# 4. Check Notebook
if os.path.exists("train_orbis.ipynb"):
    check_step("Training Notebook", True, "Created (Ready for Colab)")
else:
    check_step("Training Notebook", False, "Missing")

print("="*40 + "\n")
