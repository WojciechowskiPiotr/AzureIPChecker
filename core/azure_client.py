# azure_vnet_checker/core/azure_client.py

from azure.identity import (
    InteractiveBrowserCredential,
    AzureCliCredential,
    CredentialUnavailableError
)
from azure.mgmt.network import NetworkManagementClient
from azure.mgmt.resource import ResourceManagementClient
from azure.core.exceptions import ClientAuthenticationError, ResourceNotFoundError
from typing import List, Dict, Any, Optional
from colorama import Fore, Style
import sys


class AzureClient:
    """
    Azure client for managing connections to Azure services.
    """

    def __init__(self, subscription_id: str, auth_method: str = 'cli'):
        """
        Initialize Azure client with authentication credentials.

        Args:
            subscription_id (str): Azure subscription ID
            auth_method (str): Authentication method ('cli' or 'interactive')
        """
        self.subscription_id = subscription_id
        self.credential = None
        self.network_client = None
        self.resource_client = None

        try:
            self.credential = self._get_credential(auth_method)

            self.network_client = NetworkManagementClient(
                credential=self.credential,
                subscription_id=subscription_id
            )

            self.resource_client = ResourceManagementClient(
                credential=self.credential,
                subscription_id=subscription_id
            )

        except ClientAuthenticationError as e:
            print(f"{Fore.RED}Authentication failed: {str(e)}{Style.RESET_ALL}")
            sys.exit(1)
        except CredentialUnavailableError as e:
            print(f"{Fore.RED}Credential unavailable: {str(e)}{Style.RESET_ALL}")
            if auth_method == 'cli':
                print(f"{Fore.YELLOW}Try running 'az login' first or use different auth method{Style.RESET_ALL}")
            sys.exit(1)
        except Exception as e:
            print(f"{Fore.RED}Failed to initialize Azure client: {str(e)}{Style.RESET_ALL}")
            sys.exit(1)

    def _get_credential(self, auth_method: str):
        """
        Get appropriate credential based on authentication method.

        Args:
            auth_method (str): Authentication method ('cli' or 'interactive')

        Returns:
            Credential object for Azure authentication
        """
        print(f"{Fore.CYAN}Using authentication method: {auth_method}{Style.RESET_ALL}")

        if auth_method == 'interactive':
            print(f"{Fore.YELLOW}Opening browser for interactive login...{Style.RESET_ALL}")
            return InteractiveBrowserCredential()

        elif auth_method == 'cli':
            print(f"{Fore.YELLOW}Using Azure CLI credentials...{Style.RESET_ALL}")
            return AzureCliCredential()

        else:
            raise ValueError(f"Unsupported authentication method: {auth_method}. Use 'cli' or 'interactive'.")

    def test_connection(self) -> bool:
        """
        Test the connection to Azure services.

        Returns:
            bool: True if connection is successful, False otherwise
        """
        try:
            # Try to list resource groups to test connection
            list(self.resource_client.resource_groups.list())
            return True
        except Exception as e:
            print(f"{Fore.RED}Connection test failed: {str(e)}{Style.RESET_ALL}")
            return False

    def get_resource_groups(self, resource_group_filter: Optional[str] = None) -> List[str]:
        """
        Get list of resource group names.

        Args:
            resource_group_filter (Optional[str]): Specific resource group name to filter

        Returns:
            List[str]: List of resource group names
        """
        try:
            if resource_group_filter:
                # Check if specific resource group exists
                try:
                    self.resource_client.resource_groups.get(resource_group_filter)
                    return [resource_group_filter]
                except ResourceNotFoundError:
                    print(f"{Fore.RED}Resource group '{resource_group_filter}' not found{Style.RESET_ALL}")
                    return []
            else:
                # Get all resource groups
                resource_groups = []
                for rg in self.resource_client.resource_groups.list():
                    resource_groups.append(rg.name)
                return resource_groups

        except Exception as e:
            print(f"{Fore.RED}Failed to retrieve resource groups: {str(e)}{Style.RESET_ALL}")
            return []

    def get_vnets_in_resource_group(self, resource_group_name: str) -> List[Dict[str, Any]]:
        """
        Get all virtual networks in a specific resource group.

        Args:
            resource_group_name (str): Name of the resource group

        Returns:
            List[Dict[str, Any]]: List of VNet information dictionaries
        """
        vnets = []
        try:
            for vnet in self.network_client.virtual_networks.list(resource_group_name):
                vnet_info = {
                    'name': vnet.name,
                    'resource_group': resource_group_name,
                    'location': vnet.location,
                    'address_prefixes': vnet.address_space.address_prefixes if vnet.address_space else [],
                    'subnets': []
                }

                # Get subnet information
                if vnet.subnets:
                    for subnet in vnet.subnets:
                        subnet_info = {
                            'name': subnet.name,
                            'address_prefix': subnet.address_prefix
                        }
                        vnet_info['subnets'].append(subnet_info)

                vnets.append(vnet_info)

        except Exception as e:
            print(
                f"{Fore.YELLOW}Warning: Failed to retrieve VNets from resource group '{resource_group_name}': {str(e)}{Style.RESET_ALL}")

        return vnets

    def get_all_vnets(self, resource_group_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get all virtual networks across specified resource groups.

        Args:
            resource_group_filter (Optional[str]): Specific resource group to search in

        Returns:
            List[Dict[str, Any]]: List of all VNet information dictionaries
        """
        all_vnets = []
        resource_groups = self.get_resource_groups(resource_group_filter)

        if not resource_groups:
            print(f"{Fore.YELLOW}No resource groups found to search{Style.RESET_ALL}")
            return all_vnets

        print(f"{Fore.CYAN}Searching in {len(resource_groups)} resource group(s)...{Style.RESET_ALL}")

        for rg_name in resource_groups:
            print(f"{Fore.CYAN}Checking resource group: {rg_name}{Style.RESET_ALL}")
            vnets = self.get_vnets_in_resource_group(rg_name)
            all_vnets.extend(vnets)

            if vnets:
                print(f"{Fore.GREEN}Found {len(vnets)} VNet(s) in {rg_name}{Style.RESET_ALL}")

        return all_vnets
