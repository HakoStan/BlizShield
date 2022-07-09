import logging
import subprocess
import json


logger = logging.getLogger(__name__.split('.')[-1])
API_TOKEN = "fH62Oxk9nhwtADF9fiEaoSaaIJi1hcEbG2688C2dctk"

class WordpressScanner:
    def __init__(self, host: str, api_token: str) -> None:
        self.__host = host
        self.__api_token = API_TOKEN

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
            cmd = f"wpscan -f json --no-update --url {self.__host} --disable-tls-checks --api-token {self.__api_token}"
            logging.info(f"Executing command: {cmd}")
            output = subprocess.check_output(cmd.split(' '), shell=True)
        except subprocess.CalledProcessError as wpscan_err:
            output = wpscan_err.output

        if type(output) is bytes:
            output = output.decode("utf8")

        output = json.loads(output)
        for finding in output["interesting_findings"]:
            data.append({"type": finding["type"], "description": finding["to_s"], \
                "interesting_entries": finding["interesting_entries"], "status": True})

        for finding in output["version"]["vulnerabilities"]:
            finding["status"] = True
            data.append(finding)

        for finding in output["main_theme"]["vulnerabilities"]:
            finding["status"] = True
            data.append(finding)

        # TODO :: Add Plugins Vuln. Need to test on a site with plugins vulnable
        # TODO :: Test on a site with vulns
        return data


def run(config: dict) -> str:
    logger.info("WordpressScanner Starting")
    wordpress_scanner = WordpressScanner(config["host"])
    return wordpress_scanner.execute()
