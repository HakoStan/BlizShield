import logging
import ftplib


logger = logging.getLogger(__name__.split('.')[-1])


class FtpChecker:
    def __init__(self, ip: str, user: str = "anonymous", password: str = ""):
        self.__user = user
        self.__password = password
        self.__ip = ip

    def execute(self) -> list[dict]:
        server = None
        ftp_info = {}
        data = []
        connect = False

        # Init ftp connection
        try:
            server = ftplib.FTP()
            server.connect(self.__ip, 21)
            server.login(self.__user, self.__password)
            server.quit()
            connect = True
        except Exception as ex:
            logger.error(f"Exception login {self.__ip}")
            logger.error(f"{str(ex)}")

        ftp_info = {"ip": self.__ip, "protocol": "FTP",
                    "username": self.__user, "password": self.__password, "status": connect}
        data.append(ftp_info)
        return data


def run(config: dict) -> str:
    logger.info("FtpScan Starting")
    if "username" in config.keys() and "password" in config.keys():
        ftp_check = FtpChecker(config["ip"], config["username"], config["password"])
    else:
        ftp_check = FtpChecker(config["ip"])
    return ftp_check.execute()









