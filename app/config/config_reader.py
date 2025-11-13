import os
from typing import Any
from dotenv import load_dotenv

# Initialize logger at the top so it's available everywhere
from logger.loggingFactory import logger_factory
logger = logger_factory.get_logger('config_reader')

class ConfigError(Exception):
    """Custom exception for configuration errors"""
    pass

class ConfigReader:
    """Read and manage configuration from JSON file"""
    def __init__(self, config_file: str = 'config/config.json'):
        """
        Initialize the configuration reader
        
        Args:
            config_file: Path to the JSON configuration file
        """
        self.config_file = config_file
        self._load_config()
    
    def _load_config(self):
        """
        Load configuration from .env file
        
        Raises:
            ConfigError: If file doesn't exist or JSON is invalid
        """
        logger.info(f"Loading configuration from .env ...")
        # Load environment from .env file
        load_dotenv()

        logger.info(f"Configuration loaded successfully.")
        logger.info(f"  API_HOST: {os.getenv('API_HOST')}")
        logger.info(f"  API_PORT: {os.getenv('API_PORT')}")
        logger.info(f"  SSL_KEYFILE: {os.getenv('SSL_KEYFILE')}")
        logger.info(f"  SSL_CERTFILE: {os.getenv('SSL_CERTFILE')}")
        logger.info(f"  ENFORCE_HTTPS: {os.getenv('ENFORCE_HTTPS')}")
        logger.info(f"  ALLOWED_HOSTS: {os.getenv('ALLOWED_HOSTS')}")
        logger.info(f"  KEYCLOAK_SERVER_URL: {os.getenv('KEYCLOAK_SERVER_URL')}")
        
    def get(self, key: str) -> Any:
        """
        Get an environment variable value by key.
        
        Args:
            key: Environment variable name
            
        Returns:
            The value of the environment variable or None if not set
        """
        if key in 'ENFORCE_HTTPS':
            value = None
            raw = os.getenv(key)
            if isinstance(raw, str):
                normalized = raw.strip().lower()
                value = normalized in ('true', '1', 'yes', 'on')
            else:
                value = bool(raw)
            return value

        return os.getenv(key)
    
    def reload_config(self):
        """
        Reload configuration from file
        
        Raises:
            ConfigError: If configuration file is invalid
        """
        logger.info("Reloading configuration...")
        self.config.clear()
        self._load_config()
    
# Convenience function for quick usage
def load_config(config_file: str = 'config.json') -> ConfigReader:
    """
    Quick function to load configuration
    
    Args:
        config_file: Path to configuration file
        
    Returns:
        ConfigReader instance
        
    Raises:
        ConfigError: If configuration is invalid
    """
    return ConfigReader(config_file)

####################################################
##### Initialize configuration reader instance #####
####################################################
config = ConfigReader()

# Example usage
if __name__ == "__main__":
    try:
        # Load configuration
        config_reader = load_config('config.json')
        
        # List all services
        print(f"\n📋 Available services: {config_reader.list_services()}")
        
        # Get specific service
        keycloak_config = config_reader.get_service('windfire-calendar-srv')
        print(f"\n🔐 Keycloak service config:")
        print(f"   Realm: {keycloak_config.realm}")
        print(f"   Client ID: {keycloak_config.client_id}")
        print(f"   Client Secret: (hidden for security)")
        
        # Access all services
        print(f"\n🔍 All services:")
        for service_name, service_config in config_reader.get_all_services().items():
            print(f"   - {service_name}: realm={service_config.realm}")
        
    except ConfigError as e:
        print(f"❌ Configuration Error: {str(e)}")
    except Exception as e:
        print(f"❌ Unexpected Error: {str(e)}")