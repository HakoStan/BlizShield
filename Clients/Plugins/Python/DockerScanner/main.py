import logging
import docker
import datetime
import os

logger = logging.getLogger(__name__.split('.')[-1])


class DockerScanner:
    def __init__(self, docker_name: str, command: str) -> None:
        self.__command = command.split(' ')
        self.__docker_name = docker_name
        self.__client = docker.from_env()

    def execute(self, expr) -> list[dict]:
        res = None
        try:
            image = self.__client.images.get(self.__docker_name)
            res = self.__client.containers.run(image=image, command=self.__command)
        except Exception as ex:
            logger.error(f"Exception Occurred using docker {self.__docker_name} with {self.__command}")
            logger.error(f"{str(ex)}")

        is_vuln = False
        docker_info = []
        if res:
            if expr in str(res):
                is_vuln = True

        docker_info.append({"docker_name": self.__docker_name, "is_vunl": is_vuln, "status": is_vuln})
        return docker_info


def run(config: dict) -> str:
    logger.info("DockerScanner Starting")
    docker_scanner = DockerScanner(config["dockerName"], config["command"])
    return docker_scanner.execute(config["vuln_expression"])