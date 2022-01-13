import logging

# https://github.com/torproject/stem/issues/112
from stem.util.log import get_logger

_stemLogger = get_logger()
_stemLogger.propagate = False


def getLevelFromString(s):
    if s == "INFO":
        return logging.INFO
    elif s == "DEBUG":
        return logging.DEBUG
    elif s == "WARNING":
        return logging.WARNING
    elif s == "ERROR":
        return logging.ERROR
    elif s == "CRITICAL":
        return logging.CRITICAL


def getLogger(
    name,
    localLevel="INFO",
    rootLevel="INFO",
    logFile="LOG.log",
    logFileMode="w",
    console=False,
):
    handlers = [
        logging.FileHandler(logFile, mode=logFileMode),
    ]
    if console:
        handlers.append(logging.StreamHandler())

    # Config for root logger
    logging.basicConfig(
        format="%(name)-24s :: %(levelname)-8s :: %(asctime)s :: %(filename)-18s - L%(lineno)-3d :: %(message)s",
        handlers=handlers,
        level=getLevelFromString(rootLevel),
    )

    # Instantiate local logger
    logger = logging.getLogger(name)
    logger.setLevel(getLevelFromString(localLevel))

    return logger
