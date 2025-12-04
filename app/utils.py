import secrets
from sqlalchemy.orm import Session
from typing import Optional

from . import models

def generate_api_key() -> str:
    """
    Generate a random 32-char hex API key for merchants.
    """
    return secrets.token_hex(16)

def get_merchant_by_api_key(db: Session, api_key: str) -> Optional[models.Merchant]:
    """
    Look up a merchant by its API key.
    """
    return (
        db.query(models.Merchant)
        .filter(models.Merchant.api_key == api_key)
        .first()
    )
