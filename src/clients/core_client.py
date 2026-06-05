import httpx
from src.auth.security import create_access_token
from src.schemas.jwt_schema import TokenData
from src.schemas.bot_schema import UserRegister, CheckUserBalance, AdmUpdateBalance
from src.schemas.vpn_client_schema import AccessUrlUser, ReturnKeyForBot, CreateKeyApiBody

class ArgentCoreClient:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")

        self.client = httpx.AsyncClient(
            base_url=base_url,
            timeout=httpx.Timeout(15.0, connect=5.0)
            )

    async def close(self):
        await self.client.aclose()    


    async def check_user(self, user_id: int) -> bool:
        try:
            token_data = TokenData(user_id=user_id)
            token = create_access_token(data = token_data)

            url = "/users/check"
            header = {"Authorization": f"Bearer {token}" }

            response = await self.client.get(url=url, headers=header)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Ошибка проверки юзера: {e}")
            return None
            
    async def register_user(self, user_data: UserRegister):
        try:
            response = await self.client.post(f"/users/register", json=user_data.model_dump())
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Ошибка при регистрации пользователя: {e}")
            return None
        
    async def update_balance(self, data: AdmUpdateBalance, user_id: int):
        try:
            token_data = TokenData(user_id=user_id)
            token = create_access_token(data = token_data)            
            url = "/users/update_balance"
            header = {'Authorization': f"Bearer {token}"}

            response = await self.client.post(url, json=data.model_dump(), headers=header)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Ошибка пополнения: {e}")
            return None
        
    async def get_balance(self, user_id: int):       
        try:
            token_data = TokenData(user_id=user_id)
            token = create_access_token(data = token_data)            
            url = "/users/get_balance"
            header = {'Authorization': f"Bearer {token}"}

            response = await self.client.get(url=url, headers=header)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Ошибка получения баланса: {e}")
            return None
        

    #for keys
    async def get_user_access_url(self, user_id: int) -> AccessUrlUser:
        try:
            token_data = TokenData(user_id=user_id)
            token = create_access_token(data = token_data)            
            url = "/vpn-core/access_url"
            header = {'Authorization': f"Bearer {token}"}

            response = await self.client.get(url=url, headers=header)
            response.raise_for_status()
            return AccessUrlUser(**response.json())
        except Exception as e:
            print(f"Error get access key: {e}")
            return None
        
    async def create_key(self, protocol: str, user_id: int) -> ReturnKeyForBot:
        try:
            token_data = TokenData(user_id=user_id)
            token = create_access_token(data = token_data)            
            url = "/vpn-core/create_key"
            header = {'Authorization': f"Bearer {token}"}
            body = CreateKeyApiBody(protocol=protocol)

            response = await self.client.post(url=url,json=body.model_dump(), headers=header)
            response.raise_for_status()
            return ReturnKeyForBot(**response.json())
        except Exception as e:
            print(f"Error create key: {e}")
            return None
        
    async def create_key(self, user_id: int):
        try:
            token_data = TokenData(user_id=user_id)
            token = create_access_token(data = token_data)            
            url = "/vpn-core/del_key"
            header = {'Authorization': f"Bearer {token}"}

            response = await self.client.delete(url=url, headers=header)
            response.raise_for_status()
            return response.json()      
        except Exception as e:
            print(f"Error del key: {e}")
            return None 