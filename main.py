# azure_vnet_checker/main.py

import argparse
import sys
import os
from colorama import init, Fore, Style

try:
    from utils.config_loader import ConfigLoader
    from utils.ip_validator import IPValidator
    from core.azure_client import AzureClient
    from core.subnet_analyzer import SubnetAnalyzer
except ImportError as e:
    print(f"Import error: {e}")
    print("Please ensure utils/ and core/ directories exist with required modules")
    sys.exit(1)


class AzureVNetChecker:
    """
    Main application class for Azure VNet IP address checker.
    """

    def __init__(self):
        """Initialize the Azure VNet Checker application."""
        # Initialize colorama for Windows compatibility
        init(autoreset=True)

        self.config_loader = None
        self.azure_client = None
        self.ip_validator = IPValidator()
        self.subnet_analyzer = SubnetAnalyzer()

    def parse_arguments(self) -> argparse.Namespace:
        """
        Parse command line arguments.

        Returns:
            argparse.Namespace: Parsed command line arguments
        """
        parser = argparse.ArgumentParser(
            description="Check IP address usage in Azure Virtual Networks",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  python main.py
  python main.py --ip 10.0.0.1
  python main.py --ip 172.16.20.0/24
  python main.py -s "12345678-1234-1234-1234-123456789abc" --ip 192.168.1.0/24
  python main.py -rg "my-resource-group" --ip 10.0.0.100/32
            """
        )

        parser.add_argument(
            '--ip',
            help='IP address or network in CIDR notation (e.g., 10.0.0.1 or 172.16.20.0/24)',
            type=str
        )

        parser.add_argument(
            '-s', '--subscription',
            help='Azure subscription ID (overrides config file)',
            type=str
        )

        parser.add_argument(
            '-rg', '--resource-group',
            help='Specific resource group to search (default: all)',
            type=str
        )

        return parser.parse_args()

    def load_configuration(self, subscription_override: str = None) -> bool:
        """
        Load application configuration.

        Args:
            subscription_override (str): Override subscription ID from command line

        Returns:
            bool: True if configuration loaded successfully, False otherwise
        """
        try:
            self.config_loader = ConfigLoader()
            azure_config = self.config_loader.get_azure_config()

            # Override subscription if provided via command line
            if subscription_override:
                azure_config['subscription_id'] = subscription_override
                print(f"{Fore.YELLOW}Using subscription from command line: {subscription_override}{Style.RESET_ALL}")

            # Initialize Azure client with authentication
            auth_method = azure_config.get('auth_method', 'cli')

            self.azure_client = AzureClient(
                subscription_id=azure_config['subscription_id'],
                auth_method=auth_method
            )

            return True

        except (FileNotFoundError, KeyError, ValueError) as e:
            print(f"{Fore.RED}Configuration error: {str(e)}{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}Please ensure config.ini is properly configured{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}Available auth methods: cli, interactive{Style.RESET_ALL}")
            return False
        except Exception as e:
            print(f"{Fore.RED}Unexpected error loading configuration: {str(e)}{Style.RESET_ALL}")
            return False

    def get_user_input(self, ip_from_args: str = None) -> tuple:
        """
        Get IP address input from user or command line arguments.

        Args:
            ip_from_args (str): IP address provided via command line arguments

        Returns:
            tuple: (is_valid, network_object_or_error_message)
        """
        print(f"\n{Fore.CYAN}Azure VNet IP Address Checker{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'=' * 40}{Style.RESET_ALL}")

        # If IP provided via command line, validate it directly
        if ip_from_args:
            print(f"\nUsing IP address from command line: {ip_from_args}")

            is_valid, result = self.ip_validator.validate_input(ip_from_args)

            if is_valid:
                print(f"{Fore.GREEN}Validated network: {result}{Style.RESET_ALL}")
                return True, result
            else:
                print(f"{Fore.RED}Error: {result}{Style.RESET_ALL}")
                return False, result

        # Interactive input mode
        while True:
            print(f"\nEnter IP address or network in CIDR notation:")
            print(f"Examples: 10.0.0.1/32, 172.16.20.0/24, or 192.168.1.100")

            ip_input = input(f"{Fore.GREEN}IP/Network: {Style.RESET_ALL}").strip()

            if not ip_input:
                print(f"{Fore.RED}Please enter a valid IP address or network{Style.RESET_ALL}")
                continue

            is_valid, result = self.ip_validator.validate_input(ip_input)

            if is_valid:
                print(f"\n{Fore.GREEN}Validated network: {result}{Style.RESET_ALL}")

                # Confirm with user
                confirm = input(f"\nProceed with analysis? (Y/n): ").strip().lower()
                if confirm in ['', 'y', 'yes']:
                    return True, result
                else:
                    continue
            else:
                print(f"{Fore.RED}Error: {result}{Style.RESET_ALL}")

                # Ask if user wants to try again
                retry = input(f"\nTry again? (Y/n): ").strip().lower()
                if retry in ['n', 'no']:
                    return False, "User cancelled input"

    def run_analysis(self, target_network, resource_group_filter: str = None) -> bool:
        """
        Run the main analysis process.

        Args:
            target_network: Network object to analyze
            resource_group_filter (str): Optional resource group filter

        Returns:
            bool: True if analysis completed successfully, False otherwise
        """
        try:
            # Test Azure connection
            print(f"\n{Fore.CYAN}Testing Azure connection...{Style.RESET_ALL}")
            if not self.azure_client.test_connection():
                return False

            print(f"{Fore.GREEN}Connection successful{Style.RESET_ALL}")

            # Get all VNets
            print(f"\n{Fore.CYAN}Retrieving VNet configurations...{Style.RESET_ALL}")
            vnets = self.azure_client.get_all_vnets(resource_group_filter)

            if not vnets:
                print(f"{Fore.YELLOW}No VNets found to analyze{Style.RESET_ALL}")
                return True

            print(f"{Fore.GREEN}Found {len(vnets)} VNet(s) to analyze{Style.RESET_ALL}")

            # Analyze IP usage
            results = self.subnet_analyzer.analyze_ip_usage(target_network, vnets)

            # Print summary
            self.subnet_analyzer.print_summary(results)

            return True

        except KeyboardInterrupt:
            print(f"\n{Fore.YELLOW}Analysis interrupted by user{Style.RESET_ALL}")
            return False
        except Exception as e:
            print(f"\n{Fore.RED}Analysis failed: {str(e)}{Style.RESET_ALL}")
            return False

    def run(self) -> int:
        """
        Run the main application.

        Returns:
            int: Exit code (0 for success, 1 for error)
        """
        try:
            # Parse command line arguments
            args = self.parse_arguments()

            # Load configuration
            if not self.load_configuration(args.subscription):
                return 1

            # Get user input
            is_valid, target_network = self.get_user_input(args.ip)
            if not is_valid:
                print(f"{Fore.YELLOW}Exiting...{Style.RESET_ALL}")
                return 0

            # Run analysis
            if self.run_analysis(target_network, args.resource_group):
                return 0
            else:
                return 1

        except KeyboardInterrupt:
            print(f"\n{Fore.YELLOW}Application interrupted by user{Style.RESET_ALL}")
            return 0
        except Exception as e:
            print(f"\n{Fore.RED}Unexpected error: {str(e)}{Style.RESET_ALL}")
            return 1


def main():
    """Main entry point of the application."""
    app = AzureVNetChecker()
    sys.exit(app.run())


if __name__ == "__main__":
    main()