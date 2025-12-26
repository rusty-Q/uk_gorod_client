from dataclasses import dataclass
from typing import Optional

@dataclass
class Credentials:
    """Учетные данные для входа"""
    email: str
    password: str

@dataclass
class MeterReading:
    """Данные счетчика"""
    id: str                    # MeterReadingId из hidden input
    service: str              # Услуга (Электроснабжение, Отопление и т.д.)
    serial_number: str        # Заводской номер
    last_reading_date: str    # Дата последнего показания
    last_reading_value: str   # Значение последнего показания
    next_verification: str    # Дата следующей поверки
    # Поля для ввода новых показаний
    current_value: Optional[str] = None      # Текущее значение для ввода
    input_field_name: str = "InputValCnt"    # Имя поля для ввода
    
    def __str__(self):
        return f"{self.service} (SN: {self.serial_number}, ID: {self.id})"

@dataclass
class SubmissionResult:
    """Результат отправки показаний"""
    success: bool
    message: str
    validated: Optional[dict] = None  # {meter_id: bool} - результаты проверки
