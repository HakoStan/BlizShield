import logging
import nmap
import requests

logger = logging.getLogger(__name__.split('.')[-1])


class HostScanner:
    def __init__(self, subnet: str, possible_ports: list) -> None:
        self.__nmap = nmap.PortScanner()
        self.__subnet = subnet
        self.__possible_ports = possible_ports
        self.__ports = possible_ports.split(',')

    def __is_host_accepting_requests(self, host: str) -> bool:
        for port in self.__ports:
            try:
                requests.get(f"http://{host}:{port}/")
                return True
            except Exception:
                pass
            try:
                requests.get(f"https://{host}:{port}/")
                return True
            except Exception:
                pass
        return False

    def execute(self) -> list[dict]:
        logger.info(f"Scanning {self.__subnet} using nmap - ports {self.__possible_ports}")
        self.__nmap.scan(hosts=self.__subnet, arguments=f"-v -n -sS -PE -PA{self.__possible_ports}")
        data = []
        for result in self.__nmap.all_hosts():
            status = False if self.__nmap[result]["status"]["state"] == 'down' else True
            if status is False:
                status = self.__is_host_accepting_requests(result)
            state = self.__nmap[result]["status"]["state"] if status is False else "UP"
            info = {
                "host": result,
                "state": state,
                "status": status
            }
            data.append(info)
        return data


def run(config: dict) -> str:
    logger.info("HostScanner Starting")
    host_scanner = HostScanner(config["subnet"], config["possible_ports"])
    return host_scanner.execute()
