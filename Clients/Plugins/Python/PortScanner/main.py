import logging

logger = logging.getLogger(__name__.split('.')[-1])


def run(config: dict):
    logger.info("Running Plugin PortScanner")
