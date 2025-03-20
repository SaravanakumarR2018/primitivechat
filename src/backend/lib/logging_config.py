import os

log_format = os.getenv(
        "LOG_FORMAT",
        "%(asctime)s %(filename)s:%(lineno)d %(funcName)s %(levelname)s %(message)s"
    )