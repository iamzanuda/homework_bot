class NoHTTPResponseError(Exception):
    """Если статус овета АПИ не равен 200."""

    pass


class NoAPIResponseError(Exception):
    """Если API домашки не отвечает."""

    pass
