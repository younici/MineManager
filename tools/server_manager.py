import paramiko as pr
import re

from mcrcon import MCRcon

import logging

log = logging.getLogger(__name__)

class ServerManager():
    def __init__(self, host: str, port: int, password: str, username: str, container_name: str, rcon_pass: str):
        if None in (host, port, password, username, container_name, rcon_pass):
            raise ValueError("Missing required parameter")

        self._host = host
        self._port = port
        self._passworld = password
        self._username = username
        self._container_name = container_name
        self._rcon_pass = rcon_pass

        self._client = pr.SSHClient()
        self._client.set_missing_host_key_policy(pr.AutoAddPolicy())
        self.connect()
        log.info("Manager inited")

    def start_server(self):
        log.info(self._run(f'docker start {self._container_name}'))

    def check_status(self) -> bool:
        result = self._run(
            f"docker inspect -f '{{{{.State.Running}}}}' {self._container_name}"
        ).replace("\n", "")
        log.info(f'server status: {result == "true"} {result}')
        return result == "true"

    def stop_server(self):
        log.info(self._run(f'docker stop {self._container_name}'))
    
    def restart_server(self) -> str:
        return self._run(f'docker restart {self._container_name}')
    
    def get_logs(self, tails: int = 50) -> str | None:
        return self._run(f'docker logs {self._container_name} {f"--tail={tails}" if tails != 0 else ""}')
    
    def clear_logs(self):
        return self._run(f"truncate -s 0 $(docker inspect --format='{{{{.LogPath}}}}' {self._container_name})")
    
    def get_players_list(self) -> list[str] | None:
        data = self.exec_server("rcon-cli list")
        if "Failed" in data:
            return None
        
        result = data.split(sep=":", maxsplit=2)[1].strip().split(sep=",")
        if result[0] == '':
            return None
        return result
    
    def get_uptime(self) -> str:
        """Returns a string with the container's uptime (e.g. 'Up 2 hours')"""
        command = f"docker ps -a --filter 'name={self._container_name}' --format '{{{{.Status}}}}'"
        result = self._run(command)
        
        if not result:
            return "Container not found"
        
        log.info(f"Server uptime/status: {result}")
        return result

    def connect(self):
        self._client.connect(
            hostname=self._host,
            port=self._port,
            username=self._username,
            password=self._passworld,
            timeout=15
        )
        log.info(f'Manager client connected')

    def exec_server(self, command: str) -> str:
        try:
            # Подключаемся к RCON напрямую, минуя SSH и Docker
            with MCRcon(
                host=self._host, 
                password=self._rcon_pass, 
                port=25575, 
                timeout=5.0
            ) as mcr:
                resp = mcr.command(command)
                log.info(f"Direct RCON Result: {resp}")
                return self.clean_ansi(resp) if resp else "✅ Команда выполнена (без вывода)"
        except ConnectionRefusedError:
            return "❌ Ошибка: RCON порт закрыт (сервер выключен или загружается)."
        except Exception as e:
            log.error(f"RCON Error: {e}")
            return f"❌ Ошибка RCON: {e}"
     
    def _run(self, command: str) -> str:
        if self._client.get_transport() is None or not self._client.get_transport().is_active():
            log.info("SSH session is inactive. Reconnecting...")
            self.connect()

        try:
            # Устанавливаем таймаут на выполнение
            stdin, stdout, stderr = self._client.exec_command(command, timeout=10.0)
            
            # ИСПРАВЛЕНО: Обязательно ставим таймаут на ЧТЕНИЕ из канала (защита от вечного зависания)
            stdout.channel.settimeout(10.0)
            stderr.channel.settimeout(10.0)

            output = stdout.read().decode()
            error = stderr.read().decode()

            log.debug(f"\t_run command: {command} | Error stream: {error}")
            return output.strip() if output else error.strip()

        except Exception as ex:
            # Если произошла ошибка (например TimeoutError), мы НЕ запускаем команду снова вглухую.
            # Мы логируем её, переподключаемся на будущее и пробрасываем ошибку дальше боту.
            log.error(f"SSH Command '{command}' failed with error: {ex}")
            try:
                self.connect() # Восстанавливаем соединение для будущих команд
            except:
                pass
            
            # Пробрасываем ошибку, чтобы бот мог написать вам "TimeOut", а не завис.
            raise TimeoutError("SSH/RCON channel timed out")

    def close(self):
        self._client.close()
        log.info('Manager connect closed')

    def clean_ansi(self, text: str) -> str:
        # Удаляем ANSI escape sequences (цвета консоли)
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        text = ansi_escape.sub('', text)
        
        # Удаляем цветовые коды Minecraft (§ и последующий символ)
        minecraft_escape = re.compile(r'§[0-9a-fk-orx]')
        text = minecraft_escape.sub('', text)
        
        return text.strip()