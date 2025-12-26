def normalize_serial_number(serial: str) -> str:
    if not serial:
        return ""
    
    serial = str(serial).strip()
    
    if serial and all(c == '0' for c in serial):
        return "0"
    
    return serial.lstrip('0') or "0"


def compare_serial_numbers(serial1: str, serial2: str) -> bool:
    return normalize_serial_number(serial1) == normalize_serial_number(serial2)


def format_meter_readings(meters: list) -> str:
    lines = []
    lines.append("=" * 60)
    lines.append("METER READINGS")
    lines.append("=" * 60)
    
    for i, meter in enumerate(meters, 1):
        lines.append(f"{i}. {meter.service}")
        lines.append(f"   Serial: {meter.serial_number}")
        lines.append(f"   ID: {meter.id}")
        lines.append(f"   Last reading: {meter.last_reading_value} ({meter.last_reading_date})")
        if meter.current_value:
            lines.append(f"   Current value: {meter.current_value}")
        lines.append(f"   Next verification: {meter.next_verification}")
        lines.append("")
    
    lines.append(f"Total: {len(meters)} meters")
    return "\n".join(lines)
