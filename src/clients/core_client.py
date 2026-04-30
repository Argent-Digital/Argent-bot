import httpx

class ArgentCoreClient:
    def __init__(self, base_url: str = "http://127.0.0.1:8000"):
        self.base_url = base_url

    async def is_user_registered(self, user_id: int) -> bool:
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(f"{self.base_url}/users/{user_id}/check")
                response.raise_for_status()
                return response.json()
            except Exception as e:
                print(f"Ошибка при связи с Core: {e}")
                return False