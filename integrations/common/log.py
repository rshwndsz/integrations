import logging

# https://github.com/torproject/stem/issues/112
from stem.util.log import get_logger
_stemLogger = get_logger()
_stemLogger.propagate = False


def getLogger(name, level=logging.INFO, console=False):
    handlers = [
        logging.FileHandler("LOG.log", mode="w"),
    ]
    if console:
        handlers.append(logging.StreamHandler())

    # Config for root logger
    logging.basicConfig(
        format="%(name)-24s :: %(levelname)-8s :: %(asctime)s :: %(filename)-18s - L%(lineno)-3d :: %(message)s",
        handlers=handlers,
        level=logging.DEBUG,
    )

    # Instantiate local logger
    logger = logging.getLogger(name)
    logger.setLevel(level)

    return logger
