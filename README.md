# Неофициальный клиент портала управляющей компании "Город" г. Казань
Специализированная библиотека для работы с порталом УК "Город" (Казань), которая позволит легко интегрировать различные источники данных.

# Установка
```bash
git clone https://github.com/rusty-Q/uk_gorod_client
cd uk-gorod-client
pip install -e .
```
# Использование
``` python
import os
from uk_gorod import UKGorodClient

def main():
    config_path = os.path.join(os.path.dirname(__file__), 'secrets.yaml')
    
    client = UKGorodClient(base_url="https://nd.inno-e.ru", config_path=config_path)
    
    try:
        print("Logging in to UK Gorod...")
        
        try:
            if not client.login_with_config(service_name="uk_gorod"):
                print("Login failed. Check credentials in secrets.yaml")
                return
        except FileNotFoundError as e:
            print(f"Config error: {e}")
            print("\nCreate secrets.yaml with structure:")
            print("services:")
            print("  - name: uk_gorod")
            print("    login: your_email@mail.ru")
            print("    password: your_password")
            return
        
        print("Login successful")
        
        print("\nGetting meter data...")
        meters = client.get_meters()
        
        if not meters:
            print("No meters found")
            return
        
        print(f"Found {len(meters)} meters")
        
        for i, meter in enumerate(meters, 1):
            print(f"\n{i}. {meter.service}")
            print(f"   ID: {meter.id}")
            print(f"   Serial: {meter.serial_number}")
            print(f"   Last: {meter.last_reading_value} ({meter.last_reading_date})")
            if meter.current_value:
                print(f"   Current: {meter.current_value}")
        
        client.logout()
        print("\nSession closed")
        
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()
```
