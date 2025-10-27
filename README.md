# Azure VNET Management API

A FastAPI-based REST API for creating and managing Azure Virtual Networks (VNETs) with multiple subnets. The API includes JWT-based authentication and stores resource metadata in Azure Table Storage.

## Features

- **JWT Authentication**: Secure API endpoints with token-based authentication
- **VNET Creation**: Create virtual networks with multiple subnets in Azure
- **Resource Management**: Get, list, and delete virtual networks
- **Persistent Storage**: Store VNET metadata in Azure Table Storage for fast retrieval
- **Comprehensive Documentation**: Auto-generated OpenAPI/Swagger documentation

## Architecture

The application follows a clean architecture pattern with separation of concerns:

```
app/
├── core/           # Configuration and security utilities
├── routers/        # API route handlers
├── schemas/        # Pydantic schemas for request/response validation
└── services/       # Business logic (Azure SDK, Storage)
```

## Prerequisites

- Python 3.11+
- Azure Subscription
- Azure Service Principal with Network Contributor role
- Azure Storage Account for Table Storage

## Azure Resources Setup

### 1. Create Service Principal

```bash
# Create service principal
az ad sp create-for-rbac --name "vnet-api-sp" \
  --role "Network Contributor" \
  --scopes /subscriptions/{subscription-id}/resourceGroups/{resource-group}

# Note the output: appId (client_id), password (client_secret), tenant
```

### 2. Create Storage Account

```bash
# Create storage account
az storage account create \
  --name vnetapistorageacct \
  --resource-group {resource-group} \
  --location eastus \
  --sku Standard_LRS

# Get connection string
az storage account show-connection-string \
  --name vnetapistorageacct \
  --resource-group {resource-group}
```

### 3. Create Resource Group (if needed)

```bash
az group create --name vnet-api-rg --location eastus
```

## Installation

### Local Development

1. **Clone the repository**

```bash
git clone https://github.com/yourusername/azure-vnet-api.git
cd azure-vnet-management-api
```

2. **Create virtual environment**

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**

```bash
pip install -r requirements.txt
```

4. **Configure environment variables**

```bash
cp .env.example .env
# Edit .env with your Azure credentials and configuration
```

5. **Generate SECRET_KEY**

```bash
python -c "import secrets; print(secrets.token_hex(32))"
# Copy the output to SECRET_KEY in .env
```

6. **Run the application**

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## API Usage

### 1. Authentication

First, obtain a JWT token by logging in:

```bash
curl -X POST http://localhost:8000/api/v1/vnet/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "password"
  }'
```

Response:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### 2. Create Virtual Network

```bash
curl -X POST http://localhost:8000/api/v1/vnet/create \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "vnet_name": "my-vnet",
    "address_space": "10.0.0.0/16",
    "location": "eastus",
    "subnets": [
      {
        "name": "web-subnet",
        "address_prefix": "10.0.1.0/24"
      },
      {
        "name": "app-subnet",
        "address_prefix": "10.0.2.0/24"
      },
      {
        "name": "db-subnet",
        "address_prefix": "10.0.3.0/24"
      }
    ],
    "tags": {
      "Environment": "Production",
      "Project": "MyApp"
    }
  }'
```

### 3. Get Virtual Network Details

```bash
curl -X GET http://localhost:8000/api/v1/vnet/my-vnet \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 4. List All Virtual Networks

```bash
curl -X GET http://localhost:8000/api/v1/vnet/ \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 5. Delete Virtual Network

```bash
curl -X DELETE http://localhost:8000/api/v1/vnet/my-vnet \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## API Documentation

Once the application is running, access the interactive API documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Configuration

All configuration is managed through environment variables in the `.env` file:

| Variable | Description | Required |
|----------|-------------|----------|
| `AZURE_SUBSCRIPTION_ID` | Azure subscription ID | Yes |
| `AZURE_TENANT_ID` | Azure AD tenant ID | Yes |
| `AZURE_CLIENT_ID` | Service principal client ID | Yes |
| `AZURE_CLIENT_SECRET` | Service principal client secret | Yes |
| `AZURE_RESOURCE_GROUP` | Target resource group name | Yes |
| `AZURE_LOCATION` | Default Azure region | Yes |
| `AZURE_STORAGE_CONNECTION_STRING` | Storage account connection string | Yes |
| `AZURE_STORAGE_TABLE_NAME` | Table name for metadata | Yes |
| `SECRET_KEY` | JWT secret key | Yes |
| `API_USERNAME` | API username | Yes |
| `API_PASSWORD` | API password | Yes |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token expiration time | No (default: 30) |

## Project Structure

```
azure-vnet-management-api/
├── app/
│   ├── __init__.py
│   ├── main.py                # FastAPI application entry point
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py          # Configuration settings
│   │   └── security.py        # JWT authentication logic
│   ├── routers/
│   │   ├── __init__.py
│   │   └── vnet.py            # VNET API endpoints
│   ├── schemas/
│   │   ├── __init__.py
│   │   └── network.py         # Pydantic schemas
│   └── services/
│       ├── __init__.py
│       ├── azure_service.py   # Azure SDK integration
│       └── storage_service.py # Azure Table Storage operations
├── tests/
│   ├── __init__.py
│   └── test_vnet.py           # Unit tests
├── .env                       # Example environment variables
├── .gitignore                 # Git ignore file
├── requirements.txt           # Python dependencies
└── README.md                  # This file
```

## Security Considerations

### Production Deployment

1. **Password Hashing**: Store hashed passwords, not plain text
   ```python
   from app.core.security import get_password_hash
   hashed_password = get_password_hash("your-password")
   ```

2. **CORS Configuration**: Restrict allowed origins in `main.py`
   ```python
   allow_origins=["https://your-domain.com"]
   ```

3. **HTTPS**: Always use HTTPS in production
   
4. **Secret Management**: Use Azure Key Vault for secrets
   
5. **Service Principal**: Use managed identity when possible

6. **Token Expiration**: Set appropriate token expiration times

7. **Rate Limiting**: Implement rate limiting for API endpoints

## Troubleshooting

### Common Issues

1. **Authentication Failed**
   - Verify service principal credentials
   - Check RBAC role assignments
   - Ensure subscription ID is correct

2. **Storage Connection Failed**
   - Verify connection string format
   - Check storage account firewall rules
   - Ensure table name is valid

3. **VNET Creation Failed**
   - Check resource group exists
   - Verify location is valid
   - Ensure no naming conflicts
   - Check address space doesn't overlap

## License

MIT License - See LICENSE file for details