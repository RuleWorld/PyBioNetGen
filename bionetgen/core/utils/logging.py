import colorlog

# global log level, can be set using
# from bionetgen.core.utils import logging
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
    """
    Logger class that handles all logging in PyBNG. This class
    specifically tries to bridge the gap of using colorlog by
    itself and Cement frameworks own logging system.

    See [python logging](https://docs.python.org/3/howto/logging.html)
    for more information how logging in python works in general.

    Usage: BNGLogger()
           BNGLogger(app=app, level="DEBUG")

    Attributes
    ----------
    app : Cement App
        if using the logger with Cement framework, this will be the
        Cement app and each method will call app.log
    loc : str
        this attribute keeps track of the location string for better
        error reporting. for cement app this will be passed directly
        to app.log, for regular logging this will be parsed to get
        the right logger
    log_level : str
        this attribute sets the logging level to output. Options are
        the same as regular python logging, "DEBUG", "INFO", "WARNING",
        "ERROR", "CRITICAL"

    Methods
    -------
    get_logger : logger
        this method returns the correct logger after parsing the loc string
    debug : None
        same as all python logging, writes a message at DEBUG level
    info : None
        same as all python logging, writes a message at INFO level
    warning : None
        same as all python logging, writes a message at WARNING level
    error : None
        same as all python logging, writes a message at ERROR level
    critical : None
        same as all python logging, writes a message at CRITICAL level
    """

    def __init__(self, app=None, level="INFO", loc=None):
        self.app = app
        self.loc = loc
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
        """
        From a given loc string returns the correct python
        logger. Loc string should be of the form:

        'FILE_PATH : MODULE.METHOD'
        """
        if loc is None:
            if self.loc is None:
                logger = colorlog.getLogger()
            else:
                loc_full = self.loc.split(":")[-1]
                module_name = loc_full.split(".")[0].strip()
                logger = colorlog.getLogger(module_name)
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
        """
        Debug level messages
        """
        if self.app is None:
            logger = self.get_logger(loc=loc)
            if loc is not None:
                msg = f"from: {loc} : {msg}"
            elif self.loc is not None:
                msg = f"from: {self.loc} : {msg}"
            logger.debug(msg)
        else:
            self.app.log.debug(msg, loc)

    def info(self, msg, loc=None):
        """
        Info level messages
        """
        if self.app is None:
            logger = self.get_logger(loc=loc)
            if loc is not None:
                msg = f"from: {loc} : {msg}"
            elif self.loc is not None:
                msg = f"from: {self.loc} : {msg}"
            logger.info(msg)
        else:
            self.app.log.info(msg, loc)

    def warning(self, msg, loc=None):
        """
        Warning level messages
        """
        if self.app is None:
            logger = self.get_logger(loc=loc)
            if loc is not None:
                msg = f"from: {loc} : {msg}"
            elif self.loc is not None:
                msg = f"from: {self.loc} : {msg}"
            logger.warning(msg)
        else:
            self.app.log.warning(msg, loc)

    def error(self, msg, loc=None):
        """
        Error level messages
        """
        if self.app is None:
            logger = self.get_logger(loc=loc)
            if loc is not None:
                msg = f"from: {loc} : {msg}"
            elif self.loc is not None:
                msg = f"from: {self.loc} : {msg}"
            logger.error(msg)
        else:
            self.app.log.error(msg, loc)

    def critical(self, msg, loc=None):
        """
        Critical level messages
        """
        if self.app is None:
            logger = self.get_logger(loc=loc)
            if loc is not None:
                msg = f"from: {loc} : {msg}"
            elif self.loc is not None:
                msg = f"from: {self.loc} : {msg}"
            logger.critical(msg)
        else:
            self.app.log.critical(msg, loc)
