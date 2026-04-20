import httpx
import json
import sys

TOKEN = "rnd_2sm2Qlo3U1vMQH2fXeve0ee1OGMu"
API = "https://api.render.com/v1"
H = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}

def get(path):
    r = httpx.get(f"{API}{path}", headers=H, timeout=30)
    return r.json()

def post(path, data):
    r = httpx.post(f"{API}{path}", json=data, headers=H, timeout=30)
    return r.json()

OWNER_ID = "tea-d7j25r9f9bms738fjes0"

# Создать Background Worker
print("Creating service...")
service_data = {
    "type": "web_service",
    "name": "hot-makler-bot",
    "ownerId": OWNER_ID,
    "repo": "https://github.com/artemkolomiec95-sketch/hot-makler-bot",
    "branch": "master",
    "plan": "free",
    "serviceDetails": {
        "runtime": "python",
        "plan": "free",
        "envSpecificDetails": {
            "buildCommand": "pip install -e .",
            "startCommand": "python -m src.bot.main",
        },
    },
    "envVars": [
        {"key": "BOT_TOKEN",                  "value": "8629576368:AAGlgihzgHy8l4Po0RdUi6SWiIBSK3p0hCw"},
        {"key": "REALTOR_TG_ID",              "value": "5243807348"},
        {"key": "WHATSAPP_PROVIDER",          "value": "telegram"},
        {"key": "SHEETS_SYNC_INTERVAL_HOURS", "value": "8"},
        {"key": "ENV",                        "value": "production"},
        {"key": "GOOGLE_SHEETS_ID",           "value": ""},
        {"key": "PYTHON_VERSION",             "value": "3.11.0"},
    ],
}
result = post("/services", service_data)
print(json.dumps(result, indent=2))
