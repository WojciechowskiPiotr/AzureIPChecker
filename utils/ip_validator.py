# azure_vnet_checker/utils/ip_validator.py

import ipaddress
from typing import Union, Tuple
from colorama import Fore, Style


class IPValidator:
    """
    Utility class for validating IP addresses and networks.
    """

    @staticmethod
    def validate_input(ip_input: str) -> Tuple[bool, Union[ipaddress.IPv4Network, str]]:
        """
        Validate and parse IP address or network input.

        Args:
            ip_input (str): IP address or network in CIDR notation

        Returns:
            Tuple[bool, Union[ipaddress.IPv4Network, str]]:
                (is_valid, network_object_or_error_message)
        """
        if not ip_input.strip():
            return False, "Empty input provided"

        ip_input = ip_input.strip()

        # Handle single IP address without mask
        if '/' not in ip_input:
            try:
                ipaddress.IPv4Address(ip_input)
                ip_input += '/32'
            except ipaddress.AddressValueError:
                return False, f"Invalid IP address format: {ip_input}"

        try:
            network = ipaddress.IPv4Network(ip_input, strict=False)

            # Check for multicast addresses (224.0.0.0/4)
            if network.is_multicast:
                return False, "Multicast addresses are not supported in VNet"

            # Check for Class E addresses (240.0.0.0/4)
            if network.network_address >= ipaddress.IPv4Address('240.0.0.0'):
                return False, "Class E addresses are not supported"

            # Check for public addresses and warn user
            if network.is_global:
                print(f"{Fore.YELLOW}Warning: You entered a public IP address ({network})")
                print("Public addresses are typically not used in VNet configurations.")
                confirm = input("Are you sure this is correct? (y/N): ").strip().lower()
                if confirm not in ['y', 'yes']:
                    return False, "Operation cancelled by user"

            return True, network

        except (ipaddress.AddressValueError, ipaddress.NetmaskValueError) as e:
            return False, f"Invalid CIDR notation: {str(e)}"

    @staticmethod
    def is_subnet_overlap(network1: ipaddress.IPv4Network,
                          network2: ipaddress.IPv4Network) -> str:
        """
        Check the relationship between two networks.

        Args:
            network1 (ipaddress.IPv4Network): First network to compare
            network2 (ipaddress.IPv4Network): Second network to compare

        Returns:
            str: Relationship type ('exact', 'contains', 'contained', 'overlap', 'none')
        """
        if network1 == network2:
            return 'exact'
        elif network1.supernet_of(network2):
            return 'contains'
        elif network1.subnet_of(network2):
            return 'contained'
        elif network1.overlaps(network2):
            return 'overlap'
        else:
            return 'none'

    @staticmethod
    def check_host_in_network(host_network: ipaddress.IPv4Network,
                              subnet: ipaddress.IPv4Network) -> bool:
        """
        Check if a host address is contained within a subnet.

        Args:
            host_network (ipaddress.IPv4Network): Host network (/32)
            subnet (ipaddress.IPv4Network): Subnet to check against

        Returns:
            bool: True if host is in subnet, False otherwise
        """
        if host_network.prefixlen == 32:
            return host_network.network_address in subnet
        return False