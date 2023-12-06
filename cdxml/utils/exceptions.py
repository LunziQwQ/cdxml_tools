class BaseError(Exception):
    def __init__(self, msg: str, *args: object) -> None:
        self.msg = msg
        super().__init__(msg, *args)

class CdxmlHaveNoPageError(BaseError):
    def __init__(self):
        msg = "CDXML have no pages."
        super(CdxmlHaveNoPageError, self).__init__(msg)
