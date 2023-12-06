import logging
from typing import Dict


class CdxmlLogger(logging.Logger):
    formatter = logging.Formatter(
        fmt="[%(levelname)s] %(name)s => %(message)s",
    )

    def __init__(self, name, fields=None):
        self.fields = fields if fields else {}
        super(CdxmlLogger, self).__init__(name, logging.DEBUG)
        stdHandler = logging.StreamHandler()
        stdHandler.setFormatter(self.formatter)
        self.addHandler(stdHandler)

    def formatFields(self, fields: Dict) -> str:
        fields = fields if fields else {}
        fields.update(self.fields)

        if not fields:
            return ""

        return " " + " ".join(["%s=%s" % (k, v) for k, v in fields.items()])

    def debug(self, msg, fields=None, **kwargs):
        msg += self.formatFields(fields)
        super(CdxmlLogger, self).debug(msg, **kwargs)

    def info(self, msg, fields=None, **kwargs):
        msg += self.formatFields(fields)
        super(CdxmlLogger, self).info(msg, **kwargs)

    def warning(self, msg, fields=None, **kwargs):
        msg += self.formatFields(fields)
        super(CdxmlLogger, self).warning(msg, **kwargs)

    def error(self, msg, fields=None, exc_info=True, **kwargs):
        msg += self.formatFields(fields)
        super(CdxmlLogger, self).error(
            msg=msg, exc_info=exc_info, **kwargs
        )

    def critical(self, msg, fields=None, **kwargs):
        msg += self.formatFields(fields)
        super(CdxmlLogger, self).critical(msg=msg, **kwargs)
