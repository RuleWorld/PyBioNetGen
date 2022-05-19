import logging


class BNGLogger:
    def __init__(self, app=None):
        self.app = app

    def debug(self, msg, loc=None, name=None):
        if self.app is None:
            if name is None:
                logger = logging.getLogger()
            else:
                logger = logging.getLogger(name)
            logger.debug(msg + f" from: {loc}")
        else:
            self.app.log.debug(msg, loc)

    def info(self, msg, loc=None, name=None):
        if self.app is None:
            if name is None:
                logger = logging.getLogger()
            else:
                logger = logging.getLogger(name)
            logger.info(msg + f" from: {loc}")
        else:
            self.app.log.info(msg, loc)

    def warning(self, msg, loc=None, name=None):
        if self.app is None:
            if name is None:
                logger = logging.getLogger()
            else:
                logger = logging.getLogger(name)
            logger.warning(msg + f" from: {loc}")
        else:
            self.app.log.warning(msg, loc)

    def error(self, msg, loc=None, name=None):
        if self.app is None:
            if name is None:
                logger = logging.getLogger()
            else:
                logger = logging.getLogger(name)
            logger.error(msg + f" from: {loc}")
        else:
            self.app.log.error(msg, loc)

    def critical(self, msg, loc=None, name=None):
        if self.app is None:
            if name is None:
                logger = logging.getLogger()
            else:
                logger = logging.getLogger(name)
            logger.critical(msg + f" from: {loc}")
        else:
            self.app.log.critical(msg, loc)
