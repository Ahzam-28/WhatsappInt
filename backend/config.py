import os
from dotenv import load_dotenv

load_dotenv()

APP_ID = os.getenv("APP_ID")
APP_SECRET = os.getenv("APP_SECRET")
CONFIG_ID = os.getenv("CONFIG_ID")
REDIRECT_URI = os.getenv("REDIRECT_URI")

VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")
