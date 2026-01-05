import telebot
from telebot import types

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
def main(message):
    startmarkups = types.InlineKeyboardMarkup()
    profile = types.InlineKeyboardButton('Главная👤', callback_data='popa')
    instruction = types.InlineKeyboardButton('Инструкция📖', callback_data='popa')
    support = types.InlineKeyboardButton('Поддержка🆘', callback_data='popa')
    startmarkups.row (profile)
    startmarkups.row (instruction, support)

    # Собираем части имени, только если они существуют
    first_name = message.from_user.first_name or ""
    last_name = message.from_user.last_name or ""
    
    # Объединяем и убираем лишние пробелы по краям
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
        
# вкид фото
@bot.message_handler(content_types=['photo'])
def get_photo(message):
    bot.reply_to(message, 'Красивое фото😍')

# коннект
try:
    print("⏳ Подключаюсь к Telegram...")
    bot.polling(none_stop=True)
except Exception as e:
    print(f"❌ Ошибка: {e}")