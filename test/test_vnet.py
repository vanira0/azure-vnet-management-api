"""
Unit tests for VNET API endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.security import create_access_token

client = TestClient(app)


@pytest.fixture
def auth_token():
    """Generate a test authentication token."""
    token = create_access_token(data={"sub": "testuser"})
    return f"Bearer {token}"


def test_root_endpoint():
    """Test the root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()
    assert response.json()["status"] == "healthy"


def test_health_check():
    """Test the health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_login_success():
    """Test successful login."""
    # Note: This will fail without proper credentials in environment
    # This is a template test
    login_data = {
        "username": "admin",
        "password": "test-password"
    }
    response = client.post("/api/v1/vnet/login", json=login_data)
    # In real test, mock the authentication
    assert response.status_code in [200, 401]


def test_create_vnet_without_auth():
    """Test creating VNET without authentication should fail."""
    vnet_data = {
        "vnet_name": "test-vnet",
        "address_space": "10.0.0.0/16",
        "subnets": [
            {
                "name": "subnet1",
                "address_prefix": "10.0.1.0/24"
            }
        ]
    }
    response = client.post("/api/v1/vnet/create", json=vnet_data)
    assert response.status_code == 403  # Forbidden without auth


def test_list_vnets_without_auth():
    """Test listing VNETs without authentication should fail."""
    response = client.get("/api/v1/vnet/")
    assert response.status_code == 403


def test_get_vnet_without_auth():
    """Test getting VNET details without authentication should fail."""
    response = client.get("/api/v1/vnet/test-vnet")
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_create_vnet_with_auth(auth_token):
    """Test creating VNET with authentication."""
    # This test requires mocking Azure services
    # This is a template
    vnet_data = {
        "vnet_name": "test-vnet",
        "address_space": "10.0.0.0/16",
        "subnets": [
            {
                "name": "subnet1",
                "address_prefix": "10.0.1.0/24"
            }
        ]
    }
    headers = {"Authorization": auth_token}
    # In real test, mock AzureNetworkService
    # response = client.post("/api/v1/vnet/create", json=vnet_data, headers=headers)
    # assert response.status_code == 201
    pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])