from fastapi import APIRouter, Depends, Request
from src.schemas.pay_schemas import SuccesPay
from src.schemas.vpn_client_schema import BillingResponse
from aiogram import Bot
from src.utils.texts import BotTexts
from src.auth.dependencies import decode_access_token
from src.auth.verify_system_token import veify_system_token

router = APIRouter(prefix="/pays", tags=['pays'])

@router.post("/success_pay")
async def succes_pay(user_data: SuccesPay, request: Request, user_id: int = Depends(decode_access_token)):
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
        return {"status": "error"}
    
@router.post("/warning_users")
async def billing_notifications(request: Request, notif_data: BillingResponse, service_id: int = Depends(veify_system_token)):
    bot: Bot = request.app.state.bot
    for user_id in notif_data.deleted_keys:
        try:
            await bot.send_message(
                chat_id=user_id,
                text=BotTexts.del_key(),
                parse_mode="html"
            )
        except Exception as e:
            print(f"Error sending del_key to user {user_id}: {e}")

    for user_id in notif_data.user_lower:
        try:
            await bot.send_message(
                chat_id=user_id,
                text=BotTexts.warning_balance(),
                parse_mode="html"
            )
        except Exception as e:
            print(f"Error sending warning_balance to user {user_id}: {e}")

    return {"status": "ok"}