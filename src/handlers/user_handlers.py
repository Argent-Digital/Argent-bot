from aiogram import Router, F, Bot, types
from aiogram.filters import CommandStart, CommandObject
from aiogram.types import Message, CallbackQuery, FSInputFile, InputMediaPhoto
from src.database.dao.user_dao import UserDao
from src.database.dao.vpn_dao import VpnKeyDao
from src.utils.texts import BotTexts
from src.keyboards.user_keyboards import UserKeyboards
from xui_api import XUIPanel

router = Router()

# start menu
@router.message(CommandStart())
async def start_menu(message: Message, command: CommandObject, bot: Bot):
    args = command.args
    referrer_id = None

    is_new = not await UserDao.check_user(message.from_user.id)

    # ref check
    if is_new and args and args.isdigit():
        from_id = int(args)
        if from_id != message.from_user.id:
            referrer_id = from_id

    # add DB
    await UserDao.add_user(
        user_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
        referer_id=referrer_id
    )

    #message refferal
    if referrer_id is not None:
        await UserDao.update_balance(
            user_id=referrer_id,
            amount=30
        )
        try:
            await bot.send_message(
                chat_id=referrer_id,
                text = BotTexts.ref_notif,
                parse_mode='html'
            )
        except Exception as e:
            print(f"Не удалось отправить уведомление рефереру {referrer_id}: {e}")

    photo = FSInputFile(r"src\img\re_Start.png")

    await message.answer_photo(
        photo = photo,
        caption = BotTexts.start_message(message.from_user.first_name),
        parse_mode='html',
        reply_markup=UserKeyboards.start_menu()
    )


@router.callback_query(F.data == "back_start")
async def back_start_menu(callback: CallbackQuery):
    await callback.answer()
    await callback.message.delete()
    
    photo = FSInputFile(r"src\img\re_Start.png")
    await callback.message.answer_photo(
        photo=photo,
        caption=BotTexts.start_message(callback.from_user.first_name),
        reply_markup=UserKeyboards.start_menu(),
        parse_mode='html'
    )

# key menu
@router.callback_query(F.data == 'my_keys')
async def key_menu(callback: CallbackQuery):
    await callback.answer()
    key_data = await VpnKeyDao.get_user_access_url(user_id=callback.from_user.id)

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

@router.callback_query(F.data == "buy_vpn")
async def select_protocol_menu(callback: CallbackQuery):
    await callback.answer()

    balance = await UserDao.get_user_balance(user_id=callback.from_user.id)

    if balance < 2:
        await callback.message.answer(
            text=BotTexts.low_balance_notif()
        )

    else:
        await callback.message.edit_caption(
            caption=BotTexts.select_protocol(),
            reply_markup=UserKeyboards.select_protocol(),
            parse_mode='html'
        )

# @router.callback_query(F.data == "Vless_connect")
# async def connect_vless_key(callback: CallbackQuery):
#     await UserDao.update_balance(callback.from_user.id, -2)

#     try:
#         v_url, v_uuid = await XUIPanel.add_client(callback.from_user.id)

#         await VpnKeyDao.add_vpn_key(
#             user_id=callback.from_user.id,
#             key_name=f"user_{callback.from_user.id}",
#             access_url=v_url,
#             protocol="vless",
#             vless_uuid=v_uuid
#         )

@router.callback_query(F.data == "home")
async def profile_menu(callback: CallbackQuery):
    await callback.answer()

    display_name = callback.from_user.first_name
    balance = await UserDao.get_user_balance(user_id=callback.from_user.id)
    status_text = await VpnKeyDao.get_user_access_url(user_id=callback.from_user.id)
    expiry_info = balance // 2
    channel_link = "https://t.me/ArgentVPNru"
    photo = FSInputFile(r"src\img\profile.png")


    if status_text is not None:
        status_text = "✅ Работает"
    else:
        status_text = "❌ Отключен"

    await callback.message.edit_media(
        media= InputMediaPhoto(
            media=photo,
            caption=BotTexts.profile_menu(display_name=display_name, balance=balance, status_text=status_text, expiry_info=expiry_info, channel_link=channel_link),
            parse_mode='html'
            ),
        reply_markup=UserKeyboards.profile_buttons()
    )
