import paramiko as pr

import logging

log = logging.getLogger(__name__)

class ServerManager():
    def __init__(self, host: str, port: int, password: str, username: str, container_name: str):
        if None in (host, port, password, username, container_name):
            raise ValueError("Missing required parameter")

        self._host = host
        self._port = port
        self._passworld = password
        self._username = username
        self._container_name = container_name

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
        data = self._run(f"docker exec {self._container_name} rcon-cli list")
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
        return self._run(f"docker exec {self._container_name} {command}")

    def _run(self, command: str) -> str:
        if self._client.get_transport() is None or not self._client.get_transport().is_active():
            self.connect()

        try:
            stdin, stdout, stderr = self._client.exec_command(command)
        except Exception as ex:
            log.error(f'{ex}')
            self.connect()
            stdin, stdout, stderr = self._client.exec_command(command)
        log.debug(f"\t_run: {stdin}, {stdout}, {stderr}")


        output = stdout.read().decode()
        error = stderr.read().decode()

        return output.strip() if output else error

    def close(self):
        self._client.close()
        log.info('Manager connect closed')
