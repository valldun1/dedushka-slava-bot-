import os

SLAVA_ID = int(os.getenv("SLAVA_TG_ID", "0"))
FAMILY_IDS = list(map(int, os.getenv("FAMILY_IDS", "").split(","))) if os.getenv("FAMILY_IDS") else []


def get_mode(user_id: int, is_registered: bool) -> str:
    if user_id == SLAVA_ID:
        return "SLAVA"
    if user_id in FAMILY_IDS:
        if is_registered:
            return "FAMILY"
        return "ONBOARDING"
    return "STRANGER"


def is_family(user_id: int) -> bool:
    return user_id in FAMILY_IDS or user_id == SLAVA_ID


def is_slava(user_id: int) -> bool:
    return user_id == SLAVA_ID
