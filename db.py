import psycopg2
from psycopg2 import sql
from datetime import datetime, timedelta

# Подключение
DB_CONFIG = {
    "database": "ArgentVPN",
    "user": "postgres", 
    "password": "q20081004", 
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
            registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP              
        );
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
    conn.commit()
    cur.close()
    conn.close()
    print("✅ База готова к работе")

def add_user(user_id, username, first_name, referrer_id=None):
    conn = get_connection()
    cur = conn.cursor()
    # Используем UPSERT (обновляем имя, если юзер уже был)
    cur.execute('''
        INSERT INTO users (user_id, username, first_name, balance, referrer_id)
        VALUES (%s, %s, %s, 30, %s)
        ON CONFLICT (user_id) DO UPDATE 
        SET username = EXCLUDED.username, 
            first_name = EXCLUDED.first_name;
    ''', (user_id, username, first_name, referrer_id))
    conn.commit()
    cur.close()
    conn.close()

def get_user_balance(user_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute('SELECT balance FROM users WHERE user_id = %s', (user_id,))
    result = cur.fetchone()
    cur.close()
    conn.close()
    return result[0] if result else 0

def update_balance(user_id, amount):
    """Универсальная функция для + и - баланса"""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute('UPDATE users SET balance = balance + %s WHERE user_id = %s', (amount, user_id))
    conn.commit()
    cur.close()
    conn.close()

def add_vpn_key(user_id, server_key_id, key_name, access_url):
    conn = get_connection()
    cur = conn.cursor()
    # Теперь просто записываем текущее время как дату начала
    now = datetime.now()
    cur.execute('''
        INSERT INTO vpn_keys (user_id, server_key_id, key_name, access_url, expiry_date, is_active)
        VALUES (%s, %s, %s, %s, %s, TRUE)
        ON CONFLICT (user_id) DO UPDATE SET
            server_key_id = EXCLUDED.server_key_id,
            access_url = EXCLUDED.access_url,
            is_active = TRUE;
    ''', (user_id, server_key_id, key_name, access_url, now))
    conn.commit()
    cur.close()
    conn.close()

def get_user_vpn_data(user_id):
    """Получает все данные о ключе пользователя для меню"""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute('''
        SELECT server_key_id, access_url, expiry_date, is_active 
        FROM vpn_keys 
        WHERE user_id = %s
    ''', (user_id,))
    result = cur.fetchone()
    cur.close()
    conn.close()
    return result

def get_all_vpn_keys():
    """Для планировщика списаний"""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute('SELECT user_id, server_key_id, expiry_date, is_active FROM vpn_keys')
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
    # Берем только тех, у кого ключ активен
    cur.execute('SELECT user_id, server_key_id FROM vpn_keys WHERE is_active = TRUE')
    data = cur.fetchall()
    cur.close()
    conn.close()
    return data

def update_vpn_status(user_id, status):
    """Переключение активности (для паузы списаний)"""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute('UPDATE vpn_keys SET is_active = %s WHERE user_id = %s', (status, user_id))
    conn.commit()
    cur.close()
    conn.close()

def delete_vpn_key(server_key_id):
    conn = get_connection()
    cur = conn.cursor()
    # Важно: удаляем по server_key_id, так как мы его передаем из кнопки
    cur.execute('DELETE FROM vpn_keys WHERE server_key_id = %s', (server_key_id,))
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