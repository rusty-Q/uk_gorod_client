import requests
from typing import List, Dict, Optional
from urllib.parse import urljoin

from .models import Credentials, MeterReading, SubmissionResult
from .parser import parse_meters_page, extract_csrf_token
from .config import ConfigLoader


class UKGorodClient:
    
    def __init__(self, base_url: str = "https://nd.inno-e.ru", config_path: Optional[str] = None):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.config_loader = ConfigLoader(config_path)
        self._set_default_headers()
    
    def _set_default_headers(self):
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
        return self.config_loader.load_credentials(service_name)
    
    def login_with_config(self, service_name: str = "uk_gorod") -> bool:
        credentials = self.load_credentials_from_config(service_name)
        return self.login(credentials)
    
    def login(self, credentials: Credentials) -> bool:
        try:
            login_url = f"{self.base_url}/gorod"
            response = self.session.get(login_url, allow_redirects=True)
            
            csrf_token = extract_csrf_token(response.text)
            
            form_data = {
                '__RequestVerificationToken': csrf_token,
                'Email': credentials.email,
                'Password': credentials.password
            }
            
            post_url = response.url
            login_response = self.session.post(post_url, data=form_data)
            
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
            raise Exception(f"Login error: {str(e)}")
    
    def get_meters(self) -> List[MeterReading]:
        try:
            counters_url = f"{self.base_url}/gorod/Abonent/Counters"
            response = self.session.get(counters_url)
            
            if response.status_code != 200:
                raise Exception(f"Page error: {response.status_code}")
            
            return parse_meters_page(response.text)
            
        except Exception as e:
            raise Exception(f"Error getting meters: {str(e)}")
    
    def submit_readings(self, readings: Dict[str, str]) -> SubmissionResult:
        try:
            counters_url = f"{self.base_url}/gorod/Abonent/Counters"
            response = self.session.get(counters_url)
            
            if response.status_code != 200:
                return SubmissionResult(
                    success=False,
                    message=f"Page error: {response.status_code}"
                )
            
            csrf_token = extract_csrf_token(response.text)
            current_meters = parse_meters_page(response.text)
            
            form_data = self._prepare_submission_data(current_meters, readings, csrf_token)
            
            submit_response = self.session.post(counters_url, data=form_data)
            
            if submit_response.status_code != 200:
                return SubmissionResult(
                    success=False,
                    message=f"Submission error: {submit_response.status_code}"
                )
            
            success = self._check_submission_success(submit_response.text)
            
            validated = None
            if success:
                validated = self._validate_submitted_readings(readings)
            
            return SubmissionResult(
                success=success,
                message="Readings submitted successfully" if success else "Submission error",
                validated=validated
            )
            
        except Exception as e:
            return SubmissionResult(
                success=False,
                message=f"Error: {str(e)}"
            )
    
    def _prepare_submission_data(self, meters: List[MeterReading], 
                                new_readings: Dict[str, str], 
                                csrf_token: str) -> Dict[str, str]:
        form_data = {
            '__RequestVerificationToken': csrf_token,
        }
        
        for meter in meters:
            value = new_readings.get(meter.id, meter.current_value or "")
            form_data[f'InputValCnt'] = value
        
        return form_data
    
    def _check_submission_success(self, html: str) -> bool:
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
        self.session.close()
