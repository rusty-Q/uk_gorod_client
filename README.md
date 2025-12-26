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
from uk_gorod import UKGorodClient, Credentials, format_meter_readings

def main():
    # Создаем клиент
    client = UKGorodClient(base_url="https://nd.inno-e.ru")
    
    # Учетные данные
    credentials = Credentials(
        email="ваш_email@mail.ru",
        password="ваш_пароль"
    )
    
    try:
        # 1. Вход на портал
        print("Вход на портал УК Город...")
        if not client.login(credentials):
            print("Ошибка входа. Проверьте учетные данные.")
            return
        
        print("Успешный вход")
        
        # 2. Получение списка счетчиков
        print("\nПолучение данных счетчиков...")
        meters = client.get_meters()
        
        if not meters:
            print("Счетчики не найдены")
            return
        
        # Выводим информацию о счетчиках
        print(format_meter_readings(meters))
        
        # 3. Пример отправки показаний (опционально)
        # Собираем данные для отправки
        readings_to_submit = {}
        
        for meter in meters:
            if meter.service == "Электроснабжение":
                # Например, новое показание для электроснабжения
                readings_to_submit[meter.id] = "1234.56"
            elif meter.service == "Холодная вода":
                readings_to_submit[meter.id] = "567.89"
        
        if readings_to_submit:
            print(f"\nОтправка {len(readings_to_submit)} показаний...")
            
            result = client.submit_readings(readings_to_submit)
            
            if result.success:
                print(f"{result.message}")
                if result.validated:
                    valid_count = sum(result.validated.values())
                    print(f" Проверено: {valid_count}/{len(result.validated)}")
            else:
                print(f"{result.message}")
        
        # 4. Выход (опционально)
        client.logout()
        print("\nСессия завершена")
        
    except Exception as e:
        print(f"Ошибка: {str(e)}")

if __name__ == "__main__":
    main()
```
