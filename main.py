import telebot
from telebot import types
import db

db.init_db()

bot = telebot.TeleBot('8195901758:AAFg_179LBV84ryKgbBAr0v0jRactmfxdP0')

bot.set_my_commands([
    telebot.types.BotCommand("start", "Главное меню"),
    telebot.types.BotCommand("buy", "Купить подписку"),
    telebot.types.BotCommand("instructions", "Настройка устройств"),
    telebot.types.BotCommand("profile", "Личный кабинет"),
    telebot.types.BotCommand("support", "Поддержка")
])

# start
@bot.message_handler(commands=['start'])
def main(message, user_name = None):
    db.add_user(message.from_user.id, message.from_user.username)

    try:
        bot.delete_message(message.chat.id, message.message_id)
    except:
        pass

    startmarkups = types.InlineKeyboardMarkup()
    profile = types.InlineKeyboardButton('Главная👤', callback_data='home')
    instruction = types.InlineKeyboardButton('Инструкция📖', callback_data='instuct')
    support = types.InlineKeyboardButton('Поддержка🆘', callback_data='helping')
    startmarkups.row (profile)
    startmarkups.row (instruction, support)

    if user_name:
        # Если имя пришло из callback (нажатия кнопки)
        full_name = user_name
    else:
        # Если это команда /start
        first_name = message.from_user.first_name or ""
        last_name = message.from_user.last_name or ""
        full_name = f"{first_name} {last_name}".strip()
    
    with open('img\\start.png', 'rb') as photo:
        bot.send_photo(
            message.chat.id, 
            photo, 
            caption=f"""<b>Привет, {full_name}! 👋</b>

Ищешь надежный и быстрый VPN? Ты по адресу! 🚀

<b>Наши преимущества:</b>
- <b>Скорость:</b> Без ограничений, летай в соцсетях и смотри видео в 4K.⚡

- <b>Цена:</b> Всего <b>60 рублей</b> в месяц — дешевле чашки кофе!😍

- <b>Устройства:</b> Подключай до <b>3-х устройств</b> на одну подписку.📲

<b>Доступен на всех платформах:</b>
iOS & Android 📱
Windows, macOS & Linux 💻      
""",
            parse_mode='html',
            reply_markup=startmarkups)
        
# действия с кнопками
@bot.callback_query_handler(func=lambda callback: True)
def callback_message(callback):
    if callback.data == "home":
        # Берем данные ЧЕЛОВЕКА, нажвашего кнопку
        u_name = f"{callback.from_user.first_name or ''} {callback.from_user.last_name or ''}".strip()
        u_id = callback.from_user.id
        
        # Передаем их в функцию
        show_profile(callback.message, user_name=u_name, user_id=u_id)
        bot.answer_callback_query(callback.id)

    elif callback.data == 'instuct':       
        send_instruction_menu(callback.message)

    # функции для установки из инструкции
    elif callback.data == 'android':
        bot.send_message(callback.message.chat.id, 'Ссылка на установку в Google play 👉: https://play.google.com/store/apps/details?id=org.outline.android.client&pcampaignid=web_share')
    elif callback.data == 'ios':
        bot.send_message(callback.message.chat.id, 'Ссылка на установку в App Store 👉: https://apps.apple.com/us/app/outline-app/id1356177741')
    elif callback.data == 'mac':
        bot.send_message(callback.message.chat.id, 'Ссылка на установку в App Store для Mac 👉: https://apps.apple.com/us/app/outline-secure-internet-access/id1356178125?mt=12')
    elif callback.data == 'win':
        winsetup_id = "BQACAgIAAxkBAANsaV1LoQKyU_tHKMIW3QqwZjTVQfcAAneRAALl4ulKC4UWPPhd4m84BA" # Вставь сюда длинную строку
        bot.send_document(callback.message.chat.id, winsetup_id, caption="Установщик для Windows💻 (Вынужденная мера, так как официальный сайт для установки outline блокируется в РФ.)")
    elif callback.data == 'lin':
        linsetup_id = "BQACAgIAAxkBAANzaV1XzyM0KeYie7pAUJcHRDrCbM0AAmeSAALl4ulKAAHUnL7E_gABFTgE"
        bot.send_document(callback.message.chat.id, linsetup_id, caption="Файл для Linux💻 (Вынужденная мера, так как официальный сайт для установки outline блокируется в РФ.)")

    elif callback.data== 'back_for_inst':
        name_to_show = callback.from_user.first_name
        main(callback.message, user_name=name_to_show)

    #поддержка 
    elif callback.data == 'back_to_main':
        name_to_show = callback.from_user.first_name
        main(callback.message, user_name=name_to_show)
    
    elif callback.data == 'back_to_profile':
        u_name = f"{callback.from_user.first_name or ''} {callback.from_user.last_name or ''}".strip()
        u_id = callback.from_user.id
        
        # Передаем данные человека
        show_profile(callback.message, user_name=u_name, user_id=u_id)
        bot.answer_callback_query(callback.id)

    elif callback.data == 'helping':
        support_mes(callback.message, back_target='back_to_main')

    # Переход в поддержку из профиля
    elif callback.data == 'support_from_profile':
        support_mes(callback.message, back_target='back_to_profile')

    # стартовая из профиля
    elif callback.data == 'back_main':
        name_to_show = callback.from_user.first_name
        main(callback.message, user_name=name_to_show)



# раздел с инструкцией
@bot.message_handler(commands=['instructions'])
def send_instruction_menu(message):
    try:
        bot.delete_message(message.chat.id, message.message_id)
    except:
        pass

    instuctmarkups = types.InlineKeyboardMarkup()
    android = types.InlineKeyboardButton('Android', callback_data='android')
    ios = types.InlineKeyboardButton('Ios', callback_data='ios')
    mac = types.InlineKeyboardButton('MacOS', callback_data='mac')
    win = types.InlineKeyboardButton('Windows', callback_data='win')
    lin = types.InlineKeyboardButton('Linux', callback_data='lin')
    back = types.InlineKeyboardButton('Вернуться↩️', callback_data='back_for_inst')
    instuctmarkups.row (android, ios)
    instuctmarkups.row (mac, lin)
    instuctmarkups.row (win)
    instuctmarkups.row(back)
             
    bot.send_message(message.chat.id,
        f"""
<b>Инструкция по подключению Argent VPN 🚀</b>

1️⃣ <b>Скачайте приложение Outline.</b>

2️⃣ <b>Скопируйте ваш ключ.</b>

3️⃣ <b>Активируйте VPN:</b>
— Откройте приложение <b>Outline</b>.

— Нажмите кнопку <b>"Добавить сервер"</b> (или иконку ➕).

— Вставьте скопированный ключ и нажмите <b>"Добавить сервер"</b>.

— Нажмите кнопку <b>"Подключиться"</b>.

✅ <b>Готово! Теперь вы под защитой.</b>
""",
    parse_mode='html', disable_web_page_preview=True, reply_markup=instuctmarkups)


# поддержка
@bot.message_handler(commands=['support'])
def support_mes(message, back_target="back_to_main"):
    try:
        bot.delete_message(message.chat.id, message.message_id)
    except:
        pass
    
    supmarkup = types.InlineKeyboardMarkup()
    # В callback_data подставляем то, что пришло в функцию
    sup_back = types.InlineKeyboardButton('Вернуться↩️', callback_data=back_target)
    supmarkup.add(sup_back)
    
    bot.send_message(
        message.chat.id, 
        "<b>Тех. поддержка🆘:</b>\n\nНапишите нашему оператору: @Pyxxisss",
        parse_mode='html',
        reply_markup=supmarkup
    )

# профиль ВАЖНО
@bot.message_handler(commands=['profile'])
def show_profile(message, user_name=None, user_id=None):
    try:
        bot.delete_message(message.chat.id, message.message_id)
    except:
        pass

    # Определяем ID (если из кнопки — берем переданный, если команда — из message)
    final_id = user_id if user_id is not None else message.from_user.id

    # Определяем Имя
    if user_name:
        display_name = user_name
    else:
        # Это сработает только если человек сам написал /profile
        fn = message.from_user.first_name or ""
        ln = message.from_user.last_name or ""
        display_name = f"{fn} {ln}".strip() or "Пользователь"

    balance = db.get_user_balance(final_id)
    days_left = balance // 2

    profmarkups = types.InlineKeyboardMarkup()
    support = types.InlineKeyboardButton('Поддержка🆘', callback_data='support_from_profile')
    buy = types.InlineKeyboardButton('Пополнить баланс 💳', callback_data='buy')
    back = types.InlineKeyboardButton('Вернуться↩️', callback_data='back_main')
    gadgets = types.InlineKeyboardButton('Усторойства💻', callback_data="gadgets")
    profmarkups.row(buy)
    profmarkups.row(support, back)

    bot.send_message(message.chat.id, f'''
<b>👤 Профиль</b>
                     
<b>{display_name}, ваш баланс: {balance} руб.</b>
                    
Подписки хватит на: <b>{days_left} дней.👌</b>
                            
        ''', parse_mode='html', reply_markup=profmarkups)


        
# вкид фото
@bot.message_handler(content_types=['photo'])
def get_photo(message):
    bot.send_message(message.chat.id, 'Крутое фото👍')

# коннект
try:
    print("⏳ Подключаюсь к Telegram...")
    bot.polling(none_stop=True)
except Exception as e:
    print(f"❌ Ошибка: {e}")