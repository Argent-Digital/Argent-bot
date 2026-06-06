from aiogram import Router, F, Bot, types
from aiogram.filters import CommandStart, CommandObject
from aiogram.types import Message, CallbackQuery, FSInputFile, InputMediaPhoto
from src.utils.texts import BotTexts
from src.keyboards.user_keyboards import UserKeyboards
from src.loader_bot import core_client

router = Router()

@router.callback_query(F.data == "pay")
async def pay_menu(callback: CallbackQuery):
    await callback.answer()