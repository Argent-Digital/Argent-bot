from aiogram import Router, F, Bot, types
from aiogram.filters import CommandStart, CommandObject
from aiogram.types import Message, CallbackQuery, FSInputFile, InputMediaPhoto
from src.utils.texts import BotTexts
from src.keyboards.user_keyboards import UserKeyboards
from src.loader_bot import core_client

router = Router()

# key menu
@router.callback_query(F.data == 'my_keys')
async def key_menu(callback: CallbackQuery):
    await callback.answer()
    key_data = await core_client.get_user_access_url(user_id=callback.from_user.id)

    if key_data is None:
        text = BotTexts.none_key_message()
        kb = UserKeyboards.key_buttons(protocol=None)
    else:
        text = BotTexts.for_active_key_user(
            protocol=key_data.protocol,
            access_url=key_data.access_url
        )

    photo = FSInputFile(r"src\img\key_menu.png")
    
    await callback.message.edit_media(
        media=InputMediaPhoto(media=photo, caption=text, parse_mode='html'),
        reply_markup=kb
    )
