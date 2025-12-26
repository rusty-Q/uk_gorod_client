from dataclasses import dataclass, field
from typing import Optional, Dict, List, Any
from datetime import datetime

@dataclass
class LoginCredentials:
    """Учетные данные для входа"""
    email: str
    password: str

@dataclass
class LastReading:
    """Последнее показание счетчика"""
    date: str
    value: str

@dataclass
class CurrentReading:
    """Текущее показание"""
    value: Optional[str] = None
    source: str = "uk_gorod"
    date: Optional[str] = None
    input_field_name: str = "InputValCnt"
    is_editable: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            'value': self.value,
            'source': self.source,
            'date': self.date,
            'input_field_name': self.input_field_name,
            'is_editable': self.is_editable,
            'metadata': self.metadata
        }

@dataclass
class MeterReading:
    """Данные счетчика"""
    meter_reading_id: str
    service: str
    serial_number: str
    serial_normalized: str
    next_verification_date: Optional[str] = None
    last_reading: Optional[LastReading] = None
    current_reading: CurrentReading = field(default_factory=CurrentReading)
    askue_link: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def update_from_external(self, external_data: Dict[str, Any]) -> None:
        """Обновление данных из внешнего источника"""
        if 'value' in external_data:
            self.current_reading.value = str(external_data['value'])
            self.current_reading.source = external_data.get('source', 'external')
            
        if 'metadata' in external_data:
            self.metadata.update(external_data['metadata'])
    
    def to_dict(self) -> Dict:
        return {
            'meter_reading_id': self.meter_reading_id,
            'service': self.service,
            'serial_number': self.serial_number,
            'serial_normalized': self.serial_normalized,
            'next_verification_date': self.next_verification_date,
            'last_reading': {
                'date': self.last_reading.date if self.last_reading else None,
                'value': self.last_reading.value if self.last_reading else None
            } if self.last_reading else None,
            'current_reading': self.current_reading.to_dict(),
            'askue_link': self.askue_link,
            'metadata': self.metadata
        }
    
    @classmethod
    def from_html_data(cls, meter_id: str, service: str, serial_number: str, 
                      serial_normalized: str, **kwargs):
        """Создание объекта из данных HTML"""
        return cls(
            meter_reading_id=meter_id,
            service=service,
            serial_number=serial_number,
            serial_normalized=serial_normalized,
            next_verification_date=kwargs.get('next_verification_date'),
            last_reading=LastReading(
                date=kwargs.get('last_reading_date', ''),
                value=kwargs.get('last_reading_value', '')
            ) if kwargs.get('last_reading_date') else None,
            current_reading=CurrentReading(
                value=kwargs.get('current_value', ''),
                date=kwargs.get('current_reading_date'),
                input_field_name='InputValCnt'
            ),
            askue_link=kwargs.get('askue_link')
        )
