# Azure VNet IP Checker

Python application for checking IP address and subnet usage in Azure Virtual Networks. The tool analyzes all VNets in your Azure subscription to determine if a given IP address or network range is already in use.

## Features

- **Multiple Authentication Methods**: Azure CLI or interactive browser login
- **Comprehensive Analysis**: Checks for exact matches, supernetting, subnetting, and overlaps
- **Host Detection**: Identifies if a single host IP is contained within existing subnets
- **Flexible Input**: Supports both interactive and command-line input modes
- **Resource Group Filtering**: Option to limit search to specific resource groups
- **Colored Output**: Easy-to-read console output with color coding
- **Input Validation**: Validates IP addresses and rejects invalid formats

## Installation

### Prerequisites

- Python 3.7 or higher
- Azure CLI (optional, for CLI authentication)
- Azure subscription with appropriate permissions

### Setup

1. **Clone or download the project**
   ```bash
   git clone <repository-url>
   cd azure_vnet_checker
   ```

2. **Create project structure**
   ```bash
   chmod +x setup_project.sh
   ./setup_project.sh
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure authentication**
   ```bash
   cp config.example.ini config.ini
   # Edit config.ini with your settings
   ```

## Configuration

### Authentication Methods

#### Azure CLI (Recommended)
```ini
[azure]
auth_method = cli
subscription_id = your-subscription-id-here
```

Prerequisites: Install Azure CLI and run `az login`

#### Interactive Browser
```ini
[azure]
auth_method = interactive
subscription_id = your-subscription-id-here
```

This will open a browser window for Azure authentication.

### Finding Your Subscription ID

```bash
# Using Azure CLI
az account show --query id -o tsv

# Or list all subscriptions
az account list --query "[].{Name:name, SubscriptionId:id}" -o table
```

## Usage

### Command Line Mode

```bash
# Basic usage with IP parameter
python main.py --ip 10.0.0.1

# Network range
python main.py --ip 172.16.20.0/24

# With specific subscription
python main.py -s "12345678-1234-1234-1234-123456789abc" --ip 192.168.1.0/24

# Limit to specific resource group
python main.py -rg "my-resource-group" --ip 10.0.0.100/32

# Combine all parameters
python main.py -s "subscription-id" -rg "resource-group" --ip 10.0.0.0/16
```

### Interactive Mode

```bash
python main.py
```

The application will prompt you to enter the IP address or network range.

### Command Line Options

- `--ip`: IP address or network in CIDR notation (e.g., `10.0.0.1` or `172.16.20.0/24`)
- `-s, --subscription`: Azure subscription ID (overrides config file)
- `-rg, --resource-group`: Specific resource group to search (default: all)

## Analysis Types

The tool performs comprehensive analysis to detect various network relationships:

### Exact Match
When the searched network exactly matches a configured subnet.

### Supernetting
When an existing subnet contains the searched network range.
- Example: Searching for `10.0.1.0/24` finds existing `10.0.0.0/16`

### Subnetting
When the searched network contains existing subnets.
- Example: Searching for `10.0.0.0/16` finds existing `10.0.1.0/24`

### Host in Subnet
When a single host IP (/32) is contained within an existing subnet.
- Example: Searching for `10.0.1.50/32` finds existing `10.0.1.0/24`

### Overlap
When networks partially overlap without one containing the other.

## Output Examples

### No Conflicts Found
```
========================================
ANALYSIS SUMMARY
========================================
Target network: 192.168.100.0/24
Type: Network range
VNets checked: 5
Subnets checked: 15

No matches found - Address space is available
```

### Conflicts Detected
```
========================================
ANALYSIS SUMMARY
========================================
Target network: 10.0.1.0/24
Type: Network range
VNets checked: 3
Subnets checked: 8

Found 2 match(es):

Exact (1):
  • 10.0.1.0/24 in production-rg/prod-vnet/web-subnet

Contains (1):
  • 10.0.0.0/16 in development-rg/dev-vnet
```

## Error Handling

The application validates input and provides helpful error messages:

- **Invalid IP formats**: Detailed error messages for malformed addresses
- **Multicast addresses**: Rejected with explanation
- **Class E addresses**: Not supported in Azure VNets
- **Public IP warnings**: Warns when public IPs are entered (unusual in VNets)
- **Authentication failures**: Clear guidance on authentication setup

## Supported Input Formats

- Single IP addresses: `10.0.0.1` (automatically treated as /32)
- CIDR notation: `172.16.20.0/24`
- Any valid IPv4 network range

## Project Structure

```
azure_vnet_checker/
├── utils/
│   ├── config_loader.py    # Configuration management
│   └── ip_validator.py     # IP address validation
├── core/
│   ├── azure_client.py     # Azure API client
│   └── subnet_analyzer.py  # Network analysis logic
├── main.py                 # Main application entry point
├── config.ini              # Configuration file (create from example)
├── config.example.ini      # Configuration template
└── requirements.txt        # Python dependencies
```

## Troubleshooting

### Import Errors
Ensure you have the correct project structure and `__init__.py` files:
```bash
touch utils/__init__.py
touch core/__init__.py
```

### Authentication Issues
For Azure CLI authentication:
```bash
az login
az account set --subscription "your-subscription-id"
```

For interactive authentication, ensure your browser allows popups from Microsoft login pages.

### Permission Issues
Ensure your Azure account has at least `Reader` permissions on the subscription or resource groups you want to analyze.

## Dependencies

- `azure-identity`: Azure authentication
- `azure-mgmt-network`: Azure Network Management API
- `azure-mgmt-resource`: Azure Resource Management API
- `colorama`: Colored console output
- `ipaddress`: IP address manipulation (built-in)

## License

This project is provided as-is for educational and operational purposes.