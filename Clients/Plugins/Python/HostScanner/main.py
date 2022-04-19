import logging
import nmap

logger = logging.getLogger(__name__.split('.')[-1])


class HostScanner:
    def __init__(self, subnet: str, possible_ports: list) -> None:
        self.__nmap = nmap.PortScanner()
        ports = ",".join(str(x) for x in possible_ports)
        self.__nmap.scan(hosts=subnet, arguments=f"-v -n -sP -PE -PA{ports}")

    def execute(self) -> list[dict]:
        data = []
        for result in self.__nmap.all_hosts():
            info = {
                "host": result,
                "status": self.__nmap[result]["status"]["state"]
            }
            data.append(info)
        return data


def run(config: dict) -> str:
    logger.info("HostScanner Starting")
    host_scanner = HostScanner(config["subnet"], config["possible_ports"])
    return host_scanner.execute()