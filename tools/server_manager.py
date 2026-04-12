import asyncio
import re
import logging
import struct
import asyncssh

log = logging.getLogger(__name__)

class ServerManager:
    def __init__(self, host: str, port: int, password: str, username: str, container_name: str, rcon_pass: str):
        if None in (host, port, password, username, container_name, rcon_pass):
            raise ValueError("Missing required parameter")

        self._host = host
        self._port = port
        self._password = password 
        self._username = username
        self._container_name = container_name
        self._rcon_pass = rcon_pass

        self._conn = None
        log.info("Manager inited")

    # --- Вспомогательный метод для чистого RCON (без внешних библиотек) ---
    async def _internal_rcon_command(self, command: str) -> str:
        """Реализация протокола RCON на чистом asyncio"""
        reader, writer = await asyncio.open_connection(self._host, 25575)
        try:
            async def send_packet(pkt_type, payload):
                # Формат RCON: Length(4b), ID(4b), Type(4b), Payload(str), Null(2b)
                pkt_id = 42
                data = struct.pack("<ii", pkt_id, pkt_type) + payload.encode('utf-8') + b"\x00\x00"
                writer.write(struct.pack("<i", len(data)) + data)
                await writer.drain()
                
                # Читаем ответ
                raw_len = await reader.readexactly(4)
                length = struct.unpack("<i", raw_len)[0]
                raw_data = await reader.readexactly(length)
                res_id, res_type = struct.unpack("<ii", raw_data[:8])
                return res_id, raw_data[8:-2].decode('utf-8')

            # 1. Авторизация (тип 3)
            auth_id, _ = await send_packet(3, self._rcon_pass)
            if auth_id == -1:
                return "❌ Ошибка: Неверный RCON пароль"

            # 2. Выполнение команды (тип 2)
            _, response = await send_packet(2, command)
            return response
        finally:
            writer.close()
            await writer.wait_closed()

    async def exec_server(self, command: str) -> str:
        try:
            # Используем наш внутренний асинхронный метод вместо MCRcon
            resp = await asyncio.wait_for(self._internal_rcon_command(command), timeout=5.0)
            log.info(f"Direct RCON Result: {resp}")
            return self.clean_ansi(resp) if resp else "✅ Команда выполнена (без вывода)"
        except ConnectionRefusedError:
            return "❌ Ошибка: RCON порт закрыт (сервер выключен)."
        except asyncio.TimeoutError:
            return "❌ Ошибка: Таймаут RCON (сервер не ответил)."
        except Exception as e:
            log.error(f"RCON Error: {e}")
            return f"❌ Ошибка RCON: {e}"

    # --- Остальные методы (SSH и обертки) ---

    async def _run(self, command: str) -> str:
        if self._conn is None or self._conn.is_closed():
            log.info("SSH session is inactive. Connecting...")
            await self.connect()
        try:
            result = await asyncio.wait_for(self._conn.run(command), timeout=10.0)
            return str(result.stdout).strip() if result.stdout else str(result.stderr).strip()
        except Exception as ex:
            log.error(f"SSH Command '{command}' failed: {ex}")
            try: await self.connect()
            except: pass
            raise TimeoutError("SSH channel timed out")

    async def connect(self):
        if self._conn:
            self._conn.close()
            await self._conn.wait_closed()
        self._conn = await asyncssh.connect(
            host=self._host, port=self._port,
            username=self._username, password=self._password,
            known_hosts=None
        )
        log.info(f'Manager SSH connected')

    async def start_server(self):
        log.info(await self._run(f'docker start {self._container_name}'))

    async def check_status(self) -> bool:
        result = (await self._run(f"docker inspect -f '{{{{.State.Running}}}}' {self._container_name}")).replace("\n", "")
        return result == "true"

    async def stop_server(self):
        await self.exec_server("stop")
        await asyncio.sleep(15)
        await self._run(f'docker stop {self._container_name}')
    
    async def restart_server(self) -> str:
        if await self.check_status():
            await self.stop_server()
        await self.start_server()
    
    async def get_logs(self, tails: int = 50) -> str | None:
        return await self._run(f'docker logs {self._container_name} {f"--tail={tails}" if tails != 0 else ""}')
    
    async def clear_logs(self):
        return await self._run(f"truncate -s 0 $(docker inspect --format='{{{{.LogPath}}}}' {self._container_name})")
    
    async def get_players_list(self) -> list[str] | None:
        data = await self.exec_server("list")
        if "Failed" in data or "❌" in data: return None
        try:
            result = data.split(sep=":", maxsplit=2)[1].strip().split(sep=",")
            return None if result[0] == '' else result
        except: return None
    
    async def get_uptime(self) -> str:
        command = f"docker ps -a --filter 'name={self._container_name}' --format '{{{{.Status}}}}'"
        result = await self._run(command)
        return result if result else "Container not found"

    async def close(self):
        if self._conn:
            self._conn.close()
            await self._conn.wait_closed()

    def clean_ansi(self, text: str) -> str:
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        text = ansi_escape.sub('', text)
        minecraft_escape = re.compile(r'§[0-9a-fk-orx]')
        return minecraft_escape.sub('', text).strip()