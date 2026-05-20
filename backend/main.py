import os
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
import requests

from config import *
from db import add_business
from services.router import route_business
from services.processor import process_message
from services.whatsapp import send_message

app = FastAPI()

FRONTEND_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "frontend", "index.html"
)


# -----------------------------
# SERVE FRONTEND
# -----------------------------
@app.get("/", response_class=HTMLResponse)
async def index():
    with open(FRONTEND_PATH, encoding="utf-8") as f:
        return HTMLResponse(f.read())


# -----------------------------
# FRONTEND CONFIG
# -----------------------------
@app.get("/api/config")
async def get_config():
    return {"app_id": APP_ID, "config_id": CONFIG_ID}


# -----------------------------
# WEBHOOK VERIFY (META REQUIRES)
# -----------------------------
@app.get("/webhook")
async def verify(request: Request):
    params = request.query_params

    if params.get("hub.verify_token") == VERIFY_TOKEN:
        return int(params.get("hub.challenge"))

    return "invalid token"


# -----------------------------
# RECEIVE MESSAGES
# -----------------------------
@app.post("/webhook")
async def webhook(request: Request):

    data = await request.json()
    print("RAW:", data)

    try:
        entry = data["entry"][0]["changes"][0]["value"]

        # ---------------- STATUS UPDATES ----------------
        if "statuses" in entry:
            print("STATUS:", entry["statuses"][0]["status"])
            return {"ok": True}

        # ---------------- MESSAGES ----------------
        if "messages" not in entry:
            return {"ok": True}

        msg = entry["messages"][0]
        text = msg["text"]["body"]
        from_number = msg["from"]

        phone_number_id = entry["metadata"]["phone_number_id"]

        # route business
        business = route_business(phone_number_id)

        if not business:
            print("Business not found")
            return {"ok": True}

        reply = process_message(text)

        send_message(
            phone_number_id=business["phone_number_id"],
            access_token=business["access_token"],
            to=from_number,
            message=reply
        )

    except Exception as e:
        print("ERROR:", e)

    return {"ok": True}


# -----------------------------
# SAVE BUSINESS AFTER EMBEDDED SIGNUP
# Frontend sends: { code, waba_id, phone_number_id }
# -----------------------------
@app.post("/save-token")
async def save_token(request: Request):
    body = await request.json()
    code = body.get("code")
    waba_id = body.get("waba_id")
    phone_number_id = body.get("phone_number_id")

    if not code or not waba_id or not phone_number_id:
        return {"error": "Missing code, waba_id, or phone_number_id", "got": body}

    # exchange code for access token
    token_res = requests.get(
        "https://graph.facebook.com/v20.0/oauth/access_token",
        params={
            "client_id": APP_ID,
            "client_secret": APP_SECRET,
            "code": code,
        },
    ).json()
    print("TOKEN:", token_res)

    access_token = token_res.get("access_token")
    if not access_token:
        return {"error": "Token exchange failed", "details": token_res}

    # subscribe app to WABA so webhook events arrive
    sub_res = requests.post(
        f"https://graph.facebook.com/v20.0/{waba_id}/subscribed_apps",
        params={"access_token": access_token},
    ).json()
    print("SUBSCRIBE:", sub_res)

    # register phone number for Cloud API (required before sending)
    reg_res = requests.post(
        f"https://graph.facebook.com/v20.0/{phone_number_id}/register",
        params={"access_token": access_token},
        json={"messaging_product": "whatsapp", "pin": "000000"},
    ).json()
    print("REGISTER:", reg_res)

    add_business(phone_number_id, access_token, waba_id)

    return {
        "status": "ok",
        "business": {
            "phone_number_id": phone_number_id,
            "waba_id": waba_id,
        },
    }
