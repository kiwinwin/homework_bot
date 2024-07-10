
class BaseError(Exception):
    """Базовое исключение."""

    def __init__(self, *args):
        """Init."""
        if args:
            self.message = args[0]
        else:
            self.message = None
        self.error_name = 'BaseError'

    def __str__(self):
        """Str."""
        if self.message:
            return f'{self.error_name}: {self.message}'
        else:
            return f'{self.error_name} has been raised'


class NoEnvVarError(BaseError):
    """Исключение для проверки переменных окружения."""

    def __init__(self, *args):
        """Init."""
        super().__init__(*args)
        self.error_name = 'NoEnvVarError'


class GetApiError(BaseError):
    """Исключение для проверки отправки запроса."""

    def __init__(self, *args):
        """Init."""
        super().__init__(*args)
        self.error_name = 'GetApiError'


class MessageSendingError(BaseError):
    """Исключение для отправки сообщения в тг."""

    def __init__(self, *args):
        """Init."""
        super().__init__(*args)
        self.error_name = 'MessageSendingError'


class ResponseCheckingError(BaseError):
    """Исключение для проверки ответа API."""

    def __init__(self, *args):
        """Init."""
        super().__init__(*args)
        self.error_name = 'ResponseCheckingError'


class StatusParsingError(BaseError):
    """Исключение для проверки статуса домашки."""

    def __init__(self, *args):
        """Init."""
        super().__init__(*args)
        self.error_name = 'StatusParsingError'


class GetStartTimeError(BaseError):
    """Исключение для первого запроса."""

    def __init__(self, *args):
        """Init."""
        super().__init__(*args)
        self.error_name = 'GetStartTimeError'


class RepeatedMessagesError(BaseError):
    """Исключение для проверки повторяющихся сообщений."""

    def __init__(self, *args):
        """Init."""
        super().__init__(*args)
        self.error_name = 'RepetedMessagesError'
