import sys

class Logger:
    logLevel = 0
    logger = None

    def logType(self, logType):
        logTypes = {
            "error": sys.stderr,
            "output": sys.stdout
        }
        self.logger = logTypes[logType]

    def log(self, msg, level=5):
        if level <= self.logLevel and self.logger:
            print(msg, file=self.logger)

    def set_loglevel(self, level):
        self.logLevel = level
        if level > 0:
            self.logger = self.logger or sys.stdout
        else:
            self.logger = None
