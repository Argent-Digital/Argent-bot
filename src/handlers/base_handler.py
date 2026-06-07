from aiogram import Router, F, Bot
from aiogram.filters import CommandStart, CommandObject
from aiogram.types import Message, CallbackQuery, FSInputFile, InputMediaPhoto
from src.utils.texts import BotTexts
from src.keyboards.user_keyboards import UserKeyboards
from src.loader_bot import core_client

from src.schemas.bot_schema import UserRegister, UpdateBalance

router = Router()

# start menu
@router.message(CommandStart())
async def start_menu(message: Message, command: CommandObject, bot: Bot):
    args = command.args
    referrer_id = None
    user_id = message.from_user.id

    is_new = not await core_client.check_user(user_id=user_id)

    # ref check
    if is_new and args and args.isdigit():
        from_id = int(args)
        if from_id != message.from_user.id:
            referrer_id = from_id

    # add DB
    data_db = UserRegister(user_id=user_id, username=message.from_user.username, first_name=message.from_user.first_name,referrer_id=referrer_id)
    await core_client.register_user(
        user_data=data_db
    )

    #message refferal
    if is_new and referrer_id is not None:
        amount = UpdateBalance(amount=60)
        await core_client.update_balance(
            user_id=referrer_id,
            data=amount
        )
        try:
            await bot.send_message(
                chat_id=referrer_id,
                text = BotTexts.ref_notif,
                parse_mode='html'
            )
        except Exception as e:
            print(f"Не удалось отправить уведомление рефереру {referrer_id}: {e}")

    photo = FSInputFile(r"src/img/re_Start.png")

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
    
    photo = FSInputFile(r"src/img/re_Start.png")
    await callback.message.answer_photo(
        photo=photo,
        caption=BotTexts.start_message(callback.from_user.first_name),
        reply_markup=UserKeyboards.start_menu(),
        parse_mode='html'
    )

@router.callback_query(F.data == "home")
async def profile_menu(callback: CallbackQuery):
    await callback.answer()

    display_name = callback.from_user.first_name
    data_balance = await core_client.get_balance(user_id=callback.from_user.id)
    status_text = await core_client.get_user_access_url(user_id=callback.from_user.id)
    expiry_info = data_balance.balance // 2
    channel_link = "https://t.me/ArgentVPNru"
    photo = FSInputFile(r"src/img/profile.png")

    if status_text is not None:
        status_text = "✅ Работает"
    else:
        status_text = "❌ Отключен"

    await callback.message.edit_media(
        media= InputMediaPhoto(
            media=photo,
            caption=BotTexts.profile_menu(display_name=display_name, balance=data_balance.balance, status_text=status_text, expiry_info=expiry_info, channel_link=channel_link),
            parse_mode='html'
            ),
        reply_markup=UserKeyboards.profile_buttons()
    )

# about service
@router.callback_query(F.data == "about_service")
async def about_service(callback: CallbackQuery):
    await callback.answer()

    await callback.message.edit_caption(
        caption=BotTexts.about_service(),
        reply_markup=UserKeyboards.about_service(),
        parse_mode='html'
    )

# referral menu
@router.callback_query(F.data == "ref_program")
async def ref_prog(callback: CallbackQuery):
    await callback.answer()

    bot_info = await callback.bot.get_me()
    ref_link = f"http://t.me/{bot_info.username}?start={callback.from_user.id}"

    await callback.message.delete()

    await callback.message.answer(
        text=BotTexts.ref_prog(ref_link=ref_link),
        reply_markup=UserKeyboards.ref_prog(),
        parse_mode='html'
    )

# partner menu
@router.callback_query(F.data == "partner_menu")
async def partner_menu(callback: CallbackQuery):
    await callback.answer()
    await callback.message.delete()
    await callback.message.answer(
        text=BotTexts.partner_menu(),
        reply_markup=UserKeyboards.partner_menu(),
        parse_mode='html'
    )
