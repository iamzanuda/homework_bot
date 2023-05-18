class NoHTTPResponseError(Exception):
    """Если статус овета АПИ не равен 200."""

    pass


class NoStatusError(Exception):
    """Если API домашки возвращает недокументированный статус
    домашней работы либо домашку без статуса.
    """

    pass
