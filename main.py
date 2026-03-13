import os
import threading
import random
import uuid
import requests
import urllib3
import gc
import time
import pytz
from datetime import datetime
import functools
import telebot
from telebot import types
from pytz import timezone
from xui_api import XUIPanel
from flask import Flask, request, jsonify, abort
from apscheduler.schedulers.background import BackgroundScheduler
from yookassa.domain.notification import WebhookNotificationFactory
from yookassa import Configuration, Payment

from dotenv import load_dotenv

load_dotenv()

import db

xui = XUIPanel(
    base_url= os.getenv("ux_url"), 
    username= os.getenv("ux_username"), 
    password= os.getenv("ux_pass")
) #vless conf

Configuration.configure(os.getenv("shop_id"), os.getenv("Ykassa_key")) #yokassa
app = Flask(__name__)

@app.route('/yookassa_webhook', methods=['POST'])
def webhook():
    event_json = request.json
    try:
        notification_object = WebhookNotificationFactory().create(event_json)
        response_object = notification_object.object

        if notification_object.event == 'payment.succeeded':
            # 1. pull data payment
            amount = int(float(response_object.amount.value))
            user_id = response_object.metadata.get('user_id')

            if user_id:
                # 2. ubdate balance in db
                db.update_balance(int(user_id), amount)
                print(f"✅ Баланс юзера {user_id} пополнен на {amount} руб.")
                
                # 3. send messagr user
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

# pay data for hook
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
            "user_id": user_id
        }
    }, idempotency_key)

    return payment.confirmation.confirmation_url

# --- 1. SSL fix ---
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
requests.sessions.Session.request = functools.partialmethod(requests.sessions.Session.request, verify=False)

# --- 2. conf OUTLINE ---      
api_url = os.getenv("Out_url")
cert_sha256 = os.getenv("Out_cert")

try:
    from outline_vpn.outline_vpn import OutlineVPN
    client = OutlineVPN(api_url, cert_sha256)
    print("✅ Подключение к серверу Outline настроено (Global SSL fix applied)!")
except Exception as e:
    print(f"❌ Ошибка инициализации Outline: {e}")
    client = None

bot = telebot.TeleBot(os.getenv("bot_token"))
START_PHOTO_ID = None 

broadcast_message = None

# start
@bot.message_handler(commands=['start'])
def main(message, user_name = None, user_login = None):
    global START_PHOTO_ID
    
    # 1. clear step
    bot.clear_step_handler_by_chat_id(chat_id=message.chat.id)

    user_id = message.chat.id 

    # 2. search name user
    if user_name:
        final_name = user_name
    elif message.from_user:
        final_name = message.from_user.first_name
    else:
        final_name = "Пользователь"

    # 3. username
    if user_login:
        username = user_login
    elif message.from_user and not message.from_user.is_bot:
        username = message.from_user.username
    else:
        username = None

    safe_username = (username[:50] if username else None)
    
    # 4. referral
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

    # 5. check new user
    is_new_user = db.get_user_balance(user_id) is None
    print(f"Юзер {user_id} новый? {is_new_user}") 

    db.add_user(user_id, safe_username, final_name, referrer_id)

    # 6. send message refferal
    if is_new_user and referrer_id:
        db.update_balance(referrer_id, 30)
        try:
            bot.send_message(referrer_id, "💵 Вам начислено <b>30 ₽</b> за приглашение друга!", parse_mode='html')
        except:
            pass

    # 7. del message for clean char
    try:
        bot.delete_message(message.chat.id, message.message_id)
    except:
        pass

    startmarkups = types.InlineKeyboardMarkup()
    startmarkups.row(types.InlineKeyboardButton('Подключить 📲', callback_data='my_keys'))
    startmarkups.row(types.InlineKeyboardButton('Профиль👤', callback_data='home'))
    startmarkups.row(types.InlineKeyboardButton("О сервисе ℹ️", callback_data="about_service"), 
                     types.InlineKeyboardButton("канал⚡", url="https://t.me/ArgentVPNru"))

    caption_text = f"""<b>Привет, {final_name}! 👋</b>

Ищешь надежный и быстрый Proxy? Ты по адресу! 🛡️

🎁 Новым пользователям дарим <b>15 дней</b>!!!

<b>Доступен на всех платформах:</b>
iOS & Android 📱
Windows | macOS | Linux 💻
"""

    # 8. send photo
    try:
        if START_PHOTO_ID:
            bot.send_photo(message.chat.id, START_PHOTO_ID, caption=caption_text, 
                           parse_mode='html', reply_markup=startmarkups)
        else:
            with open('img/re_Start.png', 'rb') as photo:
                sent_msg = bot.send_photo(message.chat.id, photo, caption=caption_text, 
                                          parse_mode='html', reply_markup=startmarkups)
                START_PHOTO_ID = sent_msg.photo[-1].file_id
    except Exception as e:
        print(f"❌ Ошибка при отправке фото: {e}")
        bot.send_message(message.chat.id, caption_text, parse_mode='html', reply_markup=startmarkups)

# button
@bot.callback_query_handler(func=lambda callback: True)
def callback_message(callback):
    u_id = callback.from_user.id

    global client
    if callback.data == "home":
        # pull data user
        u_name = f"{callback.from_user.first_name or ''} {callback.from_user.last_name or ''}".strip()
        u_id = callback.from_user.id
        
        # push in func
        show_profile(callback.message, user_name=u_name, user_id=u_id)
        bot.answer_callback_query(callback.id)

    elif callback.data == 'instruct':       
        send_instruction_menu(callback.message)

    elif callback.data == "instvless":
        inst_vless(callback.message)

    # url instructions
    # for outline
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

    # for vless
    elif callback.data == 'androidv':
        bot.send_message(
            callback.message.chat.id, 
            "Ссылка на установку в Google Play 👉: <a href='https://play.google.com/store/apps/details?id=com.v2raytun.android'><b>Установить</b></a>",
            parse_mode='html', disable_web_page_preview=True
        )
    elif callback.data == 'iosv':
        bot.send_message(callback.message.chat.id, "Ссылка на установку в App Store 👉: <a href='https://apps.apple.com/app/id6476628951'><b>Установить</b></a>", parse_mode='html', disable_web_page_preview=True)
    elif callback.data == 'macv':
        bot.send_message(callback.message.chat.id, "Ссылка на установку в App Store для Mac 👉: <a href='https://apps.apple.com/us/app/v2raytun/id6476628951'><b>Установить</b></a>", parse_mode='html', disable_web_page_preview=True)
    elif callback.data == 'winv':
        winsetup_id = "BQACAgIAAxkBAAIRnmmca7oxnbPjjhh9QOSGInApbkilAAJTkAACeWLpSARAM4oHPdVxOgQ"
        bot.send_document(callback.message.chat.id, winsetup_id, caption="Установщик для Windows💻")
    elif callback.data == 'linv':
        bot.send_document(callback.message.chat.id, "Ссылка на установку через репозиторий 👉: <a href='https://github.com/MatsuriDayo/nekoray/releases'><b>Установить</b></a>", parse_mode='html', disable_web_page_preview=True)

    elif callback.data== 'back_for_inst':
        name_to_show = callback.from_user.first_name
        main(callback.message, user_name=name_to_show)

    #support 
    elif callback.data == 'back_to_main':
        name_to_show = callback.from_user.first_name
        login_to_show = callback.from_user.username
    
        main(callback.message, user_name=name_to_show, user_login=login_to_show)
    
    elif callback.data == 'back_to_profile':
        u_name = f"{callback.from_user.first_name or ''} {callback.from_user.last_name or ''}".strip()
        u_id = callback.from_user.id
        
        show_profile(callback.message, user_name=u_name, user_id=callback.from_user.id)
        bot.answer_callback_query(callback.id)

    elif callback.data == 'helping':
        support_mes(callback.message, back_target='back_to_main')

    elif callback.data == 'support_from_profile':
        support_mes(callback.message, back_target='back_to_profile')

    elif callback.data == 'back_main':
        name_to_show = callback.from_user.first_name
        login_to_show = callback.from_user.username 
        
        main(callback.message, user_name=name_to_show, user_login=login_to_show)

    # --- control key menu ---
    # button create key
    elif callback.data == 'buy_vpn':
        u_id = callback.from_user.id
        balance = db.get_user_balance(u_id)
        
        if balance < 2: 
            bot.answer_callback_query(callback.id, "❌ Недостаточно средств (нужно минимум 2₽)", show_alert=True)
            return
        
        try:
            menu_protokol(callback.message, u_id)

        except Exception as e:
            print(f"❌ КРИТИЧЕСКАЯ ОШИБКА API: {e}") # ЭТО ВАЖНО: смотрим в консоль!
            bot.send_message(callback.message.chat.id, f"❌ Ошибка API: {e}")
    
    #outline klient key create 
    elif callback.data == 'Outline_connect':
        try:
            db.update_balance(u_id, -2)
            db.delete_vpn_key_final(u_id) 
            
            # create
            new_key = client.create_key()
            
            # search atributs key
            k_id = getattr(new_key, 'key_id', getattr(new_key, 'id', None))
            k_url = getattr(new_key, 'access_url', getattr(new_key, 'access_key', None))

            client.rename_key(k_id, f"User_{u_id}")
            mask_url = f"{k_url}&prefix=POST%20"          
            
            db.add_vpn_key(u_id, k_id, f"Key_{u_id}", mask_url)
            
            bot.answer_callback_query(callback.id, "✅ Доступ оплачен и активирован!")
            show_devices_menu(callback.message, u_id)
            
        except Exception as e:
            db.update_balance(u_id, 2) 
            print(f"❌ КРИТИЧЕСКАЯ ОШИБКА API: {e}")
            bot.send_message(callback.message.chat.id, f"❌ Ошибка API: {e}")
    
    # create vless
    elif callback.data == "Vless_connect":
        u_id = callback.from_user.id
        bot.answer_callback_query(callback.id)
        vpn_data = db.get_user_vpn_data(u_id)

        try:
            v_uuid_to_del = vpn_data[5] if vpn_data and vpn_data[4] == 'vless' else None

            if not v_uuid_to_del:
                try:
                    base = xui.base_url.rstrip('/')
                    # push data inbound
                    res = xui.session.get(f"{base}/panel/api/inbounds/get/1")
                    if res.status_code == 200:
                        clients = res.json()['obj']['settings'] 
                        # search user in json list
                        import json
                        settings_dict = json.loads(clients)
                        for c in settings_dict['clients']:
                            if c['email'] == f"user_{u_id}":
                                v_uuid_to_del = c['id']
                                break
                except:
                    pass

            # 3. if search uuid in base - del
            if v_uuid_to_del:
                xui.delete_client(v_uuid_to_del)
                db.delete_vpn_key_final(u_id)
                import time
                time.sleep(0.5) # stop time for panel

            # --- old logic ---
            db.update_balance(u_id, -2)
            v_url, v_uuid = xui.add_client(u_id, inbound_id=1)
            
            if v_url and v_uuid:
                db.add_vpn_key_vless(u_id, v_uuid, f"user_{u_id}", v_url)
                show_devices_menu(callback.message, u_id)
            else:
                raise Exception(f"Детали: {v_uuid}")

        except Exception as e: 
            db.update_balance(u_id, 2)
            bot.send_message(callback.message.chat.id, f"⚠️ Ошибка создания:\n`{e}`")
        
    # my keys menu
    if callback.data == 'my_keys':
            show_devices_menu(callback.message, u_id)
            bot.answer_callback_query(callback.id)


    elif callback.data.startswith('del_'):
        u_id = callback.from_user.id
        vpn_data = db.get_user_vpn_data(u_id)
        
        if vpn_data:
            protocol = vpn_data[4]
            
            try:
                # 1. del in server
                if protocol == 'outline':
                    client.delete_key(vpn_data[0])
                elif protocol == 'vless':
                    v_uuid = vpn_data[5]
                    if v_uuid:
                        xui.delete_client(v_uuid)
            except Exception as e:
                print(f"⚠️ Ошибка при физическом удалении ключа: {e}")
                pass 
            
            # 2. delete write in db
            db.delete_vpn_key_final(u_id)
            
            bot.answer_callback_query(callback.id, "🗑 Ключ полностью удален")

            # back user in key menu
            show_devices_menu(callback.message, u_id)

    # ref menu 
    elif callback.data == "ref_program":
        try:
            bot_info = bot.get_me()
            ref_link = f"https://t.me/{bot_info.username}?start={u_id}"
            ref_count = db.get_referrals_count(u_id)

            text = f'''
<b>👥 Реферальная программа</b>

Приглашайте друзей и получайте <b>15 дней подписки</b> на баланс за каждого нового пользователя!🎉
<i>Друг также получит приветственный бонус при регистрации.</i>

<b>Ваша ссылка для приглашения:</b>
<code>{ref_link}</code>
<i>(Нажмите на ссылку, чтобы скопировать)</i>

<b>Статистика:</b>
— Приглашено: <b>{ref_count}</b> чел.
'''
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("⬅️ Назад в профиль", callback_data="home"))
            
            # Удаляем старое сообщение (с фото профиля) и присылаем чистое меню рефералов
            bot.delete_message(callback.message.chat.id, callback.message.message_id)
            bot.send_message(callback.message.chat.id, text, reply_markup=markup, parse_mode='HTML')
            
        except Exception as e:
            print(f"❌ Ошибка в рефералке: {e}")
            bot.send_message(callback.message.chat.id, "⚠️ Не удалось открыть реферальное меню.")

    # partner menu
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

# about service
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

    # pay meny
    elif callback.data == "top_up":
            markup = types.InlineKeyboardMarkup()
            # Кнопки тарифов
            markup.add(types.InlineKeyboardButton("🔥 1 Месяц — 60 ₽", callback_data="pay_60"))
            markup.add(types.InlineKeyboardButton("⭐ 2 Месяца — 120 ₽", callback_data="pay_120"))
            markup.add(types.InlineKeyboardButton("🌟 3 Месяца — 180 ₽", callback_data="pay_180"))
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
                f"💵 <b>Пополнение баланса: {amount} ₽</b>\n\n"
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

    # adm panel
    elif callback.data == "confirm_send":
        if callback.from_user.id != ADMIN_ID:
            return
        
        bot.edit_message_reply_markup(callback.message.chat.id, callback.message.message_id, reply_markup=None)
        bot.send_message(callback.message.chat.id, "🚀 Рассылка запущена...")
        
        all_users = db.get_all_user_ids()
        if 'broadcast_message' in globals():
            threading.Thread(
            target=send_broadcast, 
            args=(broadcast_message, all_users), 
            daemon=True
                ).start()
        else:
            bot.send_message(callback.message.chat.id, "❌ Ошибка: сообщение потеряно. Попробуй заново.")
        
    elif callback.data == "cancel_send":
        bot.edit_message_reply_markup(callback.message.chat.id, callback.message.message_id, reply_markup=None)
        bot.send_message(callback.message.chat.id, "🚫 Рассылка отменена.")

    elif callback.data == "adm_mes":
        msg = bot.send_message(callback.message.chat.id, "📢 Отправь пост для рассылки:")
        bot.register_next_step_handler(msg, confirm_broadcast)

    elif callback.data == "gift":
        msg = bot.send_message(callback.message.chat.id, "👤 Введи **ID** пользователя, которому хочешь начислить баланс:", parse_mode='Markdown')
        bot.register_next_step_handler(msg, process_gift_id)


# instrucrion
MANUAL_PHOTO_ID = None

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
    try:
        if MANUAL_PHOTO_ID:
            bot.send_photo(message.chat.id, MANUAL_PHOTO_ID, caption=text, 
                           parse_mode='html', reply_markup=instuctmarkups)
        else:
            with open('img/inst.png', 'rb') as photo:
                sent_msg = bot.send_photo(message.chat.id, photo, caption=text, 
                                          parse_mode='html', reply_markup=instuctmarkups)
                MANUAL_PHOTO_ID = sent_msg.photo[-1].file_id
                print(f"📸 Фото загружено на сервер Telegram. File_ID сохранен.")
    except Exception as e:
        print(f"❌ Ошибка при отправке фото: {e}")
        bot.send_message(message.chat.id, text, parse_mode='html', reply_markup=instuctmarkups)

#vless inst
def inst_vless(message):
    try:
        bot.delete_message(message.chat.id, message.message_id)
    except:
            pass

    instuctmarkups = types.InlineKeyboardMarkup()
    android = types.InlineKeyboardButton('Android', callback_data='androidv')
    ios = types.InlineKeyboardButton('Ios', callback_data='iosv')
    mac = types.InlineKeyboardButton('MacOS', callback_data='macv')
    win = types.InlineKeyboardButton('Windows', callback_data='winv')
    lin = types.InlineKeyboardButton('Linux', callback_data='linv')
    back = types.InlineKeyboardButton('Вернуться↩️', callback_data='back_for_inst')
    instuctmarkups.row (android, ios)
    instuctmarkups.row (mac, lin)
    instuctmarkups.row (win)
    instuctmarkups.row(back)
             

    text = f"""
<b>Инструкция по подключению Argent Proxy 🚀</b>

1️⃣ <b>Скачайте приложение в зависимости от вашей ос (Для пк и телефонов приложения отличаются!).</b>

2️⃣ <b>Скопируйте ваш ключ.</b>

3️⃣ <b>Активируйте сервис:</b>
— Откройте приложение.

— Нажмите кнопку <b>"Добавить сервер"</b> (или иконку ➕).

— Вставьте скопированный ключ и нажмите <b>"Добавить сервер"</b>.

— Нажмите кнопку <b>"Подключиться"</b>.

✅ <b>Готово! Теперь вы под защитой.</b>
"""
    global MANUAL_PHOTO_ID
    try:
        if MANUAL_PHOTO_ID:
            bot.send_photo(message.chat.id, MANUAL_PHOTO_ID, caption=text, 
                           parse_mode='html', reply_markup=instuctmarkups)
        else:
            with open('img/inst.png', 'rb') as photo:
                sent_msg = bot.send_photo(message.chat.id, photo, caption=text, 
                                          parse_mode='html', reply_markup=instuctmarkups)
                MANUAL_PHOTO_ID = sent_msg.photo[-1].file_id
                print(f"📸 Фото загружено на сервер Telegram. File_ID сохранен.")
    except Exception as e:
        print(f"❌ Ошибка при отправке фото: {e}")
        bot.send_message(message.chat.id, text, parse_mode='html', reply_markup=instuctmarkups)

# support
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

# profile
PROFILE_PHOTO_ID = None

@bot.message_handler(commands=['profile'])
def show_profile(message, user_name=None, user_id=None):
    try:
        bot.delete_message(message.chat.id, message.message_id)
    except:
        pass

    if user_id:
        final_id = user_id
    elif hasattr(message, 'reply_to_message') and message.from_user: 
        final_id = message.from_user.id
    else: 
        final_id = message.chat.id
    
    if user_name:
        display_name = user_name
    else:
        fn = message.from_user.first_name or ""
        ln = message.from_user.last_name or ""
        display_name = f"{fn} {ln}".strip() or "Пользователь"

    balance = db.get_user_balance(final_id)
    vpn_data = db.get_user_vpn_data(final_id)
    
    is_active = False
    if vpn_data:
        is_active = vpn_data[3]

    status_text = "✅ Работает" if is_active else "❌ Отключен"
    
    days_left = balance // 2 if balance > 0 else 0

    if days_left > 0:
        expiry_info = f"~ <b>{days_left} дн.</b>"
    else:
        expiry_info = "<b>Требуется пополнение</b>"

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

    channel_link = "https://t.me/ArgentVPNru"

    text = f'''
<b>👤 Профиль </b>
                     
<b>{display_name}, ваш баланс: {balance} руб.</b>

<b>Статус proxy:</b> {status_text}
<b>Хватит на:</b> {expiry_info} дней.

<i>Одного пополнения на 60₽ хватает на 30 дней доступа для 10 устройств!📱</i>

<b>📍 Наш канал: <a href='{channel_link}'>Подписаться</a></b>
'''
    
    global PROFILE_PHOTO_ID
    try:
        if PROFILE_PHOTO_ID:
            bot.send_photo(message.chat.id, PROFILE_PHOTO_ID, caption=text, 
                           parse_mode='html', reply_markup=profmarkups)
        else:
            with open('img/profile.png', 'rb') as photo:
                sent_msg = bot.send_photo(message.chat.id, photo, caption=text, 
                                          parse_mode='html', reply_markup=profmarkups)
                PROFILE_PHOTO_ID = sent_msg.photo[-1].file_id
                print(f"📸 Фото загружено на сервер Telegram. File_ID сохранен.")
    except Exception as e:
        print(f"❌ Ошибка при отправке фото: {e}")
        bot.send_message(message.chat.id, text, parse_mode='html', reply_markup=profmarkups)

# key menu
KEY_PHOTO_ID = None

def show_devices_menu(message, user_id):
    global KEY_PHOTO_ID
    vpn_data = db.get_user_vpn_data(user_id)
    markup = types.InlineKeyboardMarkup()
    
    instsel = "instruct" 

    if not vpn_data: 
        text = "<b>📱 У вас пока нет созданных ключей.</b>"
        markup.add(types.InlineKeyboardButton("➕ Создать доступ (2₽/сутки)", callback_data="buy_vpn"))
    else:
        server_key_id, access_url, _, is_active, protocol, vless_uuid = vpn_data
        
        # safe user at old server
        if "194.41.113.168" in str(access_url):
            text = "<b>📱 Ваш ключ устарел.</b>\n\nКлючи, созданные до 13 февраля, больше не поддерживаются. Пожалуйста, удалите старый доступ и создайте новый (рекомендуем VLESS)."
            key_id_for_delete = server_key_id if protocol == 'outline' else vless_uuid
            markup.add(types.InlineKeyboardButton("🗑 Удалить старый ключ", callback_data=f"del_{key_id_for_delete}"))
        
        else:
            # for new key
            key_id_for_delete = server_key_id if protocol == 'outline' else vless_uuid

            text = f'''
<b>⛓️‍💥 Ваш {protocol.upper()} доступ готов!</b>

<b>1. Скопируйте этот ключ:</b> 
<code>{access_url}</code>

<b>2. Скачайте приложение {'Outline' if protocol == 'outline' else 'В ИНСТРУКЦИИ!!! <i>(если вы перешли со старого протокола, нужно установить новое)</i>'}.</b>

<b>3. Нажмите «Добавить сервер» и вставьте ключ.</b>

<i>Вы можете использовать этот ключ на 10 устройствах одновременно.</i>'''
            
            markup.add(types.InlineKeyboardButton("🗑 Удалить ключ полностью", callback_data=f"del_{key_id_for_delete}"))
            
            # select instruction
            instsel = "instruct" if protocol == 'outline' else 'instvless'

    markup.row(types.InlineKeyboardButton("📖 Установить приложение", callback_data=instsel))
    markup.row(types.InlineKeyboardButton("⬅️ В профиль", callback_data="back_to_profile"))

    try:
        bot.delete_message(message.chat.id, message.message_id)
    except:
        pass

    try:
        if KEY_PHOTO_ID:
            bot.send_photo(message.chat.id, KEY_PHOTO_ID, caption=text, 
                           parse_mode='html', reply_markup=markup)
        else:
            with open('img/key_menu.png', 'rb') as photo:
                sent_msg = bot.send_photo(message.chat.id, photo, caption=text, 
                                          parse_mode='html', reply_markup=markup)
                KEY_PHOTO_ID = sent_msg.photo[-1].file_id
                print(f"📸 Фото загружено на сервер Telegram. File_ID сохранен.")
    except Exception as e:
        print(f"❌ Ошибка при отправке фото: {e}")
        bot.send_message(message.chat.id, text, parse_mode='html', reply_markup=markup)

# protocol menu
def menu_protokol(message, user_id):
    markup=types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🚀 VLESS (Скорость)", callback_data="Vless_connect"))
    markup.add(types.InlineKeyboardButton("🛡 Outline (Резерв)", callback_data="Outline_connect"))

    text="""
🛜Выберете протокол:
"""
    bot.send_message(message.chat.id, text, parse_mode='html', reply_markup=markup)

# adm panel
ADMIN_ID = os.getenv("tg_adm_id")  

# adm update balance
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
        
        db.update_balance(target_id, amount) 

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

# adm message from user
def send_broadcast(admin_msg, user_ids):
    count = 0
    blocked = 0
    
    for uid in user_ids:
        try:
            bot.copy_message(chat_id=uid, from_chat_id=admin_msg.chat.id, message_id=admin_msg.message_id)
            count += 1
            
            time.sleep(0.05)            
        except Exception as e:
            blocked += 1
            print(f"Ошибка при отправке пользователю {uid}: {e}")
            
    bot.send_message(admin_msg.chat.id, f"✅ Рассылка завершена!\n\n📈 Успешно: {count}\n🚫 Заблокировали бота: {blocked}")

def broadcast_command(message, user_id):
    if message.from_user.id == ADMIN_ID:
        msg = bot.send_message(message.chat.id, "Отправь пост, который хочешь разослать:")
        bot.register_next_step_handler(msg, confirm_broadcast)

def confirm_broadcast(message):
    if message.from_user.id != ADMIN_ID:
        return
    
    global broadcast_message
    broadcast_message = message

    markup = types.InlineKeyboardMarkup()
    btn_yes = types.InlineKeyboardButton("✅ Да, рассылаем", callback_data="confirm_send")
    btn_no = types.InlineKeyboardButton("❌ Отмена", callback_data="cancel_send")
    markup.add(btn_yes, btn_no)

    bot.send_message(message.chat.id, "Пост принят. Начинаем рассылку?", reply_markup=markup)

# adm stat
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

# photo prank
@bot.message_handler(content_types=['photo'])
def get_photo(message):
    bot.send_message(message.chat.id, 'Крутое фото👍')


# for take id file
# айди дока (временное, потом комент)
# @bot.message_handler(content_types=['document'])
# def handle_docs(message):
#     # Этот код сработает, когда ТЫ (админ) пришлешь файл
#     file_id = message.document.file_id
#     file_name = message.document.file_name
    
#     bot.reply_to(message, 
#         f"✅ <b>Файл получен!</b>\n\n"
#         f"📎 Имя: <code>{file_name}</code>\n"
#         f"🆔 ID: <code>{file_id}</code>\n\n"
#         f"Используй этот ID в коде, чтобы отправить файл юзеру.", 
#         parse_mode='html'
#     )

# test billing for one user
@bot.message_handler(commands=['testme'])
def test_billing_me(message):
    user_id = message.from_user.id
    
    user_key = db.get_user_vpn_data(user_id)
    
    if not user_key:
        bot.reply_to(message, "❌ У тебя нет VPN ключа для теста")
        return
    
    server_key_id, _, _, _, protocol, vless_uuid = user_key
    balance = db.get_user_balance(user_id)
    
    if balance >= 2:
        db.update_balance(user_id, -2)
        new_balance = db.get_user_balance(user_id)
        bot.reply_to(message, 
            f"🧪 <b>Тест списания успешен!</b>\n"
            f"Протокол: <code>{protocol}</code>\n"
            f"Списано: 2 рубля\n"
            f"Баланс: {balance} → {new_balance} руб", parse_mode='html')
    else:
        # fake del
        bot.reply_to(message, f"🧪 <b>Тест удаления (баланс {balance}₽):</b>", parse_mode='html')
        
        try:
            if protocol == 'outline':
                client.delete_key(server_key_id)
                bot.send_message(user_id, "✅ Ключ удален из Outline")
            elif protocol == 'vless':
                if vless_uuid:
                    xui.delete_client(vless_uuid)
                    bot.send_message(user_id, "✅ Ключ удален из 3X-UI")
            
            db.delete_vpn_key_final(user_id)
            bot.send_message(user_id, "✅ Запись стерта из БД бота. Тест завершен.")
            
        except Exception as e:
            bot.send_message(user_id, f"⚠️ Ошибка при тестовом удалении: {e}")

# promocode logic
PROMOS = {
    "ARGENT12": {"days": 12, "limit": 6, "users": []},
    "TestPromo": {"days": 1, "limit": 1, "users": []}
}

@bot.message_handler(commands=['promo'])
def handle_promo(message):
    parts = message.text.split()
    if len(parts) < 2:
        return bot.reply_to(message, "Введи код, например: /promo ВЕСНА")
    
    code = parts[1].upper()
    user_id = message.from_user.id

    if code in PROMOS:
        p = PROMOS[code]
        if len(p["users"]) >= p["limit"]:
            bot.send_message(message.chat.id, "Лимит исчерпан! 💨")
        elif user_id in p["users"]:
            bot.send_message(message.chat.id, "Ты уже в деле, второй раз нельзя! ✋")
        else:
            p["users"].append(user_id)
            db.update_balance(user_id, p["days"] * 2)
            bot.send_message(message.chat.id, f"🔥 Успех! +{p['days']} дней к твоему Argent.")
    else:
        bot.send_message(message.chat.id, "Недействительный код.")    

# billing
def daily_billing_job():
    """Ежедневное списание - универсальное для Outline и VLESS"""
    print(f"💰 [{datetime.now().strftime('%H:%M')}] Начинаю ежедневное списание...")
    
    try:
        all_keys = db.get_all_active_keys() 
        print(f"   📊 Всего активных ключей: {len(all_keys)}")
        
        for user_id, server_key_id, protocol, vless_uuid in all_keys:
            try:
                balance = db.get_user_balance(user_id)
                
                if balance >= 2:
                    db.update_balance(user_id, -2)
                    print(f"✅ {user_id}: -2 руб. (Протокол: {protocol})")
                else:
                    print(f"🚫 У {user_id} баланс {balance} руб. Удаляю {protocol}...")
                    
                    # --- del in panel ---
                    if protocol == 'outline':
                        try:
                            client.delete_key(server_key_id)
                            print(f"   🔒 Удален из Outline")
                        except Exception as e:
                            print(f"   ⚠️ Ошибка Outline: {e}")
                            
                    elif protocol == 'vless':
                        try:
                            if vless_uuid:
                                xui.delete_client(vless_uuid)
                                print(f"   🔒 Удален из 3X-UI (VLESS)")
                        except Exception as e:
                            print(f"   ⚠️ Ошибка VLESS: {e}")

                    # --- del in db ---
                    db.delete_vpn_key_final(user_id)
                    
                    # message
                    try:
                        bot.send_message(user_id, 
                            "⚠️ *Доступ приостановлен*\n\n"
                            "Баланс менее 2₽, ваш ключ удален.\n"
                            "Пополните счет и создайте новый ключ в профиле.",
                            parse_mode='Markdown')
                    except:
                        pass
                        
            except Exception as e:
                print(f"⚠️ Ошибка биллинга юзера {user_id}: {e}")
                
        print(f"✅ Биллинг завершен!")
    except Exception as e:
        print(f"❌ Критическая ошибка биллинга: {e}")

# --- cheduler conf ---
def clear_memory():
    print("🧹 Принудительная очистка памяти...")
    gc.collect()

moscow_tz = timezone('Europe/Moscow')
scheduler = BackgroundScheduler(timezone=moscow_tz)

# dayli magazine at 00
scheduler.add_job(daily_billing_job, 'cron', hour=0, minute=0)
# clear py cashe
scheduler.add_job(clear_memory, 'interval', minutes=30)

# --- block init ---
if __name__ == "__main__":
    try:
        # 1. start scheduler
        scheduler.start()
        print("✅ Планировщик запущен (списания + очистка памяти)!")

        # 2. init database
        db.init_db()

        # 3. init flask for webhooks
        flask_thread = threading.Thread(
            target=lambda: app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)
        )
        flask_thread.daemon = True 
        flask_thread.start()
        print("✅ Flask-сервер для ЮKassa запущен на порту 5000!")

        # 4. cycle bot
        print("🚀 Бот вышел на связь...")
        bot.polling(none_stop=True)

    except Exception as e:
        print(f"❌ Критическая ошибка при запуске: {e}")