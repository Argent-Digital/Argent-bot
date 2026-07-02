import asyncio
from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, FSInputFile, InputMediaPhoto
from src.utils.distributor import run_distribution
from src.utils.texts import BotTexts
from src.keyboards.user_keyboards import UserKeyboards
from src.states.adm_states import AdminStates
from src.loader_bot import core_client
from src.schemas.bot_schema import AdmUpdateBalance
from src.config import settings

router = Router()

@router.message(Command("panel"))
async def cmd_stats(message: Message):
    user_id = message.from_user.id
    if user_id == settings.TG_ADM_ID:
        stats = await core_client.get_adm_stats(user_id=user_id)

        await message.answer(
            text=BotTexts.stats_menu(stats=stats),
            reply_markup=UserKeyboards.stats_adm_button(),
            parse_mode="html"
        )

#update balance
@router.callback_query(F.data=="adm_update_balance")
async def adm_update_balance(callback: CallbackQuery, state: FSMContext):
    await state.set_state(AdminStates.waiting_for_id)
    await callback.message.answer("Введите ID пользователя:")

@router.message(AdminStates.waiting_for_id)
async def process_id(message: Message, state: FSMContext):
    await state.update_data(user_id=message.text)
    await state.set_state(AdminStates.waiting_for_amount)
    await message.answer("Теперь введите сумму:")

@router.message(AdminStates.waiting_for_amount)
async def process_amount(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    user_id = int(data.get("user_id"))
    amount = int(message.text)

    update_data = AdmUpdateBalance(user_id=user_id, amount=amount)
    
    try:
        await core_client.adm_update_balance(data=update_data, user_id=message.from_user.id)
        try:
            await bot.send_message(
                chat_id=user_id,
                text=BotTexts.adm_update(amount=amount),
                parse_mode="html"
            )
        except:
            await message.answer("Юзер заблокировал бота, не доставили сообщение!")

        await message.answer(f"Готово! Юзеру {user_id} начислен баланс {amount}.")
    except Exception as e:
        await message.answer(f"Не удалось пополнить:{e}")

    finally:
        await state.clear()

#dist
@router.callback_query(F.data=="distribution")
async def wait_post(callback: CallbackQuery, state: FSMContext):
    await state.set_state(AdminStates.waiting_for_post)
    await callback.message.answer("Отправьте пост для рассылки:")

@router.message(AdminStates.waiting_for_post)
async def adm_dist(message: Message, state: FSMContext, bot: Bot):
    post = message.html_text
    await state.update_data(post_text=post)

    await message.answer(text=post, parse_mode="html")
    await message.answer(text="Пост принят, начинаем рассылку?", reply_markup=UserKeyboards.dist_query())

@router.callback_query(F.data=="Ye")
async def start_dist(callback: CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    post = data.get("post_text")

    user_ids = await core_client.get_users_list(user_id=callback.message.from_user.id)
    if user_ids is None:
        print("Список пользователей пуст")
        return None

    asyncio.create_task(run_distribution(bot=bot, user_ids=user_ids, post_text=post))
    await callback.message.answer(text="Рассылка запущена в фоновом режиме!")
    await state.clear()
