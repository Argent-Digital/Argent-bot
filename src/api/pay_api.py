from fastapi import APIRouter, Depends, Request
from src.schemas.pay_schemas import SuccesPay
from aiogram import Bot
from src.utils.texts import BotTexts

router = APIRouter(prefix="/pays", tags=['pays'])

@router.post("/success_pay")
async def succes_pay(user_data: SuccesPay, request: Request):
    bot: Bot = request.app.state.bot
    try:
        await bot.send_message(
            chat_id=user_data.user_id,
            text=BotTexts.pay_succes(amount=user_data.amount),
            parse_mode="html"
        )
        return {"status": "ok"}
    except Exception as e:
        print (f"Error pay notif: {e}")
        return {"status": "error"}