import logging
import argparse
import asyncio

from .Framework import utils
from .Core.core import Core


# Logger
logFormatter = logging.Formatter("%(asctime)s [%(threadName)-12.12s] %(name)-12s: %(levelname)-8s %(message)s")
rootLogger = logging.getLogger()

fileHandler = logging.FileHandler(filename="error.log", encoding="utf-8")
fileHandler.setFormatter(logFormatter)
fileHandler.setLevel(logging.DEBUG)
rootLogger.addHandler(fileHandler)

consoleHandler = logging.StreamHandler()
consoleHandler.setLevel(logging.DEBUG)
consoleHandler.setFormatter(logFormatter)
rootLogger.addHandler(consoleHandler)
rootLogger.setLevel(logging.DEBUG)


async def run_core(config):
    core = Core(**config["core"])
    await core.run()


def logic(args):
    loop = asyncio.get_event_loop()
    config = utils.read_config()

    # TODO: Break on keyboard interrupt
    if args.core:
        loop.run_until_complete(run_core(config))
        loop.run_forever()


def main():
    # TODO: Accept config name as a parameter.
    parser = argparse.ArgumentParser(description="BlizShield Core - Running Plugins")
    parser.add_argument("--core", help='Run Core', action='store_true', default=False)

    logic(parser.parse_args())


if __name__ == "__main__":
    main()
