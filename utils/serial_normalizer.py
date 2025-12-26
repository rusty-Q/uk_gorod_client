def normalize_serial_number(serial: str) -> str:
    """Нормализация серийного номера (удаление лидирующих нулей)"""
    if not serial:
        return ""
    
    serial = str(serial).strip()
    
    # Если номер состоит только из нулей
    if serial and all(c == '0' for c in serial):
        return "0"
    
    return serial.lstrip('0') or "0"

def match_meters_by_serial(uk_meters: List, external_meters: List[Dict], 
                          serial_key: str = 'sn') -> Dict:
    """
    Сопоставление счетчиков по серийным номерам
    
    Args:
        uk_meters: Список счетчиков из УК Город
        external_meters: Список счетчиков из внешней системы
        serial_key: Ключ для серийного номера во внешней системе
        
    Returns:
        Dict: Сопоставленные данные {meter_reading_id: external_data}
    """
    matches = {}
    
    for uk_meter in uk_meters:
        uk_serial_normalized = uk_meter.serial_normalized
        
        for ext_meter in external_meters:
            ext_serial = str(ext_meter.get(serial_key, '')).strip()
            ext_serial_normalized = normalize_serial_number(ext_serial)
            
            if uk_serial_normalized == ext_serial_normalized:
                matches[uk_meter.meter_reading_id] = ext_meter
                break
    
    return matches
