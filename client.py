import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from typing import List, Dict, Optional
from datetime import datetime
import json
from .models import MeterReading, LoginCredentials
from .exceptions import AuthenticationError, ParseError, SubmissionError
from .utils.serial_normalizer import normalize_serial_number

class UKGorodClient:
    """Клиент для работы с порталом УК Город"""
    
    def __init__(self, base_url: str = "https://nd.inno-e.ru", user_agent: str = None):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': user_agent or 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Host': urlparse(base_url).netloc
        })
        self._is_authenticated = False
        self._csrf_token = None
        
    def login(self, credentials: LoginCredentials) -> bool:
        """Аутентификация на портале"""
        try:
            # 1. Получаем начальный редирект
            start_url = f"{self.base_url}/gorod"
            initial_response = self.session.get(start_url, allow_redirects=False)
            
            if initial_response.status_code not in [301, 302, 303, 307, 308]:
                raise AuthenticationError(f"Ожидался редирект, получен {initial_response.status_code}")
            
            # 2. Следуем за редиректом
            redirect_path = initial_response.headers.get('Location', '')
            redirect_url = urljoin(self.base_url, redirect_path)
            final_response = self.session.get(redirect_url, allow_redirects=True)
            
            # 3. Извлекаем CSRF токен
            self._csrf_token = self._extract_csrf_token(final_response.text)
            if not self._csrf_token:
                raise AuthenticationError("CSRF токен не найден на странице входа")
            
            # 4. Отправляем данные для входа
            post_url = final_response.url
            login_data = {
                '__RequestVerificationToken': self._csrf_token,
                'Email': credentials.email,
                'Password': credentials.password
            }
            
            login_response = self.session.post(post_url, data=login_data)
            
            # 5. Проверяем успешность входа
            if login_response.status_code in [301, 302]:
                self._is_authenticated = True
                return True
            elif login_response.status_code == 200:
                if 'inputEmail3' not in login_response.text:
                    self._is_authenticated = True
                    return True
                else:
                    raise AuthenticationError("Неверные учетные данные")
            
            return False
            
        except requests.RequestException as e:
            raise AuthenticationError(f"Ошибка сети: {str(e)}")
            
    def get_meter_readings(self, force_refresh: bool = False) -> List[MeterReading]:
        """Получение списка счетчиков с их последними показаниями"""
        try:
            counters_url = f"{self.base_url}/gorod/Abonent/Counters"
            response = self.session.get(counters_url)
            
            if response.status_code != 200:
                raise ParseError(f"Не удалось получить страницу счетчиков: {response.status_code}")
            
            return self._parse_meters_page(response.text)
            
        except Exception as e:
            raise ParseError(f"Ошибка парсинга данных счетчиков: {str(e)}")
    
    def submit_meter_readings(self, readings: Dict[str, str]) -> bool:
        """
        Отправка новых показаний счетчиков
        
        Args:
            readings: Словарь {meter_reading_id: value}
            
        Returns:
            bool: True если отправка успешна
        """
        try:
            # 1. Получаем текущие данные страницы (для получения актуального токена)
            current_readings = self.get_meter_readings()
            
            # 2. Подготавливаем данные для отправки
            submit_data = self._prepare_submission_data(current_readings, readings)
            
            # 3. Отправляем POST-запрос
            submit_url = f"{self.base_url}/gorod/Abonent/Counters"
            response = self.session.post(submit_url, data=submit_data)
            
            # 4. Проверяем успешность
            if response.status_code != 200:
                raise SubmissionError(f"Ошибка отправки: {response.status_code}")
            
            return True
            
        except Exception as e:
            raise SubmissionError(f"Ошибка отправки показаний: {str(e)}")
    
    def validate_submitted_readings(self, expected_readings: Dict[str, str]) -> Dict[str, bool]:
        """
        Валидация отправленных показаний
        
        Args:
            expected_readings: Ожидаемые показания {meter_reading_id: value}
            
        Returns:
            Dict: Результаты валидации {meter_reading_id: is_valid}
        """
        try:
            # Получаем актуальные данные после отправки
            actual_readings = self.get_meter_readings()
            
            validation_results = {}
            
            for meter_id, expected_value in expected_readings.items():
                # Находим соответствующий счетчик
                meter = next((m for m in actual_readings if m.meter_reading_id == meter_id), None)
                
                if meter:
                    actual_value = meter.current_reading.value
                    # Сравниваем значения (учитываем возможные форматы)
                    validation_results[meter_id] = self._compare_values(
                        expected_value, 
                        actual_value
                    )
                else:
                    validation_results[meter_id] = False
            
            return validation_results
            
        except Exception as e:
            raise ParseError(f"Ошибка валидации: {str(e)}")
    
    def export_readings_to_json(self, readings: List[MeterReading], 
                               filename: str = None) -> str:
        """Экспорт данных в JSON формат"""
        export_data = {
            'metadata': {
                'export_date': datetime.now().isoformat(),
                'source': self.base_url,
                'total_records': len(readings)
            },
            'meter_readings': [r.to_dict() for r in readings]
        }
        
        json_str = json.dumps(export_data, ensure_ascii=False, indent=2)
        
        if filename:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(json_str)
        
        return json_str
    
    def _extract_csrf_token(self, html: str) -> Optional[str]:
        """Извлечение CSRF токена из HTML"""
        soup = BeautifulSoup(html, 'html.parser')
        
        # Пробуем несколько возможных имен токена
        token_names = ['__RequestVerificationToken', 'RequestVerificationToken']
        
        for name in token_names:
            token_input = soup.find('input', {'name': name})
            if token_input and token_input.get('value'):
                return token_input['value']
        
        return None
    
    def _parse_meters_page(self, html: str) -> List[MeterReading]:
        """Парсинг страницы со счетчиками"""
        from .parsers import parse_meters_page
        return parse_meters_page(html, self.base_url)
    
    def _prepare_submission_data(self, current_readings: List[MeterReading], 
                               new_readings: Dict[str, str]) -> List[tuple]:
        """Подготовка данных для отправки"""
        # Сначала получаем актуальный CSRF токен
        if not self._csrf_token:
            raise SubmissionError("CSRF токен не найден")
        
        # Получаем текущие значения форм
        form_data = self._get_form_data(current_readings)
        
        # Обновляем значения для счетчиков из new_readings
        for meter in current_readings:
            if meter.meter_reading_id in new_readings:
                # Обновляем значение в форме
                self._update_form_value(form_data, meter, new_readings[meter.meter_reading_id])
        
        return form_data
    
    def _get_form_data(self, readings: List[MeterReading]) -> List[tuple]:
        """Получение данных формы из текущих показаний"""
        # Этот метод должен собирать все поля формы
        # включая скрытые поля и значения селектов
        form_data = [
            ('__RequestVerificationToken', self._csrf_token),
            # Добавить другие поля формы при необходимости
        ]
        
        # Добавляем данные по каждому счетчику
        for meter in readings:
            form_data.append(('MeterReadingId', meter.meter_reading_id))
            form_data.append(('InputValCnt', meter.current_reading.value or ''))
        
        return form_data
    
    def _update_form_value(self, form_data: List[tuple], meter: MeterReading, 
                          new_value: str) -> None:
        """Обновление значения в данных формы"""
        # Находим и обновляем значение для конкретного счетчика
        for i, (field_name, field_value) in enumerate(form_data):
            if field_name == 'InputValCnt' and field_value == meter.current_reading.value:
                form_data[i] = (field_name, new_value)
                break
    
    def _compare_values(self, expected: str, actual: str) -> bool:
        """Сравнение значений с учетом различных форматов"""
        # Нормализуем значения (убираем лишние пробелы, приводим к одному формату)
        expected_norm = expected.strip().replace(',', '.')
        actual_norm = actual.strip().replace(',', '.')
        
        try:
            # Пробуем сравнить как числа
            expected_float = float(expected_norm)
            actual_float = float(actual_norm)
            
            # Сравниваем с небольшой погрешностью
            return abs(expected_float - actual_float) < 0.01
        except ValueError:
            # Если не числа, сравниваем как строки
            return expected_norm == actual_norm
    
    @property
    def is_authenticated(self) -> bool:
        """Проверка статуса аутентификации"""
        return self._is_authenticated
    
    def logout(self):
        """Завершение сессии"""
        self.session.close()
        self._is_authenticated = False
        self._csrf_token = None
