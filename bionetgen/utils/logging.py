import colorlog

# global log level, can be set using
# from bionetgen.utils import logging
# logging.log_level = "DEBUG"
# options are "INFO","DEBUG","WARNING","ERROR","CRITICAL"
log_level = None

# set colorlog handler
fmter = colorlog.ColoredFormatter(
    "%(log_color)s%(levelname)s:%(name)s:%(message)s",
    log_colors={
        "DEBUG": "cyan",
        "INFO": "green",
        "WARNING": "yellow",
        "ERROR": "red",
        "CRITICAL": "red",
    },
)


class BNGLogger:
    def __init__(self, app=None, level="INFO"):
        self.app = app
        # global ll overrides everything
        if log_level is not None:
            self.level = log_level
        # cli is second most important
        elif self.app is not None:
            if self.app.pargs.debug:
                self.level = "DEBUG"
                if self.level != self.app.log.get_level():
                    self.app.log.set_level(self.level)
            elif self.app.pargs.log_level is not None:
                self.level = app.pargs.log_level
                if self.level != self.app.log.get_level():
                    self.app.log.set_level(self.level)
        # what this is instantiated with is the least
        # at least for now
        else:
            self.level = level

    def get_logger(self, loc=None):
        if loc is None:
            logger = colorlog.getLogger()
        else:
            loc_full = loc.split(":")[-1]
            module_name = loc_full.split(".")[0].strip()
            logger = colorlog.getLogger(module_name)
        if not logger.hasHandlers():
            handler = colorlog.StreamHandler()
            handler.setFormatter(fmter)
            logger.addHandler(handler)
        logger.setLevel(self.level)
        return logger

    def debug(self, msg, loc=None):
        if self.app is None:
            logger = self.get_logger(loc=loc)
            logger.debug(msg)
        else:
            self.app.log.debug(msg, loc)

    def info(self, msg, loc=None):
        if self.app is None:
            logger = self.get_logger(loc=loc)
            logger.info(msg)
        else:
            self.app.log.info(msg, loc)

    def warning(self, msg, loc=None):
        if self.app is None:
            logger = self.get_logger(loc=loc)
            logger.warning(msg)
        else:
            self.app.log.warning(msg, loc)

    def error(self, msg, loc=None):
        if self.app is None:
            logger = self.get_logger(loc=loc)
            logger.error(msg)
        else:
            self.app.log.error(msg, loc)

    def critical(self, msg, loc=None):
        if self.app is None:
            logger = self.get_logger(loc=loc)
            logger.critical(msg)
        else:
            self.app.log.critical(msg, loc)
