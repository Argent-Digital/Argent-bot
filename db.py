import os
import psycopg2
from psycopg2 import sql
from datetime import datetime, timedelta
import subprocess
import json
import uuid

from dotenv import load_dotenv

load_dotenv()

# Подключение
DB_CONFIG = {
    "database": os.getenv("db_name"),
    "user": os.getenv("db_user"), 
    "password": os.getenv("db_pass"), 
    "host": "localhost",
    "port": "5432"
}

def get_connection():
    return psycopg2.connect(**DB_CONFIG)

def init_db():
    conn = get_connection()
    cur = conn.cursor()
    # Таблица пользователей
    cur.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id BIGINT PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            balance INT DEFAULT 0,
            referrer_id BIGINT,
            registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_verified BOOLEAN DEFAULT FALSE              
        );
    ''')
    # добавление статуса капчи для существующих пользователей
    cur.execute('''
        ALTER TABLE users ADD COLUMN IF NOT EXISTS is_verified BOOLEAN DEFAULT FALSE;
    ''') 

    # Таблица ключей (Один юзер - один ключ)
    cur.execute('''
        CREATE TABLE IF NOT EXISTS vpn_keys (
            key_id SERIAL PRIMARY KEY,
            user_id BIGINT UNIQUE REFERENCES users(user_id) ON DELETE CASCADE,
            server_key_id TEXT,
            key_name TEXT,
            access_url TEXT,
            is_active BOOLEAN DEFAULT TRUE,
            expiry_date TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    ''')

    cur.execute('''
        ALTER TABLE vpn_keys ADD COLUMN IF NOT EXISTS protocol TEXT DEFAULT 'outline';
        ALTER TABLE vpn_keys ADD COLUMN IF NOT EXISTS vless_uuid UUID;
    ''')

    conn.commit()
    cur.close()
    conn.close()
    print("✅ База готова к работе")

def add_user(user_id, username, first_name, referrer_id=None):
    conn = get_connection()
    cur = conn.cursor()
    
    # Защита от None: если данных нет, записываем None или дефолтное имя
    safe_username = username[:50] if username else None
    safe_first_name = first_name[:50] if first_name else "Пользователь"
    
    try:
        cur.execute('''
            INSERT INTO users (user_id, username, first_name, referrer_id, balance)
            VALUES (%s, %s, %s, %s, 30)
            ON CONFLICT (user_id) DO NOTHING;
        ''', (user_id, safe_username, safe_first_name, referrer_id))
        conn.commit()
    except Exception as e:
        print(f"❌ Ошибка в базе данных при добавлении юзера: {e}")
    finally:
        cur.close()
        conn.close()

def get_user_balance(user_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute('SELECT balance FROM users WHERE user_id = %s', (user_id,))
    result = cur.fetchone()
    cur.close()
    conn.close()
    # Возвращаем баланс или None, если юзера нет
    return result[0] if result is not None else None

def update_balance(user_id, amount):
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute('UPDATE users SET balance = balance + %s WHERE user_id = %s', (amount, user_id))
        conn.commit()
    except Exception as e:
        print(f"❌ Ошибка UPDATE balance: {e}")
    finally:
        cur.close()
        conn.close()
        
def add_vpn_key(user_id, server_key_id, key_name, access_url):
    conn = get_connection()
    cur = conn.cursor()
    now = datetime.now()
    cur.execute('''
        INSERT INTO vpn_keys (user_id, server_key_id, key_name, access_url, expiry_date, created_at, is_active)
        VALUES (%s, %s, %s, %s, %s, %s, TRUE)
        ON CONFLICT (user_id) DO UPDATE SET
            server_key_id = EXCLUDED.server_key_id,
            access_url = EXCLUDED.access_url,
            expiry_date = EXCLUDED.expiry_date, -- Обновляем дату при пересоздании
            is_active = TRUE;
    ''', (user_id, server_key_id, key_name, access_url, now, now))
    conn.commit()
    cur.close()
    conn.close()

def add_vpn_key_vless(user_id, vless_uuid, key_name, access_url):
    print(f"DEBUG DB: Начинаю запись для {user_id}")
    conn = get_connection()
    cur = conn.cursor()
    
    try:
        # ПЕРЕДАЕМ UUID КАК СТРОКУ — это решит проблему с адаптацией типа
        str_uuid = str(vless_uuid) 
        
        cur.execute('''
            INSERT INTO vpn_keys (user_id, vless_uuid, key_name, access_url, protocol, is_active) 
            VALUES (%s, %s, %s, %s, 'vless', True) 
            ON CONFLICT (user_id) DO UPDATE SET 
            vless_uuid = EXCLUDED.vless_uuid, 
            access_url = EXCLUDED.access_url, 
            protocol = 'vless',
            is_active = True
        ''', (user_id, str_uuid, key_name, access_url))
        
        conn.commit()
        print(f"✅ Ключ VLESS для {user_id} успешно сохранен в БД")
    except Exception as e:
        print(f"❌ Ошибка в базе данных VLESS: {e}")
        # Не забываем пробрасывать, чтобы в main.py сработал откат баланса
        raise e 
    finally:
        cur.close()
        conn.close()

def get_user_access_url(user_id):
    """Возвращает только ссылку (ключ) пользователя"""
    conn = get_connection()
    cur = conn.cursor()
    # Берем только вторую колонку (access_url)
    cur.execute('SELECT access_url FROM vpn_keys WHERE user_id = %s AND is_active = TRUE', (user_id,))
    result = cur.fetchone()
    cur.close()
    conn.close()
    return result[0] if result else None

def get_user_vpn_data(user_id):
    """Получает все данные о ключе (универсально для Outline и VLESS)"""
    conn = get_connection()
    cur = conn.cursor()
    # Добавляем протокол в выборку, чтобы понимать, что это за ключ
    cur.execute('''
        SELECT server_key_id, access_url, expiry_date, is_active, protocol, vless_uuid
        FROM vpn_keys 
        WHERE user_id = %s
    ''', (user_id,))
    result = cur.fetchone()
    cur.close()
    conn.close()
    return result

def get_all_vpn_keys():
    """Возвращает данные в строгом порядке для планировщика"""
    conn = get_connection()
    cur = conn.cursor()
    # Используем COALESCE для даты, чтобы не поймать None
    cur.execute('''
        SELECT user_id, server_key_id, COALESCE(expiry_date, created_at, NOW()), is_active 
        FROM vpn_keys
    ''')
    data = cur.fetchall()
    cur.close()
    conn.close()
    return data

def update_vpn_expiry(user_id, new_date, status):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute('UPDATE vpn_keys SET expiry_date = %s, is_active = %s WHERE user_id = %s', 
                (new_date, status, user_id))
    conn.commit()
    cur.close()
    conn.close()

def get_all_active_keys():
    conn = get_connection()
    cur = conn.cursor()
    # Тянем всё нужное для биллинга
    cur.execute('SELECT user_id, server_key_id, protocol, vless_uuid FROM vpn_keys WHERE is_active = TRUE')
    result = cur.fetchall()
    cur.close()
    conn.close()
    return result

def delete_vpn_key(server_key_id):
    """Мягкое удаление: помечает ключ как неактивный для финального списания"""
    conn = get_connection()
    cur = conn.cursor()
    # Мы не удаляем, а выключаем. Планировщик увидит это ночью.
    cur.execute('UPDATE vpn_keys SET is_active = FALSE WHERE server_key_id = %s', (server_key_id,))
    conn.commit()
    cur.close()
    conn.close()

def delete_vpn_key_final(user_id):
    """Удаляет ключ по ID пользователя. Название старое — логика надежная!"""
    conn = get_connection()
    cur = conn.cursor()
    # Удаляем именно по user_id, так как это поле UNIQUE и оно главное в логике бота
    cur.execute('DELETE FROM vpn_keys WHERE user_id = %s', (user_id,))
    conn.commit()
    cur.close()
    conn.close()

def get_referrals_count(user_id):
    """Считает, сколько человек пригласил пользователь"""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute('SELECT COUNT(*) FROM users WHERE referrer_id = %s', (user_id,))
    count = cur.fetchone()[0]
    cur.close()
    conn.close()
    return count

def get_referrer(user_id):
    """Узнает, КТО пригласил этого юзера (возвращает ID пригласителя)"""
    conn = get_connection()
    cur = conn.cursor()
    # Мы ищем referrer_id для конкретного новичка
    cur.execute('SELECT referrer_id FROM users WHERE user_id = %s', (user_id,))
    result = cur.fetchone()
    cur.close()
    conn.close()
    return result[0] if result and result[0] else None

def get_all_user_ids():
    conn = get_connection()
    cur = conn.cursor()
    try:
        # Выбираем только user_id из таблицы users
        cur.execute("SELECT user_id FROM users;")
        rows = cur.fetchall()
        return [row[0] for row in rows]
    except Exception as e:
        print(f"❌ Ошибка при получении списка юзеров: {e}")
        return []
    finally:
        cur.close()
        conn.close()

def get_mega_stats():
    # 1. Считаем всё из базы (Юзеры, Активные ключи, Баланс)
    conn = get_connection()
    cur = conn.cursor()
    cur.execute('''
        SELECT 
            (SELECT count(*) FROM users) as total_users,
            (SELECT count(*) FROM vpn_keys WHERE is_active = TRUE) as active_keys
    ''')
    db_total, db_keys = cur.fetchone()
    cur.close()
    conn.close()

    # 2. Трафик из vnstat (за сегодня)
    try:
        traffic_raw = subprocess.check_output(['vnstat', '--json']).decode('utf-8')
        traffic_data = json.loads(traffic_raw)
        
        # Берем данные за сегодня
        stats_today = traffic_data['interfaces'][0]['traffic']['day'][-1]
        
        # vnstat в JSON обычно отдает в Байтах (Bytes). 
        # Делим на 1024^3, чтобы получить честные Гигабайты (GiB)
        rx_raw = stats_today['rx']
        tx_raw = stats_today['tx']
        
        # Проверка: если число слишком огромное, значит делим на 1024^3 (из байт)
        # Если маленькое — значит vnstat уже в чем-то другом отдал.
        rx = round(rx_raw / (1024**3), 2)
        tx = round(tx_raw / (1024**3), 2)
        total_gb = round(rx + tx, 2)
        
        # Если после деления на 1024^3 получили 0.0, 
        # значит там были не байты, а КБ (делим на 1024^2)
        if total_gb < 0.01:
            rx = round(rx_raw / (1024**2), 2)
            tx = round(tx_raw / (1024**2), 2)
            total_gb = round(rx + tx, 2)

    except Exception as e:
        rx = tx = total_gb = "ошибка"
        
    return {
        "users": db_total,
        "keys": db_keys,
        "traffic": total_gb,
        "rx": rx,
        "tx": tx
    }