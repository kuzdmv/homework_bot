class CanNotConnect(Exception):
    def __init__(self, error, message="Невозможно поключится"):
        self.error = error
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return f'{self.message} -> {self.error}'


class HTTPStatusError(Exception):
    def __init__(self, status, message="200"):
        self.status = status
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return f'Ошибка статуса сервера с ДЗ {self.status} != {self.message}'


class EmptyListError(Exception):
    def __init__(self, message="Получен пустой словарь"):
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return f'{self.message}'


class JsonError(Exception):
    def __init__(self, message="Ответ с сервера не преобразуется в json"):
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return f'{self.message}'


class CanNotSendMsg(Exception):
    def __init__(self, error, message="Не удалось отправить сообщение"):
        self.error = error
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return f'{self.message} -> {self.error}'
