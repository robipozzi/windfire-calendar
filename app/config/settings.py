import os
from typing import Any
from dotenv import load_dotenv
# Initialize logger at the top so it's available everywhere 
from logger.loggerFactory import logger_factory
logger = logger_factory.get_logger('settings')

class Settings():
    """Read and manage configuration from .env file"""
    def __init__(self):
        """
        Initialize the configuration reader
        """
        self._load_config()
    
    def _load_config(self):
        """
        Load configuration from .env file
        """
        logger.info(f"Loading configuration from .env ...")
        # Load environment from .env file
        load_dotenv()

        logger.info(f"Configuration loaded successfully.")
        logger.info(f"  APP_NAME: {os.getenv('APP_NAME')}")
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
        
        if key in 'API_PORT' or key in 'API_PORT_SECURE':
            raw = os.getenv(key)
            if raw is None or raw.strip() == '':
                return None
            try:
                return int(raw.strip())
            except (ValueError, TypeError):
                logger.warning(f"Invalid integer for {key}: {raw}")
            return None
        
        return os.getenv(key)

####################################################
##### Initialize configuration reader instance #####
####################################################
settings = Settings()