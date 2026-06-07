from fastapi import APIRouter, Depends, Request
import asyncio
from src.schemas.pay_schemas import SuccesPay, BillingResponse
from aiogram import Bot
from src.utils.texts import BotTexts
from src.auth.dependencies import get_current_user_id
from src.auth.verify_system_token import veify_system_token
from src.utils.semaphore_sending_notif import send_with_semaphore

router = APIRouter(prefix="/pays", tags=['pays'])

@router.post("/success_pay")
async def succes_pay(user_data: SuccesPay, request: Request, user_id: int = Depends(get_current_user_id)):
    bot: Bot = request.app.state.bot
    try:
        await bot.send_message(
            chat_id=user_id,
            text=BotTexts.pay_succes(amount=user_data.amount),
            parse_mode="html"
        )
        return {"status": "ok"}
    except Exception as e:
        print (f"Error pay notif: {e}")
        return None
    
@router.post("/warning_users")
async def billing_notifications(request: Request, notif_data: BillingResponse, service_id: int = Depends(veify_system_token)):
    bot: Bot = request.app.state.bot
    try:
        if notif_data.deleted_keys:
            tasks_del = [send_with_semaphore(user_id=user_id, text_func=BotTexts.del_key(), bot=bot) for user_id in notif_data.deleted_keys]
            await asyncio.gather(*tasks_del)

        if notif_data.user_lower:
            tasks_warn = [send_with_semaphore(user_id=user_id, text_func=BotTexts.warning_balance(), bot=bot) for user_id in notif_data.user_lower]
            await asyncio.gather(*tasks_warn)

        return {"status": "ok"}
    except Exception as e:
        print (f"Error sending bill notif: {e}")
        return None