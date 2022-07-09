import logging
import socket

logger = logging.getLogger(__name__.split('.')[-1])


class TcpScanner:
    def __init__(self,
        ip: str,
        port: int) -> None:
        self.__ip = ip
        self.__port = port

    def __tcp_scan(self, ip: int, port: int) -> bool:
        conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        conn.settimeout(2)
        is_connected = True
        try:
            conn.connect((ip, port))
        except Exception:
            is_connected = False
        finally:
            conn.close()
        return is_connected

    def execute(self) -> list[dict]:
        data = []
        port_open = False
        tcp_port_info = {"ip": self.__ip, "port": self.__port, "protocol": "TCP", "port_open": False, "status": False}
        try:
            port_open = self.__tcp_scan(self.__ip, self.__port)
        except Exception as ex:
            logger.error(f"Exception Occurred Scanning TCP Port {self.__ip}:{self.__port}")
            logger.error(f"{str(ex)}")
        tcp_port_info["port_open"] = port_open
        tcp_port_info["status"] = port_open
        data.append(tcp_port_info)
        return data


def run(config: dict) -> str:
    logger.info("TcpScanner Starting")
    port_scanner = TcpScanner(config["ip"], int(config["port"]))
    return port_scanner.execute()
