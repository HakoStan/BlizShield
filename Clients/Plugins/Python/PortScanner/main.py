import logging
import socket
import datetime

logger = logging.getLogger(__name__.split('.')[-1])


class PortScanner:
    def __init__(self,
        ip: str,
        start_port: int,
        end_port: int) -> None:
        self.__ip = ip
        self.__start_port = start_port
        self.__end_port = end_port

    def __tcp_scan(self, ip: int, port: int) -> bool:
        conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        conn.settimeout(0.5)
        is_connected = True
        try:
            conn.connect((ip, port))
        except Exception:
            is_connected = False
        finally:
            conn.close()
        return is_connected

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
        for port in range(self.__start_port, self.__end_port):
            tcp_port_info = {"ip": self.__ip, "port": port, "protocol": "TCP", "port_open": False, "status": False}
            try:
                tcp_port = self.__tcp_scan(self.__ip, port)
            except Exception as ex:
                logger.error(f"Exception Occurred Scanning TCP Port {self.__ip}:{port}")
                logger.error(f"{str(ex)}")

            tcp_port_info["port_open"] = tcp_port
            tcp_port_info["status"] = tcp_port

            udp_port_info = {"ip": self.__ip, "port": port, "protocol": "UDP", "port_open": False, "status": False}
            try:
                udp_port = self.__udp_scan(self.__ip, port)
            except Exception as ex:
                logger.error(f"Exception Occurred Scanning UDP Port {self.__ip}:{port}")
                logger.error(f"{str(ex)}")

            udp_port_info["port_open"] = udp_port
            udp_port_info["status"] = udp_port
            data.extend([tcp_port_info, udp_port_info])
        return data


def run(config: dict) -> str:
    logger.info("PortScanner Starting")
    port_scanner = PortScanner(config["ip"], config["start_port"], config["end_port"])
    return port_scanner.execute()
