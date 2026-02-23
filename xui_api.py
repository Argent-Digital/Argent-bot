import requests
import json
import uuid

class XUIPanel:
    def __init__(self, base_url, username, password):
        # Убираем лишние слэши в конце URL, если они есть
        self.base_url = base_url.rstrip('/')
        self.username = username
        self.password = password
        self.session = requests.Session()

    def login(self):
        try:
            # Чистим базовый URL от лишних слэшей
            base = self.base_url.strip('/')
            url = f"{base}/login" 
            
            print(f"--- DEBUG LOGIN ---")
            print(f"Full URL: {url}")
            
            data = {"username": self.username, "password": self.password}
            headers = {
                "User-Agent": "Mozilla/5.0",
                "Content-Type": "application/x-www-form-urlencoded",
                "Referer": f"{base}/" # Панель часто проверяет Referer
            }
            
            response = self.session.post(url, data=data, timeout=10, headers=headers)
            
            print(f"Status Code: {response.status_code}")
            # Если получили 404 — значит путь все еще неверный
            # Если 200 — смотрим результат JSON
            if response.status_code == 200:
                res_json = response.json()
                print(f"Response: {res_json}")
                return res_json.get("success", False)
            return False
        except Exception as e:
            print(f"❌ Ошибка авторизации: {e}")
            return False

    def add_client(self, user_id, inbound_id=1):
        # 1. Сначала логинимся (сессия сохранит куки автоматически)
        if not self.login():
            return None, "AUTH_FAILED_OR_404"

        client_uuid = str(uuid.uuid4())
        email = f"user_{user_id}"
        
        # Данные клиента (добавил чуть больше полей для совместимости)
        client_data = {
            "id": client_uuid,
            "alterId": 0,
            "email": email,
            "limitIp": 10,
            "totalGB": 0,
            "expiryTime": 0,
            "enable": True,
            "tgId": str(user_id),
            "subId": ""
        }

        base = self.base_url.rstrip('/')
        url = f"{base}/panel/api/inbounds/addClient"
        
        # Некоторые версии панели требуют JSON в теле запроса, а не в параметрах
        payload = {
            "id": int(inbound_id), 
            "settings": json.dumps({"clients": [client_data]})
        }

        try:
            # Делаем запрос с таймаутом и заголовками сессии
            res = self.session.post(url, data=payload, timeout=10)
            
            if not res.text:
                # Если всё еще пусто, пробуем вытащить статус код
                return None, f"EMPTY_RESPONSE (Status: {res.status_code})"
            
            data = res.json()
            if data.get("success"):
                # Собираем эталонную ссылку, копируя параметры твоего рабочего инбаунда
                # Важно: path должен быть именно таким, как в панели!
                ip = "89.169.53.247"
                port = 10000
                path = "%2Fargent-vless%2F" 
                
                vless_link = (
                    f"vless://{client_uuid}@{ip}:{port}?"
                    f"type=ws&encryption=none&path={path}&host=&security=none"
                    f"#Argent-speed_{user_id}"
                )
                
                return vless_link, client_uuid
            else:
                return None, f"PANEL_REJECT: {data.get('msg')}"
                
        except Exception as e:
            return None, f"ADD_CLIENT_ERROR: {str(e)}"
        
    def delete_client(self, client_uuid, inbound_id=1):
        if not self.login():
            return False
        
        base = self.base_url.rstrip('/')
        # НОВЫЙ ПУТЬ: часто в новых версиях используется этот формат
        url = f"{base}/panel/api/inbounds/1/delClient/{client_uuid}" 
        
        # Если не сработает тот, что выше, попробуй этот (раскомментируй если что):
        # url = f"{base}/panel/api/inbounds/client/del/{client_uuid}"

        try:
            res = self.session.post(url, timeout=10)
            print(f"--- DEBUG DELETE ---")
            print(f"URL: {url}")
            print(f"Status: {res.status_code}")
            print(f"Response: {res.text}")
            
            # Если статус 200, значит удаление прошло успешно
            return res.status_code == 200
        except Exception as e:
            print(f"❌ Ошибка в delete_client: {e}")
            return False