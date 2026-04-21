class BotTexts:
    @staticmethod
    def start_message(name: str):
        return (
            f"""<b>Привет, {name}! 👋</b>

Ищешь надежный и быстрый Proxy? Ты по адресу! 🛡️

🎁 Новым пользователям дарим <b>15 дней</b>!!!

<b>Доступен на всех платформах:</b>
iOS & Android 📱
Windows | macOS | Linux 💻
"""
        )
    
    @staticmethod
    def ref_notif():
        return (
            f"""
💵 Вам начислено <b>30 ₽</b> за приглашение друга!
"""
        )
    
    @staticmethod
    def none_key_message():
        return(f"""
<b>📱 У вас пока нет созданных ключей.</b>
""")
    
    @staticmethod
    def for_active_key_user(protocol: str, access_url: str):
        return(f"""
<b>⛓️‍💥 Ваш {protocol} доступ готов!</b>

<b>1. Скопируйте этот ключ:</b> 
<code>{access_url}</code>

<b>2. Скачайте приложение {'Outline' if protocol == 'outline' else 'В ИНСТРУКЦИИ!!! <i>(если вы перешли со старого протокола, нужно установить новое приложение)</i>'}.</b>

<b>3. Нажмите «Добавить сервер» и вставьте ключ.</b>

<i>Вы можете использовать этот ключ на 10 устройствах одновременно.</i>
""")
    
    @staticmethod
    def select_protocol():
        return(f"""
🛜Выберете протокол:
""")
    
    @staticmethod
    def low_balance_notif():
        return(f"""
❌ Недостаточно средств (нужно минимум 2₽)
""")
    
    @staticmethod 
    def profile_menu(display_name: str, balance: int, status_text: str, expiry_info: int, channel_link: str):
        return(f"""
<b>👤 Профиль </b>
                     
<b>{display_name}, ваш баланс: {balance} руб.</b>

<b>Статус proxy:</b> {status_text}
<b>Хватит на:</b> {expiry_info} дней.

<i>Одного пополнения на 60₽ хватает на 30 дней доступа для 10 устройств!📱</i>

<b>📍 Наш канал: <a href='{channel_link}'>Подписаться</a></b>
""")
    
    @staticmethod
    def instructions_out():
        return(f"""
<b>Инструкция по подключению Argent Proxy 🚀</b>

1️⃣ <b>Скачайте приложение Outline.</b>

2️⃣ <b>Скопируйте ваш ключ.</b>

3️⃣ <b>Активируйте сервис:</b>
— Откройте приложение <b>Outline</b>.

— Нажмите кнопку <b>"Добавить сервер"</b> (или иконку ➕).

— Вставьте скопированный ключ и нажмите <b>"Добавить сервер"</b>.

— Нажмите кнопку <b>"Подключиться"</b>.

✅ <b>Готово! Теперь вы под защитой.</b>
""")

    @staticmethod
    def instructions_vle():
        return(f"""
<b>Инструкция по подключению Argent Proxy 🚀</b>

1️⃣ <b>Скачайте приложение в зависимости от вашей ос (Для пк и телефонов приложения отличаются!).</b>

2️⃣ <b>Скопируйте ваш ключ.</b>

3️⃣ <b>Активируйте сервис:</b>
— Откройте приложение.

— Нажмите кнопку <b>"Добавить сервер"</b> (или иконку ➕).

— Вставьте скопированный ключ и нажмите <b>"Добавить сервер"</b>.

— Нажмите кнопку <b>"Подключиться"</b>.

✅ <b>Готово! Теперь вы под защитой.</b>
""")
