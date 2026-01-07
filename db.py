import psycopg2
from psycopg2 import sql

# подключение
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
    cur.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id BIGINT PRIMARY KEY,
            username TEXT,
            balance INT DEFAULT 0,
            registration_date TIMESTAMP DEFAULT CURREN_TIMESTAMP              
        );
    ''')
    conn.commit()
    cur.close()
    conn.close()
    print("База готова к работе")

def add_user(user_id, username):
    conn = get_connection()
    cur = conn.cursor()
    
    cur.execute('''
        INSERT INTO users (user_id, username)
        VALUES (%s, %s)
        ON CONFLICT (user_id) DO NOTHING
    ''', (user_id, username))
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