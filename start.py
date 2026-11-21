import subprocess
import sys

from src.setup import ensure_ready

status = ensure_ready()
if status["database_built"]:
    print("Built the database from the JSON file.")
if status["search_index_built"]:
    print("Built the document search (the first time it downloads a small model).")

print("Starting the chat screen...")
subprocess.run([sys.executable, "-m", "streamlit", "run", "ui/app.py"])