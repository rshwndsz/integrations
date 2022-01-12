import logging

# https://github.com/torproject/stem/issues/112
from stem.util.log import get_logger
_stemLogger = get_logger()
_stemLogger.propagate = False


def getLogger(name, level=logging.INFO):
    # Config for root logger
    logging.basicConfig(
        format="%(name)-24s :: %(levelname)-8s :: %(asctime)s :: %(filename)-18s - L%(lineno)-3d :: %(message)s",
        handlers=[
            logging.FileHandler("LOG.log", mode="w"),
            logging.StreamHandler()
        ],
        level=logging.DEBUG,
    )

    # Instantiate local logger
    logger = logging.getLogger(name)
    logger.setLevel(level)

    return logger
