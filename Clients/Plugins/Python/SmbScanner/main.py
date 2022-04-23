import logging
import socket
from smb import SMBConnection

logger = logging.getLogger(__name__.split('.')[-1])


class SmbChecker:
    def __init__(self, user: str, password: str,  ip: str, domain: str = "",
                 timeout=30) -> None:
        self.__user = user
        self.__password = password
        self.__ip = ip
        self.__domain = domain
        self.__timeout = timeout

    def execute(self) -> list[dict]:
        host = None
        info = {"ip": self.__ip, "host": "", "connected": False, "shares": []}

        # Gets computer name
        try:
            host = socket.gethostbyaddr(self.__ip)[0]
        except Exception as ex:
            logger.error(f"Exception translating {self.__ip} to hostname")
            logger.error(f"{str(ex)}")

        # If couldn't get computer name, return
        if not host:
            return [info]
        info["host"] = host

        try:
            con = SMBConnection.SMBConnection(self.__user, self.__password, socket.gethostname(), host, self.__domain, use_ntlm_v2=True)
            if not con.connect(self.__ip, 139):
                return [info]
        except Exception as ex:
            logger.error(f"Exception connecting {self.__ip}")
            logger.error(f"{str(ex)}")
            return [info]
        info["connected"] = True

        shares = con.listShares(timeout=self.__timeout)
        for share in shares:
            info["shares"].append({"name": share.name, "comments": share.comments})

        con.close()
        return [info]


def run(config: dict) -> str:
    logger.info("SmbScan Starting")
    if "domain" not in config.keys():
        smb_checker = SmbChecker(config["username"], config["password"], config["ip"])
    else:
        smb_checker = SmbChecker(config["username"], config["password"], config["ip"], config["domain"])
    return smb_checker.execute()








