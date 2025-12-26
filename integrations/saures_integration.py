import requests
from typing import Dict, List, Optional
from ..models import MeterReading
from ..utils.serial_normalizer import normalize_serial_number

class SauresIntegration:
    """Интеграция с Saures API"""
    
    def __init__(self, api_base: str = "https://api.saures.ru/1.0"):
        self.api_base = api_base
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.sid = None
    
    def authenticate(self, email: str, password: str) -> bool:
        """Аутентификация в Saures API"""
        try:
            login_url = f"{self.api_base}/login"
            response = self.session.post(login_url, data={
                'email': email,
                'password': password
            })
            
            if response.status_code != 200:
                return False
            
            data = response.json()
            if data.get('status') != 'ok':
                return False
            
            self.sid = data['data']['sid']
            return True
            
        except Exception:
            return False
    
    def get_object_meters(self, object_id: int) -> List[Dict]:
        """Получение счетчиков для объекта"""
        try:
            meters_url = f"{self.api_base}/object/meters"
            response = self.session.get(meters_url, params={
                'sid': self.sid,
                'id': object_id
            })
            
            if response.status_code != 200:
                return []
            
            data = response.json()
            if data.get('status') != 'ok':
                return []
            
            # Собираем все счетчики в плоский список
            all_meters = []
            sensors = data['data']['sensors']
            
            for sensor in sensors:
                for meter in sensor.get('meters', []):
                    meter_data = {
                        'meter_id': meter['meter_id'],
                        'serial_number': meter.get('sn', ''),
                        'serial_normalized': normalize_serial_number(meter.get('sn', '')),
                        'meter_name': meter.get('meter_name', ''),
                        'type': meter['type'],
                        'values': meter['vals'],
                        'unit': meter['unit'],
                        'state': meter['state'],
                        'sensor_name': sensor.get('name', '')
                    }
                    all_meters.append(meter_data)
            
            return all_meters
            
        except Exception:
            return []
    
    def enrich_uk_meters(self, uk_meters: List[MeterReading], 
                        saures_meters: List[Dict]) -> List[MeterReading]:
        """Обогащение данных УК Город данными из Saures"""
        for uk_meter in uk_meters:
            for saures_meter in saures_meters:
                if uk_meter.serial_normalized == saures_meter['serial_normalized']:
                    values = saures_meter['values']
                    type_number = saures_meter['type']['number']
                    
                    if type_number == 8 and len(values) >= 3:  # Электричество
                        total = sum(values)
                        uk_meter.current_reading.value = f"{total:.2f}"
                        uk_meter.current_reading.metadata['tariffs'] = {
                            'T1': f"{values[0]:.2f}",
                            'T2': f"{values[1]:.2f}",
                            'T3': f"{values[2]:.2f}"
                        }
                    elif values:
                        uk_meter.current_reading.value = f"{values[-1]:.2f}"
                    
                    uk_meter.current_reading.source = 'saures'
                    uk_meter.metadata.update({
                        'saures_meter_id': saures_meter['meter_id'],
                        'saures_type': saures_meter['type']['name'],
                        'saures_unit': saures_meter['unit'],
                        'saures_state': saures_meter['state']['name']
                    })
                    break
        
        return uk_meters
