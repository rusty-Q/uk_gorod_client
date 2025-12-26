from bs4 import BeautifulSoup
from typing import List
from .models import MeterReading

def parse_meters_page(html: str) -> List[MeterReading]:
    """Парсинг страницы со счетчиками и их прошлыми показаниями"""
    soup = BeautifulSoup(html, 'html.parser')
    readings = []
    
    # Ищем все скрытые поля с MeterReadingId
    meter_inputs = soup.find_all('input', {'name': 'MeterReadingId'})
    
    for meter_input in meter_inputs:
        meter_id = meter_input.get('value', '').strip()
        if not meter_id:
            continue
        
        # Находим родительскую строку таблицы
        row = meter_input.find_parent('tr')
        if not row:
            continue
        
        # Извлекаем данные из ячеек таблицы
        cells = row.find_all('td')
        if len(cells) < 7:  # Минимум 7 ячеек нужно
            continue
        
        # Извлекаем данные из ячеек
        service = cells[0].get_text(strip=True)
        serial_number = cells[1].get_text(strip=True)
        next_verification = cells[2].get_text(strip=True)
        last_reading_date = cells[3].get_text(strip=True)
        last_reading_value = cells[4].get_text(strip=True)
        
        # Ищем поле для ввода текущего значения
        input_field = row.find('input', {'name': 'InputValCnt'})
        current_value = input_field.get('value', '').strip() if input_field else None
        
        # Создаем объект счетчика
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
    """Извлечение CSRF токена из страницы"""
    soup = BeautifulSoup(html, 'html.parser')
    
    # Пробуем найти токен по разным возможным именам
    token_names = ['__RequestVerificationToken', 'RequestVerificationToken']
    
    for name in token_names:
        token_input = soup.find('input', {'name': name})
        if token_input and token_input.get('value'):
            return token_input['value']
    
    raise ValueError("CSRF токен не найден на странице")


def extract_form_data(html: str) -> dict:
    """Извлечение всех данных формы для отправки"""
    soup = BeautifulSoup(html, 'html.parser')
    form_data = {}
    
    # CSRF токен
    form_data['csrf_token'] = extract_csrf_token(html)
    
    # Находим форму
    form = soup.find('form')
    if form and form.get('action'):
        form_data['action'] = form['action']
    
    return form_data
