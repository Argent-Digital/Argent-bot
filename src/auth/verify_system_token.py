from fastapi import Depends, HTTPException, status
from src.auth.dependencies import get_current_user_id

async def veify_system_token(user_id: int = Depends(get_current_user_id)):
    if user_id != 0:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access only for system services"
        )
    return user_id