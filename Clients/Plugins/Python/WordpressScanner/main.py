import logging
import subprocess


logger = logging.getLogger(__name__.split('.')[-1])


class WordpressScanner:
    def __init__(self, host: str, api_token: str) -> None:
        self.__host = host
        self.__api_token = api_token

    def execute(self) -> list[dict]:
        data = []
        start = False
        vuln_list = []
        vuln_count = 0

        # Run Command
        # This is wpscan that is install with gem (Ruby)
        # The API Token is of wpscan site. We only have 25 requests per day
        # For windows you will also need libcurl.dll in $PATH
        output = ""
        try:
            output = subprocess.check_output(f"wpscan --url {self.__host} --disable-tls-checks --api-token {self.__api_token}".split(' '), shell=True)
        except subprocess.CalledProcessError as wpscan_err:
            output = wpscan_err.output
        
        if type(output) is bytes:
            output = output.decode("utf8")
        # Parse
        # Windows Line Parsing is with \r\n. Might not work on linux
        for line in output.split("\r\n"):
            if "vulnerabilities identified" in line:
                start = True
                st = "\x1b[31m[!]\x1b[0m "
                ed = "vulnerabilities"
                vuln_count = int(line[line.index(st) + len(st):line.index(ed)].strip())
            if start:
                tl = "Title:"
                if tl in line:
                    vuln_list.append(line[line.index(tl) + len(tl):].strip())
        data.append({"vuln_found": start, "vuln_list": vuln_list, "vuln_count": vuln_count})
        return data


def run(config: dict) -> str:
    logger.info("WordpressScanner Starting")
    wordpress_scanner = WordpressScanner(config["host"], config["api_token"])
    return wordpress_scanner.execute()
