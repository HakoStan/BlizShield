import logging
import subprocess
import datetime
import ftplib


logger = logging.getLogger(__name__.split('.')[-1])


class FtpChecker:
    def __init__(self, ip: str, user='anonymous', password='') -> None:
        self.__user = user
        self.__password = password
        self.__ip = ip

    def execute(self) -> list[dict]:
        server = ""
        ftp_info = {}
        data = []
        connect = True
        scan_timestamp = datetime.datetime.now(datetime.timezone.utc).astimezone().isoformat()

        # Init ftp connection
        try:
            server = ftplib.FTP()
            server.connect(self.__ip, 21)
        except Exception as ex:
            connect = False
            logger.error(f"Exception connecting to {self.__ip}")
            logger.error(f"{str(ex)}")

        try:
            server.login(self.__user, self.__password)

        except Exception as ex:
            connect = False
            logger.error(f"Exception login {self.__ip}")
            logger.error(f"{str(ex)}")

        ftp_info = {"ip": self.__ip, "protocol": "FTP",
                    "username": self.__user, "password": self.__password, "status": connect,
                    "@timestamp": scan_timestamp}
        data.append(ftp_info)
        return data


def run(config: dict) -> str:
    logger.info("FtpScan Starting")
    ftp_check = FtpChecker(config["ip"], config["username"], config["password"])
    return ftp_check.execute()









