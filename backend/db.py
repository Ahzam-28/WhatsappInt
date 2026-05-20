import os

BUSINESSES = {}


def add_business(phone_number_id, access_token, waba_id):
    BUSINESSES[phone_number_id] = {
        "phone_number_id": phone_number_id,
        "access_token": access_token,
        "waba_id": waba_id,
    }


def get_business(phone_number_id):
    return BUSINESSES.get(phone_number_id)


# Seed a test business from .env so we can develop without Embedded Signup.
_test_token = os.getenv("ACCESS_TOKEN")
_test_phone_id = os.getenv("PHONE_NUMBER_ID")
_test_waba_id = os.getenv("WABA_ID", "")

if _test_token and _test_phone_id:
    add_business(_test_phone_id, _test_token, _test_waba_id)
    print(f"[db] Seeded test business {_test_phone_id}")
