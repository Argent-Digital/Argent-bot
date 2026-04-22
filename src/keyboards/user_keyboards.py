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
        btn_back = InlineKeyboardButton(text="⬅️ В профиль", callback_data="home")

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
    
    @staticmethod
    def profile_buttons():
        btn_pay = InlineKeyboardButton(text='Пополнить баланс 💳', callback_data='pay')
        btn_conn = InlineKeyboardButton(text='Подключить 📲', callback_data='my_keys')
        btn_ref = InlineKeyboardButton(text='Пригласить друга 👥', callback_data='ref_program')
        btn_part = InlineKeyboardButton(text='Партнерская программа 🧑‍💻', callback_data= "partner_menu")
        btn_supp = InlineKeyboardButton(text='Поддержка 🆘',  url="https://t.me/pyxxisss")
        btn_back = InlineKeyboardButton(text='Вернуться ↩️', callback_data='back_start')

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [btn_pay],
                [btn_conn],
                [btn_ref],
                [btn_part],
                [btn_supp, btn_back]
            ]
        )

        return keyboard
    
    @staticmethod
    def inst_out_but():
        android = InlineKeyboardButton('Android', url="https://play.google.com/store/apps/details?id=org.outline.android.client&pcampaignid=web_share")
        ios = InlineKeyboardButton('Ios', url="https://apps.apple.com/us/app/outline-app/id1356177741")
        mac = InlineKeyboardButton('MacOS', url="https://apps.apple.com/us/app/outline-secure-internet-access/id1356178125?mt=12")
        win = InlineKeyboardButton('Windows', callback_data='win_out')
        lin = InlineKeyboardButton('Linux', callback_data="win_out")
        back = InlineKeyboardButton('Вернуться↩️', callback_data='my_key')

        keyboards = InlineKeyboardMarkup(
            inline_keyboard=[
                [android, ios],
                [win],
                [mac, lin],
                [back]
            ]
        )

        return keyboards
    
    @staticmethod
    def inst_vle_but():
        android = InlineKeyboardButton('Android', url="https://play.google.com/store/apps/details?id=com.v2raytun.android")
        ios = InlineKeyboardButton('Ios', url="https://apps.apple.com/app/id6476628951")
        mac = InlineKeyboardButton('MacOS', url="https://apps.apple.com/us/app/v2raytun/id6476628951")
        win = InlineKeyboardButton('Windows', callback_data='win_vle')
        lin = InlineKeyboardButton('Linux', url="https://github.com/MatsuriDayo/nekoray/releases")
        back = InlineKeyboardButton('Вернуться↩️', callback_data='my_key')

        keyboards = InlineKeyboardMarkup(
            inline_keyboard=[
                [android, ios],
                [win],
                [mac, lin],
                [back]
            ]
        )

        return keyboards
    
    @staticmethod
    def about_service():
        btn_ofer = InlineKeyboardButton(text="📄 Оферта", url="https://telegra.ph/Publichnaya-oferta-servisa-Argent-Digital-01-21")
        btn_private = InlineKeyboardButton(text="🛡 Приватность", url="https://telegra.ph/Politika-konfidencialnosti-Argent-Digital-01-21")
        btn_back = InlineKeyboardButton(text="⬅️ Назад", callback_data="back_start")

        keyboards = InlineKeyboardMarkup(
            inline_keyboard=[
                [btn_ofer, btn_private],
                [btn_back]
            ]
        )
        return keyboards
    
    @staticmethod
    def ref_prog():
        back = InlineKeyboardButton(text="⬅️ Назад в профиль", callback_data="home")
        keyboards = InlineKeyboardMarkup(
            inline_keyboard=[
                [back]
            ]
        )
        return keyboards
    
    @staticmethod
    def partner_menu():
        btt_support = InlineKeyboardButton(text="🆘 Связаться с поддержкой", url="https://t.me/pyxxisss")
        btn_back = InlineKeyboardButton(text="⬅️ Назад", callback_data="home")

        keyboards = InlineKeyboardMarkup(
            inline_keyboard=[
                [btt_support],
                [btn_back]
            ]
        )
        return keyboards
        