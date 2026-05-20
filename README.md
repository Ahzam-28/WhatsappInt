# WhatsApp Cloud API Bot

A FastAPI backend + minimal frontend that connects to the WhatsApp Cloud API. Supports two modes:

1. **Test mode** — seed a single business from `.env` and use Meta's free test phone number. No Business Verification required.
2. **Multi-tenant mode** — onboard real businesses through Facebook's Embedded Signup popup. Requires Business Verification + App Review on the Meta side.

Incoming messages are received via webhook, dispatched to the right business by `phone_number_id`, processed by a stub function, and a reply is sent back through Graph API.

---

## Project structure

```
.
├── backend/
│   ├── main.py              FastAPI routes (/, /api/config, /webhook, /save-token)
│   ├── config.py            Loads env vars
│   ├── db.py                In-memory BUSINESSES dict, seeded from .env on boot
│   └── services/
│       ├── router.py        Looks up a business by phone_number_id
│       ├── processor.py     Stub that decides what to reply
│       └── whatsapp.py      Sends a message via Graph API
├── frontend/
│   └── index.html           Connect-WhatsApp page using FB JS SDK Embedded Signup
├── requirements.txt
└── .gitignore
```

---

## Prerequisites

- Python 3.10+
- A Meta Developer account and an app (type **Business**) with the **WhatsApp** product enabled
- An HTTPS public URL pointing to your local server (ngrok, Cloudflare Tunnel, or a deployed host)

---

## Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Create `backend/.env`

```env
APP_ID=your_meta_app_id
APP_SECRET=your_meta_app_secret
CONFIG_ID=your_fb_login_configuration_id
REDIRECT_URI=https://your-public-host/oauth/callback
VERIFY_TOKEN=any_random_string

# Test mode: paste the test credentials from Meta dashboard
# (WhatsApp → API Setup). Leave blank for Embedded-Signup-only mode.
ACCESS_TOKEN=
PHONE_NUMBER_ID=
WABA_ID=
```

Where to find each value:

| Variable | Source |
|---|---|
| `APP_ID`, `APP_SECRET` | App settings → Basic |
| `CONFIG_ID` | Facebook Login for Business → Configurations (must be type "Business login with WhatsApp") |
| `VERIFY_TOKEN` | You choose; must match the value entered in Meta's webhook config |
| `ACCESS_TOKEN` | WhatsApp → API Setup (temporary 24h token, or a System User token for permanence) |
| `PHONE_NUMBER_ID` | WhatsApp → API Setup |
| `WABA_ID` | WhatsApp → API Setup |

### 3. Meta dashboard configuration

In your Meta app:

- **App settings → Basic**: add your public host (without `https://`) to **App Domains** and set a Privacy Policy URL
- **Facebook Login for Business → Settings**: enable Client OAuth Login, Web OAuth Login, Strict Mode. Add `https://<your-host>/oauth/callback` to Valid OAuth Redirect URIs. Add `https://<your-host>` to Allowed JS SDK Domains.
- **Facebook Login for Business → Configurations**: create one with login variation **"Business login with WhatsApp"** and permissions `whatsapp_business_messaging`, `whatsapp_business_management`. Copy the Configuration ID into `.env` as `CONFIG_ID`.
- **WhatsApp → Configuration → Webhook**: callback URL `https://<your-host>/webhook`, verify token = `VERIFY_TOKEN` from `.env`. Subscribe to the `messages` field.
- **App roles → Roles**: while in Development mode, add every Facebook user you want to test with as Admin/Developer/Tester. They must accept the invite at https://www.facebook.com/settings?tab=business_tools.

### 4. Run

```bash
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

If `ACCESS_TOKEN` and `PHONE_NUMBER_ID` are set in `.env`, the terminal prints:

```
[db] Seeded test business <phone_number_id>
```

Expose port 8000 publicly:

```bash
ngrok http 8000
```

Use the resulting `https://...ngrok-free.app` URL in all Meta dashboard fields above.

---

## Testing

### Test mode (no verification required)

1. In **WhatsApp → API Setup**, add your personal WhatsApp number to the **"To"** recipient list (Meta sends a code to verify it).
2. From your personal WhatsApp, send `"hi"` to the test number shown in API Setup.
3. The terminal logs the incoming webhook payload, and you receive `"hello"` back.

### Embedded Signup mode (real businesses)

1. Open `https://<your-host>/` in a browser.
2. Click **Connect WhatsApp**.
3. The Meta popup walks the user through creating a Business Portfolio → WhatsApp Business Account → phone number.
4. On finish, the popup posts `waba_id` and `phone_number_id` back to the page via `postMessage`, and an OAuth `code` is returned to `FB.login`.
5. Frontend `POST`s `{code, waba_id, phone_number_id}` to `/save-token`.
6. Backend exchanges the code for an access token, subscribes the app to the WABA's webhook, registers the phone number on Cloud API, and stores the business in memory.

Note: In Development mode only users with an accepted App Role can complete Embedded Signup. For real customers, the app must go through Business Verification + App Review for the WhatsApp permissions.

---

## Routes

| Method | Path | Purpose |
|---|---|---|
| GET | `/` | Serves the Connect page (`frontend/index.html`) |
| GET | `/api/config` | Returns `{app_id, config_id}` for the frontend |
| GET | `/webhook` | Meta webhook verification (echoes `hub.challenge`) |
| POST | `/webhook` | Receives messages and status updates |
| POST | `/save-token` | Exchanges OAuth code, subscribes WABA, registers phone, stores business |

---

## Customizing the reply

Edit [backend/services/processor.py](backend/services/processor.py):

```python
def process_message(text):
    return "hello"
```

Replace this with your own logic (LLM call, command parsing, database lookup, etc.). Return the string you want sent back.

---

## Notes

- `BUSINESSES` is an in-memory dict. It resets on every restart; the `.env`-seeded test business comes back automatically, but businesses added via Embedded Signup are lost. Swap to a real database (Postgres, SQLite, Redis) for production.
- The temporary access token from WhatsApp → API Setup expires every 24 hours. For longer-lived tokens, generate a **System User token** under Business Settings → System Users.
- Every time your public URL changes (ngrok restart, new host), update the App Domains, Valid OAuth Redirect URIs, JS SDK Domains, and Webhook Callback URL in the Meta dashboard.
