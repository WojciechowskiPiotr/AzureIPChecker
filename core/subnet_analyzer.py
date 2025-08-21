# azure_vnet_checker/core/subnet_analyzer.py

import ipaddress
from typing import List, Dict, Any, Optional
from colorama import Fore, Style
from utils.ip_validator import IPValidator


class SubnetAnalyzer:
    """
    Analyzer for checking IP address usage in Azure VNet subnets.
    """

    def __init__(self):
        """Initialize the subnet analyzer."""
        self.ip_validator = IPValidator()

    def analyze_ip_usage(self, target_network: ipaddress.IPv4Network,
                         vnets: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze IP address usage across all VNets.

        Args:
            target_network (ipaddress.IPv4Network): Network to search for
            vnets (List[Dict[str, Any]]): List of VNet configurations

        Returns:
            Dict[str, Any]: Analysis results
        """
        results = {
            'target_network': str(target_network),
            'is_host': target_network.prefixlen == 32,
            'matches': {
                'exact': [],
                'contains': [],
                'contained': [],
                'overlap': [],
                'host_in_subnet': []
            },
            'total_vnets_checked': len(vnets),
            'total_subnets_checked': 0
        }

        print(f"\n{Fore.CYAN}Analyzing network: {target_network}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}Checking {len(vnets)} VNet(s)...{Style.RESET_ALL}\n")

        for vnet in vnets:
            self._analyze_vnet(target_network, vnet, results)

        return results

    def _analyze_vnet(self, target_network: ipaddress.IPv4Network,
                      vnet: Dict[str, Any], results: Dict[str, Any]) -> None:
        """
        Analyze a single VNet for IP usage.

        Args:
            target_network (ipaddress.IPv4Network): Network to search for
            vnet (Dict[str, Any]): VNet configuration
            results (Dict[str, Any]): Results dictionary to update
        """
        vnet_name = vnet['name']
        resource_group = vnet['resource_group']

        print(f"{Fore.YELLOW}Checking VNet: {vnet_name} (RG: {resource_group}){Style.RESET_ALL}")

        # Check VNet address prefixes
        for prefix in vnet.get('address_prefixes', []):
            try:
                vnet_network = ipaddress.IPv4Network(prefix, strict=False)
                relationship = self.ip_validator.is_subnet_overlap(target_network, vnet_network)

                if relationship != 'none':
                    match_info = {
                        'vnet_name': vnet_name,
                        'resource_group': resource_group,
                        'type': 'vnet_address_space',
                        'network': str(vnet_network),
                        'relationship': relationship
                    }

                    if relationship == 'exact':
                        results['matches']['exact'].append(match_info)
                        print(f"  {Fore.RED}EXACT MATCH{Style.RESET_ALL} in VNet address space: {vnet_network}")
                    elif relationship == 'contains':
                        results['matches']['contains'].append(match_info)
                        print(
                            f"  {Fore.YELLOW}SUPERNET{Style.RESET_ALL} VNet address space contains target: {vnet_network}")
                    elif relationship == 'contained':
                        results['matches']['contained'].append(match_info)
                        print(
                            f"  {Fore.YELLOW}SUBNET{Style.RESET_ALL} Target contains VNet address space: {vnet_network}")
                    elif relationship == 'overlap':
                        results['matches']['overlap'].append(match_info)
                        print(f"  {Fore.YELLOW}OVERLAP{Style.RESET_ALL} with VNet address space: {vnet_network}")

            except ipaddress.AddressValueError:
                print(f"  {Fore.RED}Invalid address prefix in VNet: {prefix}{Style.RESET_ALL}")

        # Check individual subnets
        for subnet in vnet.get('subnets', []):
            self._analyze_subnet(target_network, subnet, vnet_name, resource_group, results)
            results['total_subnets_checked'] += 1

    def _analyze_subnet(self, target_network: ipaddress.IPv4Network,
                        subnet: Dict[str, str], vnet_name: str,
                        resource_group: str, results: Dict[str, Any]) -> None:
        """
        Analyze a single subnet for IP usage.

        Args:
            target_network (ipaddress.IPv4Network): Network to search for
            subnet (Dict[str, str]): Subnet configuration
            vnet_name (str): VNet name
            resource_group (str): Resource group name
            results (Dict[str, Any]): Results dictionary to update
        """
        subnet_name = subnet['name']
        subnet_prefix = subnet['address_prefix']

        try:
            subnet_network = ipaddress.IPv4Network(subnet_prefix, strict=False)

            # Check for host in subnet (when target is /32)
            if target_network.prefixlen == 32:
                if self.ip_validator.check_host_in_network(target_network, subnet_network):
                    match_info = {
                        'vnet_name': vnet_name,
                        'resource_group': resource_group,
                        'subnet_name': subnet_name,
                        'type': 'subnet',
                        'network': str(subnet_network),
                        'relationship': 'host_in_subnet'
                    }
                    results['matches']['host_in_subnet'].append(match_info)
                    print(f"    {Fore.GREEN}HOST FOUND{Style.RESET_ALL} in subnet '{subnet_name}': {subnet_network}")
                    return

            # Check network relationships
            relationship = self.ip_validator.is_subnet_overlap(target_network, subnet_network)

            if relationship != 'none':
                match_info = {
                    'vnet_name': vnet_name,
                    'resource_group': resource_group,
                    'subnet_name': subnet_name,
                    'type': 'subnet',
                    'network': str(subnet_network),
                    'relationship': relationship
                }

                if relationship == 'exact':
                    results['matches']['exact'].append(match_info)
                    print(f"    {Fore.RED}EXACT MATCH{Style.RESET_ALL} in subnet '{subnet_name}': {subnet_network}")
                elif relationship == 'contains':
                    results['matches']['contains'].append(match_info)
                    print(
                        f"    {Fore.YELLOW}SUPERNET{Style.RESET_ALL} Subnet contains target '{subnet_name}': {subnet_network}")
                elif relationship == 'contained':
                    results['matches']['contained'].append(match_info)
                    print(
                        f"    {Fore.YELLOW}SUBNET{Style.RESET_ALL} Target contains subnet '{subnet_name}': {subnet_network}")
                elif relationship == 'overlap':
                    results['matches']['overlap'].append(match_info)
                    print(f"    {Fore.YELLOW}OVERLAP{Style.RESET_ALL} with subnet '{subnet_name}': {subnet_network}")

        except ipaddress.AddressValueError:
            print(f"    {Fore.RED}Invalid subnet address prefix: {subnet_prefix}{Style.RESET_ALL}")

    def print_summary(self, results: Dict[str, Any]) -> None:
        """
        Print analysis summary.

        Args:
            results (Dict[str, Any]): Analysis results
        """
        print(f"\n{Fore.CYAN}{'=' * 60}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}ANALYSIS SUMMARY{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'=' * 60}{Style.RESET_ALL}")

        print(f"Target network: {Fore.WHITE}{results['target_network']}{Style.RESET_ALL}")
        print(f"Type: {Fore.WHITE}{'Single host' if results['is_host'] else 'Network range'}{Style.RESET_ALL}")
        print(f"VNets checked: {Fore.WHITE}{results['total_vnets_checked']}{Style.RESET_ALL}")
        print(f"Subnets checked: {Fore.WHITE}{results['total_subnets_checked']}{Style.RESET_ALL}")

        total_matches = sum(len(matches) for matches in results['matches'].values())

        if total_matches == 0:
            print(f"\n{Fore.GREEN}No matches found - Address space is available{Style.RESET_ALL}")
        else:
            print(f"\n{Fore.RED}Found {total_matches} match(es):{Style.RESET_ALL}")

            for match_type, matches in results['matches'].items():
                if matches:
                    type_name = match_type.replace('_', ' ').title()
                    print(f"\n{Fore.YELLOW}{type_name} ({len(matches)}):{Style.RESET_ALL}")

                    for match in matches:
                        location = f"{match['resource_group']}/{match['vnet_name']}"
                        if 'subnet_name' in match:
                            location += f"/{match['subnet_name']}"

                        print(f"  • {match['network']} in {location}")

        print(f"\n{Fore.CYAN}{'=' * 60}{Style.RESET_ALL}")
