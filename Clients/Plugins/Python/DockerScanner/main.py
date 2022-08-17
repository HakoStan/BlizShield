import logging
import docker
import datetime
import os

logger = logging.getLogger(__name__.split('.')[-1])

class DockerScanner:
    def __init__(self, docker_name: str, command: str, container_path: str) -> None:
        self.__command = command
        self.__docker_name = docker_name
        self.__container_path = container_path
        self.__client = docker.from_env()

    def execute(self) -> list[dict]:
        image = self.__client.images.pull(self.__docker_name)

        # ensure unique local output filename
        scan_timestamp = datetime.datetime.now(datetime.timezone.utc).astimezone().isoformat()

        container = self.__client.containers.run(image=image,
                                                 command=self.__command,
                                                 volumes={scan_timestamp:
                                                              {'bind': self.__container_path, 'mode': 'rw'}})

        docker_info = []
        with open(scan_timestamp, "r") as res:
            for line in res:
                res_list = line.split(',')
                docker_info.append({"docker_name": self.__docker_name, "ip": res_list[0],

                                    "port": res_list[1], "status": res_list[2],"@timestamp": scan_timestamp })
        os.remove(scan_timestamp)
        return docker_info

def run(config: dict) -> str:
    logger.info("DockerScanner Starting")
    docker_scanner = DockerScanner(config["dockerName"], config["command"], config["container_path"])
    return docker_scanner.execute()
