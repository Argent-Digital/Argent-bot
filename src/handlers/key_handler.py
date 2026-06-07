from aiogram import Router, F, Bot, types
from aiogram.filters import CommandStart, CommandObject
from aiogram.types import Message, CallbackQuery, FSInputFile, InputMediaPhoto
from src.utils.texts import BotTexts
from src.keyboards.user_keyboards import UserKeyboards
from src.loader_bot import core_client

from src.schemas.bot_schema import UpdateBalance
from src.schemas.vpn_client_schema import CreateKeyApiBody

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
            access_url=key_data.access_url,
        )
        kb = UserKeyboards.key_buttons(protocol=key_data.protocol)

    photo = FSInputFile(r"src/img/key_menu.png")
    
    await callback.message.edit_media(
        media=InputMediaPhoto(media=photo, caption=text, parse_mode='html'),
        reply_markup=kb
    )

@router.callback_query(F.data == "buy_vpn")
async def select_protocol_menu(callback: CallbackQuery):
    data_balance = await core_client.get_balance(user_id=callback.from_user.id)

    if data_balance.balance < 2:
        await callback.answer(
            text=BotTexts.low_balance_notif(),
            show_alert=True
        )

    else:
        await callback.answer()
        await callback.message.edit_caption(
            caption=BotTexts.select_protocol(),
            reply_markup=UserKeyboards.select_protocol(),
            parse_mode='html'
        )

@router.callback_query(F.data == "outline_inst")
async def outline_inst(callback: CallbackQuery):
    await callback.answer()


    photo = FSInputFile(r"src/img/inst.png")
    await callback.message.edit_media(
        media= InputMediaPhoto(media=photo, caption=BotTexts.instructions_out(), parse_mode='html'),
        reply_markup=UserKeyboards.inst_out_but()
    )

@router.callback_query(F.data == "vless_inst")
async def vless_inst(callback: CallbackQuery):
    await callback.answer()


    photo = FSInputFile(r"src/img/inst.png")
    await callback.message.edit_media(
        media= InputMediaPhoto(media=photo, caption=BotTexts.instructions_vle(), parse_mode='html'),
        reply_markup=UserKeyboards.inst_vle_but()
    )

#file client app
@router.callback_query(F.data == "win_out")
async def win_out_file(callback: CallbackQuery):
    await callback.message.answer_document(
        document="BQACAgIAAxkBAANsaV1LoQKyU_tHKMIW3QqwZjTVQfcAAneRAALl4ulKC4UWPPhd4m84BA",
        caption="Outline client for Windows"
    )

@router.callback_query(F.data == "lin_out")
async def lin_out_file(callback: CallbackQuery):
    await callback.message.answer_document(
        document="BQACAgIAAxkBAANzaV1XzyM0KeYie7pAUJcHRDrCbM0AAmeSAALl4ulKAAHUnL7E_gABFTgE",
        caption="Outline client for linux"
    )

@router.callback_query(F.data == "win_vle")
async def win_out_file(callback: CallbackQuery):
    await callback.message.answer_document(
        document="BQACAgIAAxkBAAIRnmmca7oxnbPjjhh9QOSGInApbkilAAJTkAACeWLpSARAM4oHPdVxOgQ",
        caption="Vless client for Windows"
    )

@router.callback_query(F.data == "Vless_connect")
async def connect_vless_key(callback: CallbackQuery):
    try:
        body=CreateKeyApiBody(protocol="vless")
        await core_client.create_key(body=body, user_id=callback.from_user.id)

        data = UpdateBalance(amount=-2)
        await core_client.update_balance(data=data, user_id=callback.from_user.id)

        await key_menu(callback)

    except Exception as e:
        print(f"Ошибка при создании ключа: {e}")
        await callback.answer("❌ Не удалось создать ключ. Попробуй позже.", show_alert=True)