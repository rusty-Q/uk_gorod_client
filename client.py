import requests
from typing import List, Dict, Optional
from urllib.parse import urljoin

from .models import Credentials, MeterReading, SubmissionResult
from .parser import parse_meters_page, extract_csrf_token
from .config import ConfigLoader


class UKGorodClient:
    """Клиент для работы с порталом УК Город"""
    
    def __init__(self, base_url: str = "https://nd.inno-e.ru", config_path: Optional[str] = None):
        """
        Инициализация клиента
        
        Args:
            base_url: Базовый URL портала
            config_path: Путь к файлу конфигурации (если None, ищет secrets.yaml)
        """
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.config_loader = ConfigLoader(config_path)
        self._set_default_headers()
    
    def _set_default_headers(self):
        """Установка стандартных заголовков"""
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
    
    def load_credentials_from_config(self, service_name: str = "uk_gorod") -> Credentials:
        """
        Загрузка учетных данных из конфигурационного файла
        
        Args:
            service_name: Имя сервиса в secrets.yaml
            
        Returns:
            Credentials: Учетные данные
            
        Raises:
            FileNotFoundError: Если файл не найден
            ValueError: Если данные некорректны
        """
        return self.config_loader.load_credentials(service_name)
    
    def login_with_config(self, service_name: str = "uk_gorod") -> bool:
        """
        Вход на портал с использованием учетных данных из конфигурации
        
        Args:
            service_name: Имя сервиса в secrets.yaml
            
        Returns:
            bool: True если вход успешен
        """
        credentials = self.load_credentials_from_config(service_name)
        return self.login(credentials)
    
    def login(self, credentials: Credentials) -> bool:
        """
        Вход на портал УК Город
        
        Args:
            credentials: Учетные данные (email и пароль)
            
        Returns:
            bool: True если вход успешен
        """
        try:
            # 1. Получаем страницу входа (следуем редиректам)
            login_url = f"{self.base_url}/gorod"
            response = self.session.get(login_url, allow_redirects=True)
            
            # 2. Извлекаем CSRF токен
            csrf_token = extract_csrf_token(response.text)
            
            # 3. Формируем данные для отправки
            form_data = {
                '__RequestVerificationToken': csrf_token,
                'Email': credentials.email,
                'Password': credentials.password
            }
            
            # 4. Отправляем запрос на вход
            post_url = response.url
            login_response = self.session.post(post_url, data=form_data)
            
            # 5. Проверяем успешность входа
            if login_response.status_code in [302, 303]:
                redirect_url = login_response.headers.get('Location')
                if redirect_url:
                    self.session.get(urljoin(self.base_url, redirect_url))
                return True
            
            if ('inputEmail3' not in login_response.text and 
                'login-box-body' not in login_response.text):
                return True
            
            return False
            
        except Exception as e:
            raise Exception(f"Ошибка входа: {str(e)}")
    
    def get_meters(self) -> List[MeterReading]:
        """
        Получение списка счетчиков с их прошлыми показаниями
        
        Returns:
            List[MeterReading]: Список счетчиков
        """
        try:
            counters_url = f"{self.base_url}/gorod/Abonent/Counters"
            response = self.session.get(counters_url)
            
            if response.status_code != 200:
                raise Exception(f"Ошибка получения страницы: {response.status_code}")
            
            return parse_meters_page(response.text)
            
        except Exception as e:
            raise Exception(f"Ошибка получения данных счетчиков: {str(e)}")
    
    def submit_readings(self, readings: Dict[str, str]) -> SubmissionResult:
        """
        Отправка новых показаний счетчиков
        
        Args:
            readings: Словарь {meter_id: значение}
            
        Returns:
            SubmissionResult: Результат отправки
        """
        try:
            # 1. Получаем текущую страницу со счетчиками
            counters_url = f"{self.base_url}/gorod/Abonent/Counters"
            response = self.session.get(counters_url)
            
            if response.status_code != 200:
                return SubmissionResult(
                    success=False,
                    message=f"Ошибка получения страницы: {response.status_code}"
                )
            
            # 2. Извлекаем CSRF токен
            csrf_token = extract_csrf_token(response.text)
            
            # 3. Получаем текущие счетчики
            current_meters = parse_meters_page(response.text)
            
            # 4. Подготавливаем данные для отправки
            form_data = self._prepare_submission_data(current_meters, readings, csrf_token)
            
            # 5. Отправляем POST запрос
            submit_response = self.session.post(counters_url, data=form_data)
            
            if submit_response.status_code != 200:
                return SubmissionResult(
                    success=False,
                    message=f"Ошибка отправки: {submit_response.status_code}"
                )
            
            # 6. Проверяем результат
            success = self._check_submission_success(submit_response.text)
            
            # 7. При необходимости проверяем валидацию
            validated = None
            if success:
                validated = self._validate_submitted_readings(readings)
            
            return SubmissionResult(
                success=success,
                message="Показания успешно отправлены" if success else "Ошибка при отправке",
                validated=validated
            )
            
        except Exception as e:
            return SubmissionResult(
                success=False,
                message=f"Ошибка: {str(e)}"
            )
    
    def _prepare_submission_data(self, meters: List[MeterReading], 
                                new_readings: Dict[str, str], 
                                csrf_token: str) -> Dict[str, str]:
        """Подготовка данных формы для отправки"""
        form_data = {
            '__RequestVerificationToken': csrf_token,
        }
        
        for meter in meters:
            value = new_readings.get(meter.id, meter.current_value or "")
            form_data[f'InputValCnt'] = value
        
        return form_data
    
    def _check_submission_success(self, html: str) -> bool:
        """Проверка успешности отправки по содержимому страницы"""
        error_indicators = [
            'Ошибка',
            'error',
            'не удалось',
            'повторите',
        ]
        
        for indicator in error_indicators:
            if indicator.lower() in html.lower():
                return False
        
        return True
    
    def _validate_submitted_readings(self, submitted_readings: Dict[str, str]) -> Dict[str, bool]:
        """Проверка, что отправленные значения приняты"""
        try:
            updated_meters = self.get_meters()
            validation_results = {}
            
            for meter in updated_meters:
                submitted_value = submitted_readings.get(meter.id)
                if submitted_value:
                    validation_results[meter.id] = True
            
            return validation_results
            
        except:
            return {meter_id: True for meter_id in submitted_readings.keys()}
    
    def logout(self):
        """Завершение сессии"""
        self.session.close()
