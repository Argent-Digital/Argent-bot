from sqlalchemy import insert, select, update, func
from sqlalchemy.dialects.postgresql import insert
from src.database.database import async_session_factory
from src.database.models import UsersOrm, VpnKeysOrm
import json
import subprocess

class AdminDao:

    @classmethod 
    async def get_stats(cls):
        async with async_session_factory() as session:
            user_query = select(func.count(UsersOrm.id))
            key_query = select(func.count(VpnKeysOrm.key_id))

            users_res = await session.execute(user_query)
            key_res = await session.execute(key_query)

            # Трафик из vnstat (текущий день)
            try:
                traffic_raw = subprocess.check_output(['vnstat', '--json']).decode('utf-8')
                traffic_data = json.loads(traffic_raw)
                
                stats_today = traffic_data['interfaces'][0]['traffic']['day'][-1]
                
                rx_raw = stats_today['rx']
                tx_raw = stats_today['tx']
                
                rx = round(rx_raw / (1024**3), 2)
                tx = round(tx_raw / (1024**3), 2)
                total_gb = round(rx + tx, 2)
                
                if total_gb < 0.01:
                    rx = round(rx_raw / (1024**2), 2)
                    tx = round(tx_raw / (1024**2), 2)
                    total_gb = round(rx + tx, 2)

            except Exception as e:
                rx = tx = total_gb = "ошибка"

            return {
                "users": users_res.scalar() or 0,
                "keys": key_res.scalar() or 0,
                "traffic": total_gb,
                "rx": rx,
                "tx": tx
            }


