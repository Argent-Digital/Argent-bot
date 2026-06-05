from aiogram import Router, F, Bot, types
from aiogram.filters import CommandStart, CommandObject
from aiogram.types import Message, CallbackQuery, FSInputFile, InputMediaPhoto
from src.utils.texts import BotTexts
from src.keyboards.user_keyboards import UserKeyboards
from clients.core_client import ArgentCoreClient

router = Router()

# start menu
@router.message(CommandStart())
async def start_menu(message: Message, command: CommandObject, bot: Bot, user_client: ArgentCoreClient):
    args = command.args
    referrer_id = None
    user_id = message.from_user.id

    is_new = not await user_client.check_user(user_id=user_id)

    # ref check
    if is_new and args and args.isdigit():
        from_id = int(args)
        if from_id != message.from_user.id:
            referrer_id = from_id

    # add DB
    await user_client.register_user(
        user_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
        referer_id=referrer_id
    )

    #message refferal
    if is_new and referrer_id is not None:
        await user_client.update_balance(
            user_id=referrer_id,
            amount=60
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