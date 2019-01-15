import logging
import logging.handlers
import sys


def setup_logging(log_level):
    log_format = "%(asctime)s - %(module)s - %(levelname)s - %(message)s"
    logging.basicConfig(stream=sys.stdout, level=log_level, format=log_format)
    logging.getLogger()
