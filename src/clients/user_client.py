import httpx

class ArgentCoreClient:
    def __init__(self, base_url: str = "http://127.0.0.1:8000"):
        self.base_url = base_url

        self.client = httpx.AsyncClient(base_url=base_url)    

    async def check_user(self, user_id: int) -> bool:
        try:
            response = await self.client.get(f"/users/check/{user_id}")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Ошибка проверки юзера: {e}")
            return False
            
    async def register_user(self, user_id: int,first_name: str, username: str = None, referrer_id: int = None):
        user_data = {
            "user_id": user_id,
            "username": username,
            "first_name": first_name,
            "referrer_id": referrer_id
            }
        try:
            response = await self.client.post(f"/users/register", json=user_data)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Ошибка при регистрации пользователя: {e}")
            return None
        
    async def update_balance(self, user_id: int, amount: int):
        data = {
            "user_id": user_id,
            "amount": amount
        }
        try:
            response = await self.client.post(f"/users/update_balance", json=data)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Ошибка пополнения: {e}")
            return None
        
    async def get_balance(self, user_id: int):       
        try:
            response = await self.client.get(f"/users/get_balance/{user_id}")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Ошибка получения баланса: {e}")
            return None