def normalize_serial_number(serial: str) -> str:
    """Нормализация серийного номера (удаление лидирующих нулей)"""
    if not serial:
        return ""
    
    serial = str(serial).strip()
    
    # Если все символы - нули
    if serial and all(c == '0' for c in serial):
        return "0"
    
    # Удаляем лидирующие нули
    return serial.lstrip('0') or "0"


def compare_serial_numbers(serial1: str, serial2: str) -> bool:
    """Сравнение серийных номеров с учетом лидирующих нулей"""
    return normalize_serial_number(serial1) == normalize_serial_number(serial2)


def format_meter_readings(meters: list) -> str:
    """Форматирование списка счетчиков для вывода"""
    lines = []
    lines.append("=" * 60)
    lines.append("СПИСОК СЧЕТЧИКОВ")
    lines.append("=" * 60)
    
    for i, meter in enumerate(meters, 1):
        lines.append(f"{i}. {meter.service}")
        lines.append(f"   Серийный номер: {meter.serial_number}")
        lines.append(f"   ID счетчика: {meter.id}")
        lines.append(f"   Последнее показание: {meter.last_reading_value} ({meter.last_reading_date})")
        if meter.current_value:
            lines.append(f"   Текущее значение: {meter.current_value}")
        lines.append(f"   Следующая поверка: {meter.next_verification}")
        lines.append("")
    
    lines.append(f"Всего: {len(meters)} счетчиков")
    return "\n".join(lines)
