import json
import urllib.request

URL = "https://openrouter.ai/api/v1/models"

with urllib.request.urlopen(URL, timeout=30) as response:
    models = json.load(response)["data"]

print("Free models that support tool calling:\n")
for model in models:
    pricing = model.get("pricing", {})
    is_free = str(pricing.get("prompt")) == "0" and str(pricing.get("completion")) == "0"
    has_tools = "tools" in (model.get("supported_parameters") or [])
    if is_free and has_tools:
        print(f"{model['id']}   (context: {model.get('context_length')})")