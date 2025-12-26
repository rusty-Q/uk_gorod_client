class UKGorodError(Exception):
    """Базовое исключение библиотеки"""
    pass

class AuthenticationError(UKGorodError):
    """Ошибка аутентификации"""
    pass

class ParseError(UKGorodError):
    """Ошибка парсинга данных"""
    pass

class SubmissionError(UKGorodError):
    """Ошибка отправки данных"""
    pass

class ValidationError(UKGorodError):
    """Ошибка валидации данных"""
    pass

class IntegrationError(UKGorodError):
    """Ошибка интеграции с внешними системами"""
    pass
