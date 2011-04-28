#import logging
import logging.handlers
#import sys

__author__ = "Markus Guenther"
    
def init_logger(logfile, level=logging.WARN, console=True):
    '''
    Initializes a logger that prints INFO messages to the stdout and
    DEBUG messages to an optional file. If you omit that file (logfile is None)
    than the logger will only print INFO messages.
    '''
    logger = logging.getLogger()
    if logfile: logger.setLevel(logging.DEBUG)
    else: logger.setLevel(level)
    
    formatter = logging.Formatter("%(name)s: %(asctime)s - %(levelname)s - %(message)s")
    
    consoleHandler = logging.StreamHandler()
    consoleHandler.setLevel(level)
    consoleHandler.setFormatter(formatter)
    logger.addHandler(consoleHandler)
    
    if not console:
        consoleHandler.setLevel(logging.CRITICAL)
    

    if logfile is not None:
        fileHandler = logging.handlers.RotatingFileHandler(logfile, maxBytes=1024*1024)
        fileHandler.setFormatter(formatter)
        fileHandler.setLevel(logging.DEBUG)
        logger.addHandler(fileHandler)
