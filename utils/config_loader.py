# azure_vnet_checker/utils/config_loader.py

import configparser
import os
from typing import Dict, Any
from colorama import Fore, Style


class ConfigLoader:
    """
    Configuration loader for Azure VNet Checker application.
    """

    def __init__(self, config_path: str = 'config.ini'):
        """
        Initialize the configuration loader.

        Args:
            config_path (str): Path to the configuration file
        """
        self.config_path = config_path
        self.config = configparser.ConfigParser()
        self._load_config()

    def _load_config(self) -> None:
        """
        Load configuration from the INI file.

        Raises:
            FileNotFoundError: If configuration file doesn't exist
            configparser.Error: If configuration file is malformed
        """
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")

        try:
            self.config.read(self.config_path)
        except configparser.Error as e:
            raise configparser.Error(f"Error reading configuration file: {str(e)}")

    def get_azure_config(self) -> Dict[str, str]:
        """
        Get Azure authentication configuration.

        Returns:
            Dict[str, str]: Dictionary containing Azure configuration

        Raises:
            KeyError: If required configuration keys are missing
        """
        # Check for subscription_id - always required
        if not self.config.has_option('azure', 'subscription_id'):
            raise KeyError("Missing required configuration key: azure.subscription_id")

        subscription_id = self.config.get('azure', 'subscription_id').strip()
        if not subscription_id or subscription_id == 'your-subscription-id-here':
            raise ValueError("Configuration key 'azure.subscription_id' is not properly configured")

        # Get auth method - default to cli
        auth_method = self.config.get('azure', 'auth_method', fallback='cli').strip().lower()

        # Validate auth method
        valid_methods = ['cli', 'interactive']
        if auth_method not in valid_methods:
            raise ValueError(f"Invalid auth_method '{auth_method}'. Use one of: {', '.join(valid_methods)}")

        azure_config = {
            'subscription_id': subscription_id,
            'auth_method': auth_method
        }

        return azure_config

    def get_setting(self, key: str, default: Any = None) -> Any:
        """
        Get application setting value.

        Args:
            key (str): Setting key name
            default (Any): Default value if key doesn't exist

        Returns:
            Any: Setting value or default
        """
        try:
            value = self.config.get('settings', key)
            # Try to convert to appropriate type
            if value.lower() in ['true', 'false']:
                return value.lower() == 'true'
            elif value.isdigit():
                return int(value)
            return value
        except (configparser.NoOptionError, configparser.NoSectionError):
            return default
