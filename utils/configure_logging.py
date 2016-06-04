import logging
import logging.handlers
import sys

from game_config import MAX_LOG_BYTES, BACKUP_COUNT, LOG_TO_FILE


def setup_logging(log_level, log_file_name):
    logger = logging.getLogger('')
    logger.setLevel(log_level)
    log_format = logging.Formatter("%(asctime)s - %(module)s - %(levelname)s - %(message)s")

    ch = logging.StreamHandler(sys.stdout)
    ch.setFormatter(log_format)
    logger.addHandler(ch)

    if LOG_TO_FILE:
        fh = logging.handlers.RotatingFileHandler(log_file_name, maxBytes=MAX_LOG_BYTES, backupCount=BACKUP_COUNT)
        fh.setFormatter(log_format)
        logger.addHandler(fh)
