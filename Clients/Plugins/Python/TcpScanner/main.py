import logging
import socket

logger = logging.getLogger(__name__.split('.')[-1])


class TcpScanner:
    def __init__(self,
        ip: str,
        port: int) -> None:
        self.__ip = ip
        self.__port = port

    def __udp_scan(self, ip: int, port: int) -> bool:
        conn = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        conn.settimeout(0.5)

        is_connected = True
        try:
            conn.connect((ip, port))
            conn.send(bytes(0))
            conn.recv(1024)
        except Exception:
            is_connected = False
        finally:
            conn.close()
        return is_connected

    def execute(self) -> list[dict]:
        data = []
        udp_port_info = {"ip": self.__ip, "port": self.__port, "protocol": "UDP", "port_open": False, "status": False}
        try:
            port_open = self.__udp_scan(self.__ip, self.__port)
        except Exception as ex:
            logger.error(f"Exception Occurred Scanning UDP Port {self.__ip}:{self.__port}")
            logger.error(f"{str(ex)}")
        udp_port_info["port_open"] = port_open
        udp_port_info["status"] = port_open
        data.append(udp_port_info)
        return data


def run(config: dict) -> str:
    logger.info("TcpScanner Starting")
    port_scanner = TcpScanner(config["ip"], config["port"])
    return port_scanner.execute()
