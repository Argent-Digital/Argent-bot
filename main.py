import threading
import random
import uuid
import requests
import urllib3
import gc
import time
import functools
import telebot
from telebot import types
from flask import Flask, request, jsonify, abort
from apscheduler.schedulers.background import BackgroundScheduler
from yookassa.domain.notification import WebhookNotificationFactory
from yookassa import Configuration, Payment

import db

Configuration.configure('1254528', 'live_6aco-HloIFi4SFGpCXYITwcGnguz26uhEZ4V1imd3zk')
app = Flask(__name__)

@app.route('/yookassa_webhook', methods=['POST'])
def webhook():
    event_json = request.json
    try:
        notification_object = WebhookNotificationFactory().create(event_json)
        response_object = notification_object.object

        if notification_object.event == 'payment.succeeded':
            # 1. Получаем данные платежа
            amount = int(float(response_object.amount.value))
            user_id = response_object.metadata.get('user_id')

            if user_id:
                # 2. Обновляем баланс в базе данных
                db.update_balance(int(user_id), amount)
                print(f"✅ Баланс юзера {user_id} пополнен на {amount} руб.")
                
                # 3. ОТПРАВЛЯЕМ СООБЩЕНИЕ ПОЛЬЗОВАТЕЛЮ
                try:
                    bot.send_message(
                        user_id, 
                        f"💳 <b>Оплата прошла успешно!</b>\n\n"
                        f"Ваш баланс пополнен на <b>{amount} ₽</b>.\n"
                        f"Спасибо, что пользуетесь Argent Proxy! 🚀",
                        parse_mode='HTML'
                    )
                except Exception as send_error:
                    print(f"❌ Не удалось отправить сообщение юзеру: {send_error}")
            
        return 'OK', 200
    except Exception as e:
        print(f"❌ Ошибка в вебхуке: {e}")
        return 'Error', 400

def create_payment(user_id, amount):
    idempotency_key = str(uuid.uuid4())
    payment = Payment.create({
        "amount": {
            "value": str(amount),
            "currency": "RUB"
        },
        "confirmation": {
            "type": "redirect",
            "return_url": "https://t.me/ArgentVPNbot"
        },
        "capture": True,
        "description": f"Пополнение баланса Argent Proxy",
        "metadata": {
            "user_id": user_id  # ОБЯЗАТЕЛЬНО ПЕРЕДАЕМ ID
        }
    }, idempotency_key)

    return payment.confirmation.confirmation_url

# --- 1. ГЛОБАЛЬНЫЙ SSL ФИКС ---
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
# Подменяем метод запроса, чтобы verify всегда был False
requests.sessions.Session.request = functools.partialmethod(requests.sessions.Session.request, verify=False)

# --- 2. НАСТРОЙКИ OUTLINE ---      
api_url = "https://194.41.113.168:62468/j7UAACvTcgwC8fOFU3qojg"
cert_sha256 = "21C5C9A862E9BCE996E018759A7A448FA6504804459F00D52D8B77529798E85C"

try:
    from outline_vpn.outline_vpn import OutlineVPN
    client = OutlineVPN(api_url, cert_sha256)
    print("✅ Подключение к серверу Outline настроено (Global SSL fix applied)!")
except Exception as e:
    print(f"❌ Ошибка инициализации Outline: {e}")
    client = None

bot = telebot.TeleBot('8195901758:AAFg_179LBV84ryKgbBAr0v0jRactmfxdP0')
START_PHOTO_ID = None  # Сюда бот сам запишет ID после первой отправки

# start
@bot.message_handler(commands=['start'])
def main(message, user_name = None):
    global START_PHOTO_ID # Обращаемся к нашей глобальной переменной
    
    if hasattr(message, 'from_user') and message.from_user.is_bot:
        user_id = message.chat.id # В личке ID чата и ID юзера СОВПАДАЮТ
    else:
        user_id = message.from_user.id

    if user_name:
        final_name = user_name
    elif message.from_user and not message.from_user.is_bot:
        final_name = message.from_user.first_name
    else:
        final_name = "Пользователь"

    username = message.chat.username if hasattr(message.chat, 'username') else None
    if not username and message.from_user and not message.from_user.is_bot:
        username = message.from_user.username
    
    # Реферальная логика
    referrer_id = None
    if hasattr(message, 'text') and message.text:
        args = message.text.split()
        if len(args) > 1:
            try:
                potential_referrer = int(args[1])
                if potential_referrer != user_id:
                    referrer_id = potential_referrer
            except:
                pass

    is_new_user = db.get_user_balance(user_id) is None
    print(f"Юзер {user_id} новый? {is_new_user}") # ПРОВЕРКА

    db.add_user(user_id, username, final_name, referrer_id)

    if not db.get_user_status(user_id):
        send_captcha(message)
        return

    if is_new_user and referrer_id:
        db.update_balance(referrer_id, 20)
        try:
            bot.send_message(referrer_id, "🎁 Вам начислено <b>20 ₽</b> за приглашение друга!", parse_mode='html')
        except:
            pass

    try:
        bot.delete_message(message.chat.id, message.message_id)
    except:
        pass

    # Клавиатура
    startmarkups = types.InlineKeyboardMarkup()
    startmarkups.row(types.InlineKeyboardButton('Подключить 📲', callback_data='my_keys'))
    startmarkups.row(types.InlineKeyboardButton('Профиль👤', callback_data='home'))
    startmarkups.row(types.InlineKeyboardButton("О сервисе ℹ️", callback_data="about_service"), 
                     types.InlineKeyboardButton("канал⚡", url="https://t.me/ArgentVPNru"))

    # Формируем имя
    full_name = final_name
    
    caption_text = f"""<b>Привет, {full_name}! 👋</b>

Ищешь надежный и быстрый Proxy? Ты по адресу! 🚀

🎁 Новым пользователям дарим <b>15 дней</b>!!!

<b>Доступен на всех платформах:</b>
iOS & Android 📱
Windows | macOS | Linux 💻
"""

    # --- ОПТИМИЗИРОВАННАЯ ОТПРАВКА ФОТО ---
    try:
        if START_PHOTO_ID:
            # Если ID уже есть в памяти, отправляем "ссылкой" (мгновенно)
            bot.send_photo(message.chat.id, START_PHOTO_ID, caption=caption_text, 
                           parse_mode='html', reply_markup=startmarkups)
        else:
            # Если это первый запуск после рестарта, читаем файл с диска
            with open('img/re_Start.png', 'rb') as photo:
                sent_msg = bot.send_photo(message.chat.id, photo, caption=caption_text, 
                                          parse_mode='html', reply_markup=startmarkups)
                # Сохраняем полученный от Telegram ID в переменную
                START_PHOTO_ID = sent_msg.photo[-1].file_id
                print(f"📸 Фото загружено на сервер Telegram. File_ID сохранен.")
    except Exception as e:
        print(f"❌ Ошибка при отправке фото: {e}")
        # Запасной вариант: отправить просто текстом, если фото удалено или недоступно
        bot.send_message(message.chat.id, caption_text, parse_mode='html', reply_markup=startmarkups)

def send_captcha(message):
    num1 = random.randint(1, 9)
    num2 = random.randint(1, 9)
    correct_answer = num1 + num2
    
    # Генерируем варианты ответов
    options = {correct_answer, correct_answer + 1, correct_answer - 1}
    # Превращаем в список и перемешиваем
    options = list(options)
    random.shuffle(options)
    
    markup = types.InlineKeyboardMarkup()
    btns = [types.InlineKeyboardButton(str(opt), callback_data=f"captcha_{opt}_{correct_answer}") for opt in options]
    markup.add(*btns)
    
    text = f"🤖 <b>Проверка на робота!</b>\nСколько будет {num1} + {num2}?"
    bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode='HTML')
        
# действия с кнопками
@bot.callback_query_handler(func=lambda callback: True)
def callback_message(callback):
    u_id = callback.from_user.id
    u_name = callback.from_user.first_name

    if not db.get_user_status(u_id) and not callback.data.startswith('captcha_'):
        # 1. Сначала удаляем старое сообщение, на которое нажал юзер
        try:
            bot.delete_message(callback.message.chat.id, callback.message.message_id)
        except:
            pass
        
        # 2. Сразу же присылаем ему капчу
        send_captcha(callback.message)
        
        # 3. Выдаем уведомление сверху
        bot.answer_callback_query(callback.id, "🤖 Пожалуйста, пройдите проверку на робота")
        return

# --- БЛОК КАПЧИ ---
    if callback.data.startswith('captcha_'):
        _, user_answer, correct_answer = callback.data.split('_')
        
        if user_answer == correct_answer:
            # 1. Сначала узнаем, был ли юзер уже подтвержден
            was_verified = db.get_user_status(u_id)
            
            # 2. Подтверждаем юзера (ставим is_verified = True)
            db.set_user_verified(u_id)
            bot.answer_callback_query(callback.id, "✅ Проверка пройдена!")
            
            # 3. ЛОГИКА НАЧИСЛЕНИЯ (только если это ПЕРВОЕ прохождение капчи)
            if not was_verified:
                # ВОТ ТУТ используем новую функцию из db.py
                ref_id = db.get_referrer(u_id) 
                
                if ref_id:
                    db.update_balance(ref_id, 20)
                    try:
                        bot.send_message(ref_id, "🎁 Вам начислено <b>20 ₽</b> за приглашение друга!", parse_mode='html')
                    except Exception as e:
                        print(f"Не удалось отправить уведомление рефереру: {e}")

            bot.delete_message(callback.message.chat.id, callback.message.message_id)
            
            # 4. После успеха запускаем main, чтобы показать меню
            main(callback.message, user_name=callback.from_user.first_name)
            
        else:
            bot.answer_callback_query(callback.id, "❌ Неверно, попробуй еще раз!", show_alert=True)
            bot.delete_message(callback.message.chat.id, callback.message.message_id)
            send_captcha(callback.message)
        return

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
        bot.send_message(
            callback.message.chat.id, 
            "Ссылка на установку в Google Play 👉: <a href='https://play.google.com/store/apps/details?id=org.outline.android.client&pcampaignid=web_share'><b>Установить</b></a>",
            parse_mode='html', disable_web_page_preview=True
        )
    elif callback.data == 'ios':
        bot.send_message(callback.message.chat.id, "Ссылка на установку в App Store 👉: <a href='https://apps.apple.com/us/app/outline-app/id1356177741'><b>Установить</b></a>", parse_mode='html', disable_web_page_preview=True)
    elif callback.data == 'mac':
        bot.send_message(callback.message.chat.id, "Ссылка на установку в App Store для Mac 👉: <a href='https://apps.apple.com/us/app/outline-secure-internet-access/id1356178125?mt=12'><b>Установить</b></a>", parse_mode='html', disable_web_page_preview=True)
    elif callback.data == 'win':
        winsetup_id = "BQACAgIAAxkBAANsaV1LoQKyU_tHKMIW3QqwZjTVQfcAAneRAALl4ulKC4UWPPhd4m84BA"
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
        
        if balance < 2: 
            bot.answer_callback_query(callback.id, "❌ Недостаточно средств (нужно минимум 2₽)", show_alert=True)
            return

        try:
            # 1. Списываем оплату за первый день сразу (защита от абуза пересозданием)
            db.update_balance(u_id, -2)
            
            # 2. Жестко чистим старую запись, если она есть
            db.delete_vpn_key_final(u_id) 
            
            # 3. Создаем новый ключ в Outline
            new_key = client.create_key()
            client.rename_key(new_key.key_id, f"User_{u_id}")
            mask_url = f"{new_key.access_url}&prefix=POST%20"          
            
            # 4. Записываем новый ключ в базу
            db.add_vpn_key(u_id, new_key.key_id, f"Key_{u_id}", mask_url)
            
            bot.answer_callback_query(callback.id, "✅ Доступ оплачен и активирован!")
            show_devices_menu(callback.message, u_id)
            
        except Exception as e:
            # Если что-то пошло не так (например, API Outline не ответил), 
            # по-хорошему тут надо бы вернуть 2 рубля юзеру:
            # db.update_balance(u_id, 2) 
            print(f"❌ Ошибка при покупке: {e}")
            bot.send_message(callback.message.chat.id, "❌ Произошла ошибка. Баланс не списан или будет возвращен.")

    # Кнопка "Мои ключи" (Список для удаления)
    if callback.data == 'my_keys':
            show_devices_menu(callback.message, u_id)
            bot.answer_callback_query(callback.id)


    elif callback.data.startswith('del_'):
        u_id = callback.from_user.id
        # vpn_data: (server_key_id, access_url, expiry_date, is_active)
        vpn_data = db.get_user_vpn_data(u_id)
        
        if vpn_data:
            try:
                # 1. Удаляем ключ физически из Outline
                client.delete_key(vpn_data[0])
            except:
                pass # Если на сервере уже нет, просто идем дальше
            
            # 2. Удаляем запись из базы полностью
            db.delete_vpn_key_final(u_id)
            
            bot.answer_callback_query(callback.id, "🗑 Ключ полностью удален")
            # Возвращаем пользователя в меню создания
            show_devices_menu(callback.message, u_id)   

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
            markup.add(types.InlineKeyboardButton("⬅️ Назад", callback_data="back_to_profile"))

            try:
                bot.delete_message(callback.message.chat.id, callback.message.message_id)
            except:
                pass
            
            bot.send_message(callback.message.chat.id,  
                         "<b>💳 Выберите тарифный план:</b>\n\n"
                         "<i>Деньги будут зачислены на баланс, списание происходит ежедневно по 2 ₽.</i>", 
                         reply_markup=markup, parse_mode='HTML')

    elif callback.data.startswith("pay_"):
        amount = int(float(callback.data.split("_")[1])) # ЮKassa любит целые числа или строки
        user_id = callback.from_user.id

        try:
            # 1. Генерируем реальную ссылку через API ЮKassa
            payment_url = create_payment(user_id, amount)

            markup = types.InlineKeyboardMarkup()
            # 2. Подставляем сгенерированную ссылку в кнопку
            markup.add(types.InlineKeyboardButton("💳 Перейти к оплате", url=payment_url))
            markup.add(types.InlineKeyboardButton("⬅️ Назад к тарифам", callback_data="top_up"))
            
            bot.edit_message_text(
                f"💠 <b>Пополнение баланса: {amount} ₽</b>\n\n"
                f"Нажмите кнопку ниже, чтобы перейти на защищенную страницу оплаты <b>ЮKassa</b>.\n\n"
                f"📍 <b>Сумма:</b> {amount} ₽\n"
                f"📍 <b>ID пользователя:</b> <code>{user_id}</code>\n\n"
                f"<i>После подтверждения платежа банком, средства будут зачислены на ваш баланс автоматически.</i>",
                callback.message.chat.id,
                callback.message.message_id,
                reply_markup=markup,
                parse_mode='HTML'
            )
        except Exception as e:
            print(f"Ошибка при создании платежа: {e}")
            bot.answer_callback_query(callback.id, "❌ Ошибка при формировании счета. Попробуйте позже.")

    elif callback.data == "confirm_send":
        if callback.from_user.id != ADMIN_ID: # Еще одна проверка прямо перед запуском
            return
        # Убираем кнопки у превью
        bot.edit_message_reply_markup(callback.message.chat.id, callback.message.message_id, reply_markup=None)
        bot.send_message(callback.message.chat.id, "🚀 Рассылка запущена...")
        
        # Получаем юзеров и запускаем поток
        all_users = db.get_all_user_ids()
        # Проверяем, что сообщение вообще есть в памяти
        if 'broadcast_message' in globals():
            threading.Thread(target=send_broadcast, args=(broadcast_message, all_users)).start()
        else:
            bot.send_message(callback.message.chat.id, "❌ Ошибка: сообщение потеряно. Попробуй заново.")
        
    elif callback.data == "cancel_send":
        # Убираем кнопки
        bot.edit_message_reply_markup(callback.message.chat.id, callback.message.message_id, reply_markup=None)
        bot.send_message(callback.message.chat.id, "🚫 Рассылка отменена.")

    elif callback.data == "adm_mes":
        broadcast_command(callback.message)

    elif callback.data == "gift":
        msg = bot.send_message(callback.message.chat.id, "👤 Введи **ID** пользователя, которому хочешь начислить баланс:", parse_mode='Markdown')
        bot.register_next_step_handler(msg, process_gift_id)


# раздел с инструкцией
MANUAL_PHOTO_ID = None

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
             

    text = f"""
<b>Инструкция по подключению Argent Proxy 🚀</b>

1️⃣ <b>Скачайте приложение Outline.</b>

2️⃣ <b>Скопируйте ваш ключ.</b>

3️⃣ <b>Активируйте сервис:</b>
— Откройте приложение <b>Outline</b>.

— Нажмите кнопку <b>"Добавить сервер"</b> (или иконку ➕).

— Вставьте скопированный ключ и нажмите <b>"Добавить сервер"</b>.

— Нажмите кнопку <b>"Подключиться"</b>.

✅ <b>Готово! Теперь вы под защитой.</b>
"""
    
    global MANUAL_PHOTO_ID
    # --- ОПТИМИЗИРОВАННАЯ ОТПРАВКА ФОТО ---
    try:
        if MANUAL_PHOTO_ID:
            # Если ID уже есть в памяти, отправляем "ссылкой" (мгновенно)
            bot.send_photo(message.chat.id, MANUAL_PHOTO_ID, caption=text, 
                           parse_mode='html', reply_markup=instuctmarkups)
        else:
            # Если это первый запуск после рестарта, читаем файл с диска
            with open('img/inst.png', 'rb') as photo:
                sent_msg = bot.send_photo(message.chat.id, photo, caption=text, 
                                          parse_mode='html', reply_markup=instuctmarkups)
                # Сохраняем полученный от Telegram ID в переменную
                MANUAL_PHOTO_ID = sent_msg.photo[-1].file_id
                print(f"📸 Фото загружено на сервер Telegram. File_ID сохранен.")
    except Exception as e:
        print(f"❌ Ошибка при отправке фото: {e}")
        # Запасной вариант: отправить просто текстом, если фото удалено или недоступно
        bot.send_message(message.chat.id, text, parse_mode='html', reply_markup=instuctmarkups)


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
PROFILE_PHOTO_ID = None

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
    my_keys = types.InlineKeyboardButton('Подключение 📲', callback_data="my_keys")
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

    channel_link = "https://t.me/ArgentVPNru"

    text = f'''
<b>👤 Профиль</b>
                     
<b>{display_name}, ваш баланс: {balance} руб.</b>

<b>Статус proxy:</b> {status_text}
<b>Хватит на:</b> {expiry_info} дней.

<i>Одного пополнения на 60₽ хватает на 30 дней доступа для 10 устройств!</i>

<b>⚡ Наш канал: <a href='{channel_link}'>Подписаться</a></b>
'''
    
    global PROFILE_PHOTO_ID
    # --- ОПТИМИЗИРОВАННАЯ ОТПРАВКА ФОТО ---
    try:
        if PROFILE_PHOTO_ID:
            # Если ID уже есть в памяти, отправляем "ссылкой" (мгновенно)
            bot.send_photo(message.chat.id, PROFILE_PHOTO_ID, caption=text, 
                           parse_mode='html', reply_markup=profmarkups)
        else:
            # Если это первый запуск после рестарта, читаем файл с диска
            with open('img/profile.png', 'rb') as photo:
                sent_msg = bot.send_photo(message.chat.id, photo, caption=text, 
                                          parse_mode='html', reply_markup=profmarkups)
                # Сохраняем полученный от Telegram ID в переменную
                PROFILE_PHOTO_ID = sent_msg.photo[-1].file_id
                print(f"📸 Фото загружено на сервер Telegram. File_ID сохранен.")
    except Exception as e:
        print(f"❌ Ошибка при отправке фото: {e}")
        # Запасной вариант: отправить просто текстом, если фото удалено или недоступно
        bot.send_message(message.chat.id, text, parse_mode='html', reply_markup=profmarkups)

# меню ключей
KEY_PHOTO_ID = None

def show_devices_menu(message, user_id):
    global KEY_PHOTO_ID
    vpn_data = db.get_user_vpn_data(user_id)
    markup = types.InlineKeyboardMarkup()

    # Если записи в базе вообще нет — предлагаем создать
    if not vpn_data: 
        text = "<b>📱 У вас пока нет созданных ключей.</b>"
        markup.add(types.InlineKeyboardButton("➕ Создать доступ (2₽/сутки)", callback_data="buy_vpn"))
    else:
        # vpn_data: (server_key_id, access_url, expiry_date, is_active)
        server_key_id, access_url, _, is_active = vpn_data

        text = f'''
<b>🚀 Ваш доступ готов!</b>

<b>1. Скопируйте этот ключ:</b> 
<code>{access_url}</code>
<b>2. Скачайте приложение Outline.</b>
<b>3. Нажмите «Добавить сервер» и вставьте ключ.</b>

<i>Вы можете использовать этот ключ на 10 устройствах одновременно.</i>'''
        markup.add(types.InlineKeyboardButton("🗑 Удалить ключ полностью", callback_data=f"del_{server_key_id}"))

    # Общие кнопки
    markup.row(types.InlineKeyboardButton("📖 Установить приложение", callback_data="instuct"))
    markup.row(types.InlineKeyboardButton("⬅️ В профиль", callback_data="back_to_profile"))

    try:
        bot.delete_message(message.chat.id, message.message_id)
    except:
        pass

        # --- ОПТИМИЗИРОВАННАЯ ОТПРАВКА ФОТО ---
    try:
        if KEY_PHOTO_ID:
            # Если ID уже есть в памяти, отправляем "ссылкой" (мгновенно)
            bot.send_photo(message.chat.id, KEY_PHOTO_ID, caption=text, 
                           parse_mode='html', reply_markup=markup)
        else:
            # Если это первый запуск после рестарта, читаем файл с диска
            with open('img/key_menu.png', 'rb') as photo:
                sent_msg = bot.send_photo(message.chat.id, photo, caption=text, 
                                          parse_mode='html', reply_markup=markup)
                # Сохраняем полученный от Telegram ID в переменную
                KEY_PHOTO_ID = sent_msg.photo[-1].file_id
                print(f"📸 Фото загружено на сервер Telegram. File_ID сохранен.")
    except Exception as e:
        print(f"❌ Ошибка при отправке фото: {e}")
        # Запасной вариант: отправить просто текстом, если фото удалено или недоступно
        bot.send_message(message.chat.id, text, parse_mode='html', reply_markup=markup)

# Админ команды
ADMIN_ID = 1306570088  

# админ команда на зачисление
def process_gift_id(message):
    try:
        target_id = int(message.text)
        msg = bot.send_message(message.chat.id, f"💰 Теперь введи **сумму** для начисления пользователю `{target_id}`:", parse_mode='Markdown')
        # Передаем target_id в следующий шаг через лямбду
        bot.register_next_step_handler(msg, lambda m: process_gift_amount(m, target_id))
    except ValueError:
        bot.send_message(message.chat.id, "❌ ID должен быть числом. Попробуй еще раз зайти через кнопку.")

def process_gift_amount(message, target_id):
    try:
        amount = int(message.text)
        
        # Твоя логика обновления БД
        # Убедись, что метод update_balance существует в твоем объекте db
        db.update_balance(target_id, amount) 

        # Уведомление юзеру
        success_text = f"""
💰 <b>Баланс пополнен!</b>

Администрация зачислила вам <b>{amount}₽</b> на внутренний счет.
Используйте их для продления или покупки новых ключей.

<i>Спасибо, что вы с нами!</i> 🚀
"""
        try:
            bot.send_message(target_id, success_text, parse_mode='HTML')
            bot.send_message(message.chat.id, f"✅ Успешно! {amount}₽ начислено юзеру {target_id}")
        except Exception as e:
            bot.send_message(message.chat.id, f"✅ Баланс пополнен, но не удалось уведомить юзера: {e}")

    except ValueError:
        bot.send_message(message.chat.id, "❌ Сумма должна быть числом. Начни заново с нажатия кнопки.")

# админ команда на рассылку
def send_broadcast(admin_msg, user_ids):
    count = 0
    blocked = 0
    
    for uid in user_ids:
        try:
            # Копируем сообщение админа юзеру (текст, медиа, кнопки — всё сохранится)
            bot.copy_message(chat_id=uid, from_chat_id=admin_msg.chat.id, message_id=admin_msg.message_id)
            count += 1
            
            # Пауза 0.1 сек (10 сообщений в секунду), чтобы Telegram не забанил
            time.sleep(0.05)            
        except Exception as e:
            # Сюда попадут те, кто заблокировал бота
            blocked += 1
            print(f"Ошибка при отправке пользователю {uid}: {e}")
            
    # Когда цикл закончился, пишем админу отчет
    bot.send_message(admin_msg.chat.id, f"✅ Рассылка завершена!\n\n📈 Успешно: {count}\n🚫 Заблокировали бота: {blocked}")

def broadcast_command(message):
    if message.from_user.id == ADMIN_ID:
        msg = bot.send_message(message.chat.id, "Отправь пост, который хочешь разослать:")
        bot.register_next_step_handler(msg, confirm_broadcast)

# 2. Показываем превью и кнопки
def confirm_broadcast(message):
    if message.from_user.id != ADMIN_ID:
        return
    
    global broadcast_message
    broadcast_message = message # Запоминаем пост

    markup = types.InlineKeyboardMarkup()
    btn_yes = types.InlineKeyboardButton("✅ Да, рассылаем", callback_data="confirm_send")
    btn_no = types.InlineKeyboardButton("❌ Отмена", callback_data="cancel_send")
    markup.add(btn_yes, btn_no)

    # ОБЯЗАТЕЛЬНО: Отправляем админу вопрос с кнопками
    bot.send_message(message.chat.id, "Пост принят. Начинаем рассылку?", reply_markup=markup)

@bot.message_handler(commands=['pltn'])
def admin_dashboard(message):
    if message.from_user.id != ADMIN_ID:
        return

    s = db.get_mega_stats()
    text = (
        "💠 **Управление ArgentVPN**\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "👥 **Аудитория:**\n"
        f"├ Юзеров в БД: `{s['users']}`"
        f"└ Активных ключей: `{s['keys']}`\n"
        "📡 **Трафик (Today):**\n"
        f"├ Входящий: `{s['rx']} GiB`"
        f"├ Исходящий: `{s['tx']} GiB`\n"
        f"└ **Всего: {s['traffic']} GiB**\n"
        "━━━━━━━━━━━━━━━━━━\n"
    )

    markups = types.InlineKeyboardMarkup()
    mes = types.InlineKeyboardButton("Рассылка", callback_data="adm_mes")
    bal = types.InlineKeyboardButton("Зачисление", callback_data="gift")
    markups.row(mes, bal)

    bot.send_message(message.chat.id, text, parse_mode="Markdown", reply_markup=markups)

# вкид фото
@bot.message_handler(content_types=['photo'])
def get_photo(message):
    bot.send_message(message.chat.id, 'Крутое фото👍')

# биллинг
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

# --- НАСТРОЙКА ПЛАНИРОВЩИКА ---
def clear_memory():
    print("🧹 Принудительная очистка памяти...")
    gc.collect()

# 1. Создаем объект планировщика
scheduler = BackgroundScheduler()

# 2. Добавляем задачи
# Ежедневное списание в 00:00
scheduler.add_job(daily_billing_job, 'cron', hour=0, minute=0)
# Очистка памяти каждые 30 минут (интервальная задача)
scheduler.add_job(clear_memory, 'interval', minutes=30)

# --- БЛОК ЗАПУСКА ---
if __name__ == "__main__":
    try:
        # 1. Сначала запускаем планировщик (он теперь следит и за деньгами, и за памятью)
        scheduler.start()
        print("✅ Планировщик запущен (списания + очистка памяти)!")

        # 2. Инициализируем базу
        db.init_db()

        # 3. ЗАПУСКАЕМ FLASK ДЛЯ ВЕБХУКОВ
        flask_thread = threading.Thread(
            target=lambda: app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)
        )
        flask_thread.daemon = True 
        flask_thread.start()
        print("✅ Flask-сервер для ЮKassa запущен на порту 5000!")

        # 4. Основной цикл бота
        print("🚀 Бот вышел на связь...")
        bot.polling(none_stop=True)

    except Exception as e:
        print(f"❌ Критическая ошибка при запуске: {e}")