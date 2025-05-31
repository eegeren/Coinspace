from config.config import PREMIUM_IDS

def is_premium(user_id: int) -> bool:
    return str(user_id) in PREMIUM_IDS
