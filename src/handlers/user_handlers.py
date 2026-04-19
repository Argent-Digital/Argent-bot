from aiogram import Router, F, Bot
from aiogram.filters import CommandStart, CommandObject
from aiogram.types import Message, CallbackQuery, FSInputFile
from src.database.dao.user_dao import UserDao
from src.utils.texts import BotTexts
from src.keyboards.user_keyboards import UserKeyboards

router = Router()

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
        parse_mode='html'
    )