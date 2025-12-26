from bs4 import BeautifulSoup
from typing import List
from .models import MeterReading
from .utils.serial_normalizer import normalize_serial_number

def parse_meters_page(html: str, base_url: str) -> List[MeterReading]:
    """Парсинг страницы со счетчиками"""
    soup = BeautifulSoup(html, 'html.parser')
    meter_reading_inputs = soup.find_all('input', {'name': 'MeterReadingId'})
    
    readings = []
    
    for idx, input_tag in enumerate(meter_reading_inputs, 1):
        meter_id = input_tag.get('value', '').strip()
        if not meter_id:
            continue
        
        parent_row = input_tag.find_parent('tr')
        if not parent_row:
            continue
        
        cells = parent_row.find_all('td')
        if len(cells) >= 9:
            service = cells[0].get_text(strip=True)
            serial_raw = cells[1].get_text(strip=True)
            serial_normalized = normalize_serial_number(serial_raw)
            
            current_value_input = parent_row.find('input', {'name': 'InputValCnt'})
            current_value = current_value_input.get('value', '') if current_value_input else ''
            
            reading = MeterReading.from_html_data(
                meter_id=meter_id,
                service=service,
                serial_number=serial_raw,
                serial_normalized=serial_normalized,
                next_verification_date=cells[2].get_text(strip=True),
                last_reading_date=cells[3].get_text(strip=True),
                last_reading_value=cells[4].get_text(strip=True),
                current_reading_date=cells[5].get_text(strip=True),
                current_value=current_value,
                askue_link=f"{base_url}/gorod/Abonent/GetIndication/{meter_id}"
            )
            
            readings.append(reading)
    
    return readings

def extract_form_data(html: str) -> Dict[str, str]:
    """Извлечение данных формы со страницы"""
    soup = BeautifulSoup(html, 'html.parser')
    
    form_data = {}
    
    # CSRF токен
    token_input = soup.find('input', {'name': '__RequestVerificationToken'})
    if token_input and token_input.get('value'):
        form_data['csrf_token'] = token_input['value']
    
    # Значения селектов
    calculation_select = soup.find('select', {'id': 'CalculationDateSelectList'})
    if calculation_select:
        selected_option = calculation_select.find('option', selected=True)
        if selected_option:
            form_data['calculation_date'] = selected_option.get('value', '')
    
    account_select = soup.find('select', {'id': 'AllPersonalAccountsOfUser'})
    if account_select:
        selected_option = account_select.find('option', selected=True)
        if selected_option:
            form_data['personal_account'] = selected_option.get('value', '')
    
    return form_data
