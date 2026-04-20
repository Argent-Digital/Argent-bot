from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

class UserKeyboards:
    
    @staticmethod
    def start_menu():
        btn_conn = InlineKeyboardButton(text='Подключить 📲', callback_data='my_keys')
        btn_home = InlineKeyboardButton(text='Профиль👤', callback_data='home')
        btn_about = InlineKeyboardButton(text="О сервисе ℹ️", callback_data="about_service")
        btn_channel = InlineKeyboardButton(text="канал⚡", url="https://t.me/ArgentVPNru")

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [btn_conn],
                [btn_home],
                [btn_about, btn_channel]
            ]
        )
        return keyboard
    
    @staticmethod
    def key_buttons(protocol: str | None,):
        instsel = "outline_inst" if protocol == "outline" else "vless_inst"

        btn_create = InlineKeyboardButton(text="➕ Создать доступ (2₽/сутки)", callback_data="buy_vpn")
        btn_del = InlineKeyboardButton(text="🗑 Удалить ключ полностью", callback_data=f"del_key")
        btn_installs = InlineKeyboardButton(text="📖 Установить приложение", callback_data=instsel)
        btn_back = InlineKeyboardButton(text="⬅️ В профиль", callback_data="back_to_profile")

        if protocol is not None:
            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [btn_del],
                    [btn_installs],
                    [btn_back]
                ]
            )
        else:
            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [btn_create],
                    [btn_installs],
                    [btn_back]
                ]
            )

        return keyboard
    
    @staticmethod
    def select_protocol():
        btn_out = InlineKeyboardButton(text="🚀 VLESS (Скорость)", callback_data="Vless_connect")
        btn_vle = InlineKeyboardButton(text="🛡 Outline (Резерв)", callback_data="Outline_connect")

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [btn_vle],
                [btn_out]
            ]
        )

        return keyboard