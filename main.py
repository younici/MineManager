import os, asyncio
from dotenv import load_dotenv

from tools.server_manager import ServerManager
import bot.bot as bot

import logging
logging.basicConfig(
    level=logging.INFO,
    format="! [%(levelname)s] %(message)s"
)

from redis.asyncio import Redis

load_dotenv()

raw_admins = os.getenv("tg_admins")

if not raw_admins:
    raise RuntimeError("tg_admins not set")

admins = [int(adm.strip()) for adm in raw_admins.split(",") if adm.strip()]
token = os.getenv("token")

port =  int(os.getenv("port"))
host = os.getenv("host")
password = os.getenv("password")
username = os.getenv("serverusername")
container_name = os.getenv("container_name")

resid_url = os.getenv("redis_url")

mg: ServerManager | None = None

params = host, port, password, username, container_name

def get_server_manager() -> ServerManager:
    global mg
    if mg is None:
        mg = ServerManager(*params)
    return mg
 
async def main():
    try:
        global mg
        logging.info(params)
        mg = ServerManager(*params)
        if resid_url:
            redis = Redis.from_url(resid_url)
            logging.info("started with redis")
        else:
            redis = None
        asyncio.create_task(bot.start(token, admins, redis))
        await asyncio.Future()
    except Exception as e:
        logging.error(e)
    finally:
        mg.close()

if __name__ == "__main__":
    asyncio.run(main())