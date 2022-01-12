import logging


def getLogger(name, level=logging.INFO):
    # Config for root logger
    logging.basicConfig(
        format="%(name)s :: %(levelname)-8s :: %(asctime)s :: %(filename)s - L%(lineno)-3d :: %(message)s",
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
