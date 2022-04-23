import logging
import subprocess
import datetime
import socket
from smb import SMBConnection

logger = logging.getLogger(__name__.split('.')[-1])


class SmbChecker:
    def __init__(self, user: str, password: str, client: str, ip: str, domain: str,
                 timeout=30) -> None:
        self.__user = user
        self.__password = password
        self.__client = client
        self.__ip = ip
        self.__domain = domain
        self.__timeout = timeout

    def execute(self) -> list[dict]:
        output = ""
        host = ""
        shares = []
        data = []
        scan_timestamp = datetime.datetime.now(datetime.timezone.utc).astimezone().isoformat()

        # Gets computer name
        try:
            host = socket.gethostbyaddr(self.__ip)
        except Exception as ex:
            logger.error(f"Exception translating {self.__ip} to hostname")
            logger.error(f"{str(ex)}")

        try:
            con = SMBConnection.SMBConnection(self.__user, self.__password, self.__client, host,
                             self.__domain, use_ntlm_v2=True)
            con.connect(host, 139)
        except Exception as ex:
            logger.error(f"Exception connecting {self.__ip}")
            logger.error(f"{str(ex)}")

        shares = con.listShares(timeout=self.__timeout)
        for share in shares:
            share_info = {"ip": self.__ip, "host": host, "protocol": "SMB",
                             "share_name": shares.name, "@timestamp": scan_timestamp}
            data.append(share_info)

        return data

    def run(config: dict) -> str:
        logger.info("SmbScan Starting")
        smb_checker = SmbChecker(config["user"], config["password"], config["client"],
                               config["ip"], config["domain"])
        return smb_checker.execute()








