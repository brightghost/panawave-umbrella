import logging

def create_logger(level=logging.DEBUG):
    '''Instantiate and configure the logger.'''
    fmt="%(asctime)s (%(levelname)s): %(message)s <%(funcName)s, %(module)s:%(lineno)d>"
    datefmt="%H:%M:%S"
    logging.basicConfig(
            format=fmt,
            datefmt=datefmt,
            level=level)
    logging.debug("Logging started!")
