from db import get_business


def route_business(phone_number_id):
    return get_business(phone_number_id)
