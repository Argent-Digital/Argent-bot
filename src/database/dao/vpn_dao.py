from sqlalchemy import insert, select, update, UUID
from sqlalchemy.dialects.postgresql import insert
import uuid
from src.database.database import async_session_factory
from src.database.models import VpnKeysOrm

class VpnKeyDao:

    @classmethod
    async def add_vpn_key(
        cls, 
        user_id: int,
        server_key_id: str,
        key_name: str,
        access_url: str,
        protocol: str = "outline",
        vless_uuid: uuid.UUID | None = None
    ):
        async with async_session_factory() as session:
            stmt = (
                insert(VpnKeysOrm)
                .values(
                    user_id = user_id,
                    server_key_id = server_key_id,
                    key_name = key_name,
                    access_url = access_url, 
                    protocol = protocol,
                    vless_uuid = vless_uuid
                )
                .on_conflict_do_update(
                    index_elements=['user_id'],
                    set_={
                        'server_key_id': server_key_id,
                        'key_name': key_name,
                        'access_url': access_url,
                        "protocol": protocol,
                        "vless_uuid": vless_uuid
                    }
                )
            )

            await session.execute(stmt)
            await session.commit()

    @classmethod
    