import logging
import logging.handlers
import sys

from game_config import MAX_LOG_BYTES, BACKUP_COUNT, LOG_TO_FILE


def setup_logging(log_level, log_file_name):
    log_format = "%(asctime)s - %(module)s - %(levelname)s - %(message)s"
    logging.basicConfig(stream=sys.stdout, level=log_level, format=log_format)
    logger = logging.getLogger()

    if LOG_TO_FILE:
        fh = logging.handlers.RotatingFileHandler(log_file_name, maxBytes=MAX_LOG_BYTES, backupCount=BACKUP_COUNT)
        fh.setFormatter(logging.Formatter(log_format))
        logger.addHandler(fh)
