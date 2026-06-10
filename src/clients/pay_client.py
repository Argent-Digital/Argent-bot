import httpx
from src.auth.security import create_access_token
from src.schemas.jwt_schema import TokenData
from src.schemas.pay_schemas import CreatePaymentUrl, ReturnUrl

class ArgentPayClient:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self.client = httpx.AsyncClient(
            base_url=base_url,
            timeout=httpx.Timeout(10.0, connect=5.0)
        )
    async def close(self):
        await self.client.aclose()

    async def create_payment_url(self, data_url: CreatePaymentUrl, user_id: int) -> ReturnUrl:
        token_data = TokenData(user_id=user_id)
        token = create_access_token(data=token_data)
        header = {"Authorization": f"Bearer {token}"}
        url = "/pay-url/create_url"
        try:
            res = await self.client.post(url=url, json=data_url.model_dump(), headers=header)
            res.raise_for_status()
            return ReturnUrl(**res.json())
        except Exception as e:
            print(f"Don't get payment url: {e}")
            return None