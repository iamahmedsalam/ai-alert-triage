import logging
from src.config import load_config


def setup_logger():
    config = load_config()
    log_file = config["logging"]["file"]
    log_level = config["logging"]["level"]

    logger = logging.getLogger("triage")
    logger.setLevel(getattr(logging, log_level))

    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(getattr(logging, log_level))

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARNING)

    formatter = logging.Formatter(
        "%(asctime)s — %(levelname)s — %(message)s"
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger
