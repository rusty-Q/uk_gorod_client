# uk_gorod_client
Специализированная библиотека для работы с порталом УК "Город" (Казань), которая позволит легко интегрировать различные источники данных.

# Установка
git clone https://github.com/yourusername/uk-gorod-client
cd uk-gorod-client
pip install -e .

# использование
``` bash
#!/usr/bin/env python
import yaml
import json
from uk_gorod_client import UKGorodClient, LoginCredentials, SauresIntegration
from uk_gorod_client.utils.serial_normalizer import match_meters_by_serial

def main():
    # Загрузка конфигурации
    with open('secrets.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    uk_credentials = LoginCredentials(
        email=config['uk_gorod']['login'],
        password=config['uk_gorod']['password']
    )
    
    # Создаем клиент УК Город
    uk_client = UKGorodClient(base_url="https://nd.inno-e.ru")
    
    try:
        # 1. Аутентификация
        if not uk_client.login(uk_credentials):
            print("❌ Ошибка аутентификации в УК Город")
            return
        
        print("✅ Успешная аутентификация в УК Город")
        
        # 2. Получение данных счетчиков
        print("\n📊 Получение данных счетчиков...")
        uk_meters = uk_client.get_meter_readings()
        print(f"✅ Получено счетчиков: {len(uk_meters)}")
        
        # 3. Интеграция с Saures (опционально)
        saures_integration = SauresIntegration()
        
        if saures_integration.authenticate(
            config['saures']['login'],
            config['saures']['password']
        ):
            print("\n📡 Получение данных из Saures...")
            # Предполагаем, что есть только один объект
            saures_meters = saures_integration.get_object_meters(object_id=1)
            
            if saures_meters:
                print(f"✅ Получено счетчиков из Saures: {len(saures_meters)}")
                
                # Обогащаем данные УК Город
                enriched_meters = saures_integration.enrich_uk_meters(uk_meters, saures_meters)
                
                # Считаем сколько счетчиков было обновлено
                updated = sum(1 for m in enriched_meters if m.current_reading.source == 'saures')
                print(f"🔄 Обновлено показаний из Saures: {updated}/{len(enriched_meters)}")
                
                uk_meters = enriched_meters
        
        # 4. Подготовка данных для отправки
        # Здесь можно добавить логику для сбора актуальных данных из других источников
        readings_to_submit = {}
        
        for meter in uk_meters:
            if meter.current_reading.value and meter.current_reading.value != '0':
                readings_to_submit[meter.meter_reading_id] = meter.current_reading.value
        
        # 5. Отправка показаний (опционально)
        if readings_to_submit:
            print(f"\n📤 Отправка {len(readings_to_submit)} показаний...")
            
            try:
                if uk_client.submit_meter_readings(readings_to_submit):
                    print("✅ Показания успешно отправлены")
                    
                    # 6. Валидация отправленных данных
                    print("\n🔍 Валидация отправленных данных...")
                    validation_results = uk_client.validate_submitted_readings(readings_to_submit)
                    
                    valid_count = sum(validation_results.values())
                    print(f"✅ Корректно отправлено: {valid_count}/{len(validation_results)}")
                    
                    for meter_id, is_valid in validation_results.items():
                        if not is_valid:
                            print(f"⚠️  Ошибка валидации для счетчика {meter_id}")
                else:
                    print("❌ Ошибка отправки показаний")
            except Exception as e:
                print(f"❌ Ошибка при отправке: {str(e)}")
        
        # 7. Экспорт данных в JSON
        print("\n💾 Экспорт данных...")
        json_data = uk_client.export_readings_to_json(uk_meters, 'meter_readings.json')
        print("✅ Данные экспортированы в meter_readings.json")
        
        # 8. Вывод сводки
        print(f"\n📊 Сводка:")
        print(f"   Всего счетчиков: {len(uk_meters)}")
        print(f"   С актуальными данными: {len(readings_to_submit)}")
        
    except Exception as e:
        print(f"❌ Ошибка: {str(e)}")
    
    finally:
        # Завершаем сессию
        uk_client.logout()
        print("\n👋 Сессия завершена")

if __name__ == "__main__":
    main()
```
