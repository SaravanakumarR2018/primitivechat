import os
import logging

log_format = os.getenv(
        "LOG_FORMAT",
        "%(asctime)s %(name)s %(filename)s:%(lineno)d %(funcName)s %(levelname)s %(message)s"
    )

_logging_configured = False

def get_primitivechat_logger(name):
    """
    Configure and return a logger for the given module name.
    Ensures logging.basicConfig is called only once.

    Args:
        name (str): The name of the logger, typically __name__ of the module.

    Returns:
        logging.Logger: Configured logger instance.
    """
    global _logging_configured
    if not _logging_configured:
        logging.basicConfig(level=logging.INFO, format=log_format)
        _logging_configured = True
    
    logger = logging.getLogger(name)
    logger.info(f"Logger initialized for {name}")
    return logger