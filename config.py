import yaml
import os
from typing import Optional
from dataclasses import dataclass
from .models import Credentials

@dataclass
class ServiceConfig:
    name: str
    login: str
    password: str

class ConfigLoader:
    
    def __init__(self, config_path: Optional[str] = None):
        if config_path is None:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            self.config_path = os.path.join(os.path.dirname(script_dir), 'secrets.yaml')
        else:
            self.config_path = config_path
    
    def load_credentials(self, service_name: str = "uk_gorod") -> Credentials:
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                secrets = yaml.safe_load(f)
            
            if not secrets:
                raise ValueError(f"Config file {self.config_path} is empty or invalid")
            
            for service in secrets.get('services', []):
                if service.get('name') == service_name:
                    login = service.get('login')
                    password = service.get('password')
                    
                    if not login or not password:
                        raise ValueError(
                            f"Login or password not found for service '{service_name}'"
                        )
                    
                    return Credentials(email=login, password=password)
            
            raise ValueError(f"Service '{service_name}' not found in {self.config_path}")
            
        except FileNotFoundError:
            raise FileNotFoundError(
                f"Config file not found: {self.config_path}\n"
                f"Create secrets.yaml with structure:\n"
                f"services:\n"
                f"  - name: uk_gorod\n"
                f"    login: your_email@mail.ru\n"
                f"    password: your_password"
            )
        except yaml.YAMLError as e:
            raise ValueError(f"YAML parsing error: {e}")
    
    @staticmethod
    def create_example_config(path: str = "secrets.yaml.example"):
        example_config = """services:
  - name: uk_gorod
    login: your_email@mail.ru
    password: your_password
"""
        
        with open(path, 'w', encoding='utf-8') as f:
            f.write(example_config)
        
        print(f"Example config created: {path}")
        print("Copy to secrets.yaml and fill with real data")
