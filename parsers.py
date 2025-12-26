from bs4 import BeautifulSoup
from typing import List
from .models import MeterReading

def parse_meters_page(html: str) -> List[MeterReading]:
    soup = BeautifulSoup(html, 'html.parser')
    readings = []
    
    meter_inputs = soup.find_all('input', {'name': 'MeterReadingId'})
    
    for meter_input in meter_inputs:
        meter_id = meter_input.get('value', '').strip()
        if not meter_id:
            continue
        
        row = meter_input.find_parent('tr')
        if not row:
            continue
        
        cells = row.find_all('td')
        if len(cells) < 7:
            continue
        
        service = cells[0].get_text(strip=True)
        serial_number = cells[1].get_text(strip=True)
        next_verification = cells[2].get_text(strip=True)
        last_reading_date = cells[3].get_text(strip=True)
        last_reading_value = cells[4].get_text(strip=True)
        
        input_field = row.find('input', {'name': 'InputValCnt'})
        current_value = input_field.get('value', '').strip() if input_field else None
        
        reading = MeterReading(
            id=meter_id,
            service=service,
            serial_number=serial_number,
            last_reading_date=last_reading_date,
            last_reading_value=last_reading_value,
            next_verification=next_verification,
            current_value=current_value
        )
        
        readings.append(reading)
    
    return readings


def extract_csrf_token(html: str) -> str:
    soup = BeautifulSoup(html, 'html.parser')
    
    token_names = ['__RequestVerificationToken', 'RequestVerificationToken']
    
    for name in token_names:
        token_input = soup.find('input', {'name': name})
        if token_input and token_input.get('value'):
            return token_input['value']
    
    raise ValueError("CSRF token not found")
