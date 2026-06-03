from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from typing import Optional

from src.config import settings
from src.schemas.jwt_schema import TokenData

def create_access_token(data: TokenData) -> str:

    to_encode = {"sub": str(data.user_id)}

    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})

    encode_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY_FOR_JWT,
        algorithm=settings.ALGORITHM
    )
    return encode_jwt

def decode_access_token(token: str) -> Optional[TokenData]:
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY_FOR_JWT,
            algorithms=[settings.ALGORITHM]
        )

        user_id_str: str = payload.get("sub")
        if user_id_str is None:
            return None
        
        return TokenData(user_id=int(user_id_str))
    
    except (JWTError, ValueError):
        return None