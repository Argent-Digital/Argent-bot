from aiogram import Router, F, Bot, types
from aiogram.filters import CommandStart, CommandObject
from aiogram.types import Message, CallbackQuery, FSInputFile, InputMediaPhoto
from src.utils.texts import BotTexts
from src.keyboards.user_keyboards import UserKeyboards
from src.loader_bot import pay_client
from src.schemas.pay_schemas import CreatePaymentUrl

router = Router()

@router.callback_query(F.data == "pay")
async def pay_menu(callback: CallbackQuery):
    await callback.answer()

    await callback.message.delete()

    await callback.message.answer(
        text=BotTexts.select_tarif(),
        reply_markup=UserKeyboards.select_tarif(),
        parse_mode="html"
    )

@router.callback_query(F.data.startswith("pay_"))
async def payment_menu(callback: CallbackQuery):
    await callback.answer()
    
    amount = int(callback.data.split("_")[1])
    user_id = callback.from_user.id

    data_url = CreatePaymentUrl(amount=amount)
    try:
        url = await pay_client.create_payment_url(data_url=data_url, user_id=user_id)

        await callback.message.delete()

        await callback.message.answer(
            text=BotTexts.payment_menu(amount=amount, user_id=user_id),
            reply_markup=UserKeyboards.payed(url=url.url),
            parse_mode="html"
        )
    except Exception as e:
        print(f"🚨 АЛАРМ! Реальная ошибка: {repr(e)}", flush=True)
        await callback.answer("❌ Произошла ошибка. Попробуй позже.", show_alert=True)