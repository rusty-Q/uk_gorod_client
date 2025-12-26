import yaml
import os
from typing import Optional
from dataclasses import dataclass
from .models import Credentials

@dataclass
class ServiceConfig:
    """Конфигурация сервиса из secrets.yaml"""
    name: str
    login: str
    password: str

class ConfigLoader:
    """Загрузчик конфигурации из YAML файла"""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Инициализация загрузчика конфигурации
        
        Args:
            config_path: Путь к файлу конфигурации. 
                        Если None, ищет в папке со скриптом.
        """
        if config_path is None:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            # Поднимаемся на уровень выше (из папки библиотеки)
            self.config_path = os.path.join(os.path.dirname(script_dir), 'secrets.yaml')
        else:
            self.config_path = config_path
    
    def load_credentials(self, service_name: str = "uk_gorod") -> Credentials:
        """
        Загрузка учетных данных для указанного сервиса
        
        Args:
            service_name: Имя сервиса в secrets.yaml
            
        Returns:
            Credentials: Объект с учетными данными
            
        Raises:
            FileNotFoundError: Если файл не найден
            ValueError: Если сервис не найден или данные некорректны
        """
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                secrets = yaml.safe_load(f)
            
            if not secrets:
                raise ValueError(f"Файл {self.config_path} пустой или некорректный")
            
            # Ищем сервис в списке
            for service in secrets.get('services', []):
                if service.get('name') == service_name:
                    login = service.get('login')
                    password = service.get('password')
                    
                    if not login or not password:
                        raise ValueError(
                            f"Не найдены login или password для сервиса '{service_name}'"
                        )
                    
                    return Credentials(email=login, password=password)
            
            raise ValueError(f"Сервис с именем '{service_name}' не найден в {self.config_path}")
            
        except FileNotFoundError:
            raise FileNotFoundError(
                f"Файл конфигурации не найден: {self.config_path}\n"
                f"Создайте файл secrets.yaml с следующей структурой:\n"
                f"services:\n"
                f"  - name: uk_gorod\n"
                f"    login: ваш_email@mail.ru\n"
                f"    password: ваш_пароль"
            )
        except yaml.YAMLError as e:
            raise ValueError(f"Ошибка парсинга YAML файла {self.config_path}: {e}")
        except Exception as e:
            raise ValueError(f"Ошибка чтения конфигурации: {e}")
    
    def load_all_services(self) -> dict:
        """
        Загрузка конфигурации всех сервисов
        
        Returns:
            dict: Словарь {service_name: ServiceConfig}
        """
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                secrets = yaml.safe_load(f)
            
            services = {}
            for service_data in secrets.get('services', []):
                name = service_data.get('name')
                if name:
                    services[name] = ServiceConfig(
                        name=name,
                        login=service_data.get('login', ''),
                        password=service_data.get('password', '')
                    )
            
            return services
            
        except Exception as e:
            raise ValueError(f"Ошибка загрузки конфигурации: {e}")
    
    @staticmethod
    def create_example_config(path: str = "secrets.yaml.example"):
        """Создание примера конфигурационного файла"""
        example_config = """# Файл с учетными данными для сервисов
# ВАЖНО: Не коммитьте этот файл в git! Добавьте в .gitignore
# Создайте secrets.yaml и заполните реальными данными

services:
  # УК Город
  - name: uk_gorod
    login: ваш_email@mail.ru
    password: ваш_пароль_ук_город
  
  # Другие сервисы (при необходимости)
  - name: another_service
    login: логин
    password: пароль
"""
        
        with open(path, 'w', encoding='utf-8') as f:
            f.write(example_config)
        
        print(f"Пример конфигурации создан: {path}")
        print("Скопируйте его в secrets.yaml и заполните своими данными")
