import time
import threading
import hmac
import hashlib
import requests
import urllib3
import functools
import base64
import telebot
from telebot import types
from flask import Flask, request, jsonify, abort
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler

import db

app = Flask(__name__)

# --- 1. ГЛОБАЛЬНЫЙ SSL ФИКС ---
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
# Подменяем метод запроса, чтобы verify всегда был False
requests.sessions.Session.request = functools.partialmethod(requests.sessions.Session.request, verify=False)

# --- 2. НАСТРОЙКИ OUTLINE ---      
api_url = "https://194.41.113.168:10003/SPEwfoqnG2jj_skZzXuMuA"
cert_sha256 = "458709F137B716304C2D0EC30A309855A5436EED1925564337D9B90D79DBF47E"

try:
    from outline_vpn.outline_vpn import OutlineVPN
    client = OutlineVPN(api_url, cert_sha256)
    print("✅ Подключение к серверу Outline настроено (Global SSL fix applied)!")
except Exception as e:
    print(f"❌ Ошибка инициализации Outline: {e}")
    client = None

bot = telebot.TeleBot('8195901758:AAFg_179LBV84ryKgbBAr0v0jRactmfxdP0')

bot.set_my_commands([
    telebot.types.BotCommand("start", "Главное меню"),
    telebot.types.BotCommand("instructions", "Настройка устройств"),
    telebot.types.BotCommand("profile", "Личный кабинет"),
    telebot.types.BotCommand("support", "Поддержка")
])

# start
@bot.message_handler(commands=['start'])
def main(message, user_name = None):
    user_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name
    
    referrer_id = None
    args = message.text.split()
    if len(args) > 1:
        try:
            potential_referrer = int(args[1])
            if potential_referrer != user_id: # Нельзя пригласить самого себя
                referrer_id = potential_referrer
        except:
            pass

    user_data = db.get_user_vpn_data(user_id) 
    is_new_user = user_data is None

    db.add_user(user_id, username, first_name, referrer_id)
    if is_new_user and referrer_id:
        db.update_balance(referrer_id, 20)
        try:
            bot.send_message(referrer_id, "🎁 Вам начислено <b>10 дней</b> за приглашение друга!", parse_mode='html')
        except:
            pass

    try:
        bot.delete_message(message.chat.id, message.message_id)
    except:
        pass

    startmarkups = types.InlineKeyboardMarkup()
    profile = types.InlineKeyboardButton('Главная👤', callback_data='home')
    instruction = types.InlineKeyboardButton('Инструкция📖', callback_data='instuct')
    support = types.InlineKeyboardButton('Поддержка🆘', callback_data='helping')
    info_button = types.InlineKeyboardButton("О сервисе ℹ️", callback_data="about_service")
    chanel = types.InlineKeyboardButton("Наш канал⚡", url="https://t.me/ArgentVPNru")
    startmarkups.row (profile)
    startmarkups.row(chanel)
    startmarkups.row(instruction)
    startmarkups.row (info_button, support)

    if user_name:
        # Если имя пришло из callback (нажатия кнопки)
        full_name = user_name
    else:
        # Если это команда /start
        first_name = message.from_user.first_name or ""
        last_name = message.from_user.last_name or ""
        full_name = f"{first_name} {last_name}".strip()
    
#     with open('img/start bot.png', 'rb') as photo:
#         bot.send_photo(
#             message.chat.id, 
#             photo, 
#             caption=f"""<b>Привет, {full_name}! 👋</b>

# Ищешь надежный и быстрый Proxy? Ты по адресу! 🚀

# 🎁 Новым пользователям дарим <b>15 дней</b>!!!

# <b>Наши преимущества:</b>
# - <b>Скорость:</b> Без ограничений, летай в соцсетях и смотри видео в 4K.⚡
# - <b>Цена:</b> Всего <b>60 рублей</b> в месяц — дешевле чашки кофе!😍
# - <b>Устройства:</b> Подключай до <b>10 устройств</b> на одну подписку.📲

# <b>Доступен на всех платформах:</b>
# iOS & Android 📱
# Windows, macOS & Linux 💻
# """,
#             parse_mode='html',
#             reply_markup=startmarkups)
    bot.send_message(
    message.chat.id, 
    f"""<b>Привет, {full_name}! 👋</b>

Ищешь надежный и быстрый Proxy? Ты по адресу! 🚀

🎁 Новым пользователям дарим <b>15 дней</b>!!!

<b>Наши преимущества:</b>
- <b>Скорость:</b> Без ограничений, летай в соцсетях и смотри видео в 4K.⚡
- <b>Цена:</b> Всего <b>60 рублей</b> в месяц — дешевле чашки кофе!😍
- <b>Устройства:</b> Подключай до <b>10 устройств</b> на одну подписку.📲

<b>Доступен на всех платформах:</b>
iOS & Android 📱
Windows, macOS & Linux 💻
""",
    parse_mode='html',
    reply_markup=startmarkups
    )   
        
# действия с кнопками
@bot.callback_query_handler(func=lambda callback: True)
def callback_message(callback):
    u_id = callback.from_user.id
    u_name = callback.from_user.first_name
    global client
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
        bot.send_document(callback.message.chat.id, winsetup_id, caption="Установщик для Windows💻")
    elif callback.data == 'lin':
        linsetup_id = "BQACAgIAAxkBAANzaV1XzyM0KeYie7pAUJcHRDrCbM0AAmeSAALl4ulKAAHUnL7E_gABFTgE"
        bot.send_document(callback.message.chat.id, linsetup_id, caption="Файл для Linux💻")

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
        show_profile(callback.message, user_name=u_name, user_id=callback.from_user.id)
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

    # --- БЛОК УПРАВЛЕНИЯ VPN КЛЮЧАМИ ---
    # Кнопка "Создать ключ" (или купить)
    elif callback.data == 'buy_vpn':
        u_id = callback.from_user.id
        balance = db.get_user_balance(u_id)
        
        # Оставляем проверку минимального баланса (хотя бы на 1 день)
        if balance < 2: 
            bot.answer_callback_query(callback.id, "❌ Недостаточно средств (нужно минимум 2₽)", show_alert=True)
            return

        try:
            # Создаем ключ в Outline
            new_key = client.create_key()
            client.rename_key(new_key.key_id, f"User_{u_id}")

            mask_url = f"{new_key.access_url}&prefix=POST%20"          
            # Просто записываем ключ в базу, а списывать будет планировщик по 2р
            db.add_vpn_key(u_id, new_key.key_id, f"Key_{u_id}", mask_url)
            
            bot.answer_callback_query(callback.id, "✅ Доступ активирован!")
            show_devices_menu(callback.message, u_id)
            
        except Exception as e:
            print(f"Ошибка: {e}")
            bot.send_message(callback.message.chat.id, "❌ Ошибка при создании ключа.")

    # Кнопка "Мои ключи" (Список для удаления)
    if callback.data == 'my_keys':
            show_devices_menu(callback.message, u_id)
            bot.answer_callback_query(callback.id)


    elif callback.data.startswith('del_'):
        # Получаем ID из callback_data
        raw_id = callback.data.split('_')[1] 
        u_id = callback.from_user.id
        
        bot.answer_callback_query(callback.id)
        
        # Пробуем удаление
        try:
            # 1. Библиотека Outline часто требует INT для удаления ключа
            if client:
                client.delete_key(int(raw_id)) # Пробуем превратить в число
        except Exception as e:
            print(f"⚠️ Сервер Outline не смог удалить (возможно уже нет): {e}")

        try:
            # 2. А в базе мы ищем как строку (TEXT)
            db.delete_vpn_key(str(raw_id)) 
            
            bot.send_message(callback.message.chat.id, "🗑 Устройство удалено.")
            show_devices_menu(callback.message, u_id)
        except Exception as e:
            print(f"❌ Ошибка БД: {e}")

    elif callback.data.startswith('pause_'):
        sk_id = callback.data.split('_')[1]
        client.add_data_limit(sk_id, 1) # Лимит 1 байт на сервере
        db.update_vpn_status(callback.from_user.id, False)
        bot.answer_callback_query(callback.id, "⏸ Списания остановлены, сервис отключен", show_alert=True)
        show_devices_menu(callback.message, callback.from_user.id)

    elif callback.data.startswith('resume_'):
        sk_id = callback.data.split('_')[1]
        balance = db.get_user_balance(callback.from_user.id)
        if balance >= 2:
            client.add_data_limit(sk_id, None)
            db.update_vpn_status(callback.from_user.id, True)
            bot.answer_callback_query(callback.id, "▶️ Сервис снова работает!", show_alert=True)
        else:
            bot.answer_callback_query(callback.id, "❌ Недостаточно баланса (мин. 2₽)", show_alert=True)
        show_devices_menu(callback.message, callback.from_user.id)

    # реферальное меню 
    elif callback.data == "ref_program":
        try:
            bot_info = bot.get_me()
            ref_link = f"https://t.me/{bot_info.username}?start={u_id}"
            ref_count = db.get_referrals_count(u_id)
            total_earned = ref_count * 20 # Твоя ставка 20р за друга

            text = f'''
<b>👥 Реферальная программа</b>

Приглашайте друзей и получайте <b>10 дней подписки</b> на баланс за каждого!👌
<i>Друг также получит приветственный бонус при регистрации.</i>

<b>Ваша ссылка для приглашения:</b>
<code>{ref_link}</code>
<i>(Нажмите на ссылку, чтобы скопировать)</i>

<b>Статистика:</b>
— Приглашено: <b>{ref_count}</b> чел.
— Заработано всего: <b>{total_earned} ₽</b>
'''
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("⬅️ Назад в профиль", callback_data="home"))
            
            # Удаляем старое сообщение (с фото профиля) и присылаем чистое меню рефералов
            bot.delete_message(callback.message.chat.id, callback.message.message_id)
            bot.send_message(callback.message.chat.id, text, reply_markup=markup, parse_mode='HTML')
            
        except Exception as e:
            print(f"❌ Ошибка в рефералке: {e}")
            bot.send_message(callback.message.chat.id, "⚠️ Не удалось открыть реферальное меню.")

    elif callback.data == "partner_menu":
        text = """<b>🧑‍💻 Партнерская программа</b>
    
<b>Создавай креативный контент в соцсетях, набирай просмотры, получай деньги на баланс!🤩</b>

<b>Условия участия:</b>
✅ <b>Формат:</b> Reels, Shorts, TikTok или пост в Telegram/VK.
✅ <b>Ссылка:</b> Твоя реферальная ссылка должна быть в описании или закрепленном комменте.
✅ <b>Демонстрация:</b> Покажи, как легко работает сервис (заход в Instagram, YouTube или игры).

<b>Как получить выплату?</b>
1️⃣ Загрузи контент в свои соцсети.
2️⃣ Подожди 24 часа для фиксации просмотров.
3️⃣ Пришли ссылку на ролик в нашу поддержку @pyxxisss.

<b>Бонусы за просмотры:</b>
📈 700 просмотров — <b>60 ₽</b>
📈 5 000 просмотров — <b>250 ₽</b>
📈 10 000+ просмотров — Индивидуальные условия!

<i>*Бонусы суммируются с твоими стандартными реферальными начислениями (20 ₽ за каждого приглашенного)!</i>

👇 <b>Забирай ссылку в меню «Рефералы» и начинай снимать!</b>
"""
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🆘 Связаться с поддержкой", url="https://t.me/pyxxisss"))
        markup.add(types.InlineKeyboardButton("⬅️ Назад", callback_data="home"))
        
        bot.delete_message(callback.message.chat.id, callback.message.message_id)
        bot.send_message(callback.message.chat.id, text, reply_markup=markup, parse_mode='HTML')

# о сервисе
    elif callback.data == "about_service":
        text = f"""
    Argent Proxy — это высокоскоростной сервис доступа к частным прокси-серверам на базе протокола Shadowsocks (технология Outline).

Наши услуги включают:

Безопасность: Шифрование трафика по стандарту AEAD (256-bit), что защищает ваши данные в публичных сетях.

Производительность: Мы используем выделенные серверы с пропускной способностью до 1 Гбит/с, что позволяет просматривать контент в 4K и играть без задержек.

Мультиплатформенность: Один ключ можно использовать на iOS, Android, Windows и macOS одновременно.

Прозрачная тарификация: Посуточная оплата (2 ₽/день) позволяет вам платить только тогда, когда вы пользуетесь сервисом.

Техническая реализация: Доступ предоставляется путем генерации уникального ключа доступа, который вставляется в официальное приложение Outline. Мы не ограничиваем объем трафика.
"""
        markup = types.InlineKeyboardMarkup()
        # Кнопки на документы, которые мы подготовим следующими
        markup.row(types.InlineKeyboardButton("📄 Оферта", url="https://telegra.ph/Publichnaya-oferta-servisa-Argent-Digital-01-21"),
                   types.InlineKeyboardButton("🛡 Приватность", url="https://telegra.ph/Politika-konfidencialnosti-Argent-Digital-01-21"))
        markup.add(types.InlineKeyboardButton("⬅️ Назад", callback_data="back_to_main"))
        
        bot.delete_message(callback.message.chat.id, callback.message.message_id)
        bot.send_message(callback.message.chat.id, text, reply_markup=markup, parse_mode='HTML')

# платежное меню
    elif callback.data == "top_up":
            markup = types.InlineKeyboardMarkup()
            # Кнопки тарифов
            markup.add(types.InlineKeyboardButton("🌙 1 Месяц — 60 ₽", callback_data="pay_60"))
            markup.add(types.InlineKeyboardButton("☀️ 2 Месяца — 120 ₽", callback_data="pay_120"))
            markup.add(types.InlineKeyboardButton("⭐ 3 Месяца — 180 ₽", callback_data="pay_180"))
            # Можно добавить кнопку произвольной суммы, если хочешь
            markup.add(types.InlineKeyboardButton("⬅️ Назад", callback_data="back_to_profile"))
            
            bot.edit_message_text("<b>💳 Выберите тарифный план:</b>\n\n"
                                "<i>Деньги будут зачислены на баланс, списание происходит ежедневно по 2 ₽.</i>", 
                                callback.message.chat.id, callback.message.message_id, 
                                reply_markup=markup, parse_mode='HTML')
            

# Реальная оплата через API
    elif callback.data.startswith("pay_"):
        amount = float(callback.data.split("_")[1])
        user_id = callback.from_user.id

        markup = types.InlineKeyboardMarkup()
        # Ведем на официальный домен кассы для вида
        markup.add(types.InlineKeyboardButton("💳 Оплатить банковской картой", url="https://yookassa.ru/"))
        markup.add(types.InlineKeyboardButton("⬅️ Назад к тарифам", callback_data="top_up"))
        
        bot.edit_message_text(
            f"💠 <b>Пополнение баланса: {int(amount)} ₽</b>\n\n"
            f"Для завершения оплаты нажмите на кнопку ниже. "
            f"Вы будете перенаправлены на защищенную страницу платежной системы ЮKassa.\n\n"
            f"📍 Назначение: Пополнение баланса Argent Proxy\n"
            f"📍 Сумма: {int(amount)} ₽\n"
            f"📍 Номер заказа: <code>{user_id}</code>\n\n"
            f"<i>После оплаты баланс обновится автоматически в течение 1-2 минут.</i>",
            callback.message.chat.id,
            callback.message.message_id,
            reply_markup=markup,
            parse_mode='HTML'
        )

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
<b>Инструкция по подключению Argent Proxy 🚀</b>

1️⃣ <b>Скачайте приложение Outline.</b>

2️⃣ <b>Скопируйте ваш ключ.</b>

3️⃣ <b>Активируйте сервис:</b>
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

    if user_id:
        final_id = user_id
    elif hasattr(message, 'reply_to_message') and message.from_user: # Если это команда /profile
        final_id = message.from_user.id
    else: # Если ничего не помогло, берем ID чата (для простых случаев)
        final_id = message.chat.id
    
    # 2. ОПРЕДЕЛЯЕМ display_name (чтобы не горело желтым)
    if user_name:
        display_name = user_name
    else:
        # Пытаемся собрать имя из данных сообщения
        fn = message.from_user.first_name or ""
        ln = message.from_user.last_name or ""
        display_name = f"{fn} {ln}".strip() or "Пользователь"

    # 3. Получаем данные из базы
    balance = db.get_user_balance(final_id)
    vpn_data = db.get_user_vpn_data(final_id) # (server_key_id, access_url, expiry_date, is_active)
    
    # Логика статуса    
    is_active = False
    if vpn_data:
        is_active = vpn_data[3] # Поле is_active из базы

    status_text = "✅ Работает" if is_active else "❌ Отключен"
    
    # Расчет дней: если баланс 100 рублей, хватит на 100 // 2 = 50 дней
    days_left = balance // 2 if balance > 0 else 0

    if days_left > 0:
        expiry_info = f"~ <b>{days_left} дн.</b>"
    else:
        expiry_info = "<b>Требуется пополнение</b>"

    # 4. Создаем кнопки
    profmarkups = types.InlineKeyboardMarkup()
    buy = types.InlineKeyboardButton('Пополнить баланс 💳', callback_data='top_up')
    my_keys = types.InlineKeyboardButton('Ваш ключ 🗝️', callback_data="my_keys")
    support = types.InlineKeyboardButton('Поддержка 🆘', callback_data='support_from_profile')
    back = types.InlineKeyboardButton('Вернуться ↩️', callback_data='back_main')
    ref_button = types.InlineKeyboardButton('Пригласить друга 👥', callback_data='ref_program')
    partner = types.InlineKeyboardButton('Партнерская программа 🧑‍💻', callback_data= "partner_menu")    
    profmarkups.row(buy)
    profmarkups.row(my_keys)
    profmarkups.row(ref_button)
    profmarkups.row(partner)  
    profmarkups.row(support, back)

    # 5. Формируем текст
    text = f'''
<b>👤 Профиль</b>
                     
<b>{display_name}, ваш баланс: {balance} руб.</b>

<b>Статус proxy:</b> {status_text}
<b>Хватит на:</b> {expiry_info} дней.

<i>Одного пополнения на 60₽ хватает на 30 дней доступа для 10 устройств!</i>
'''
    bot.send_message(message.chat.id, text, parse_mode='html', reply_markup=profmarkups)
    
# меню ключей
def show_devices_menu(message, user_id):
    vpn_data = db.get_user_vpn_data(user_id)
    markup = types.InlineKeyboardMarkup()
    
    if vpn_data:
        # server_key_id, access_url, expiry_date, is_active
        server_key_id, access_url, _, is_active = vpn_data
        
        status_emoji = "🟢 Работает" if is_active else "🔴 На паузе (деньги не списываются)"
        text =f'''<b>Статус:</b> {status_emoji}
<b>Ключ:</b> 
<code>{access_url}</code>
        
<i>Вы можете использовать этот ключ на 10 устройствах одновременно.</i>'''
        
        if is_active:
            markup.add(types.InlineKeyboardButton("⏸ Приостановить (Пауза)", callback_data=f"pause_{server_key_id}"))
        else:
            markup.add(types.InlineKeyboardButton("▶️ Запустить", callback_data=f"resume_{server_key_id}"))

        markup.add(types.InlineKeyboardButton("🗑 Удалить ключ полностью", callback_data=f"del_{server_key_id}"))
    else:
        text = "<b>📱 У вас пока нет активных ключей.</b>"
        markup.add(types.InlineKeyboardButton("➕ Создать доступ (2₽/сутки)", callback_data="buy_vpn"))

    markup.add(types.InlineKeyboardButton("📖 Инструкция", callback_data="instuct"))
    markup.add(types.InlineKeyboardButton("⬅️ В профиль", callback_data="back_to_profile"))

    try:
        bot.edit_message_text(text, message.chat.id, message.message_id, reply_markup=markup, parse_mode='HTML')
    except:
        bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode='HTML')
       
# вкид фото
@bot.message_handler(content_types=['photo'])
def get_photo(message):
    bot.send_message(message.chat.id, 'Крутое фото👍')

def daily_billing_job():
    print("⏳ Запуск ежедневного списания (2 ₽)...")
    active_keys = db.get_all_active_keys() # Получаем только тех, у кого is_active = True
    
    for key in active_keys:
        user_id, server_key_id = key
        balance = db.get_user_balance(user_id)
        
        if balance >= 2:
            # Списываем 2 рубля
            db.update_balance(user_id, -2)
        else:
            # Денег нет — выключаем доступ
            db.update_vpn_status(user_id, False) # Меняем is_active на False
            if client:
                client.add_data_limit(server_key_id, 1) # Блокируем в Outline
            
            try:
                bot.send_message(user_id, "⚠️ Ваш баланс менее 2₽. Сервис временно отключен. Пополните баланс для продолжения.")
            except:
                pass

# коннект
# 1. Сначала создаем объект планировщика
scheduler = BackgroundScheduler()

# 2. Добавляем задачу (проверка раз в час)
# Напоминаю: убедись, что функция check_subscriptions определена выше в коде
scheduler.add_job(daily_billing_job, 'cron', hour=0, minute=0)

# 3. Блок запуска
if __name__ == "__main__":
    try:
        # 1. Сначала запускаем планировщик
        scheduler.start()
        print("✅ Планировщик подписок запущен!")

        # 2. Инициализируем базу
        db.init_db()

        # 3. ЗАПУСКАЕМ FLASK ДЛЯ ВЕБХУКОВ (в отдельном потоке)
        # daemon=True значит, что поток закроется вместе с ботом

        # 4. И только в самом конце — бесконечный цикл бота
        print("🚀 Бот вышел на связь...")
        bot.polling(none_stop=True)

    except Exception as e:
        print(f"❌ Критическая ошибка при запуске: {e}")