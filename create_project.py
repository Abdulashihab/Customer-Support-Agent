# create_project.py
# This script ONLY creates folders. Nothing else.
# Run it inside your project folder:   python create_project.py

import os

folders = [
    "data",          # your JSON data goes here
    "docs",          # help documents (.md files)
    "ui",            # chat screen
    "tests",         # tests
    "src/db",        # database code
    "src/tools",     # tools: get_account, add_channel ...
    "src/rag",       # document search
    "src/agent",     # the bot brain (LangGraph)
    "src/auth",      # login and OTP
]

for folder in folders:
    os.makedirs(folder, exist_ok=True)   # exist_ok=True means: no error if it already exists
    print("created:", folder)

print("Done.")