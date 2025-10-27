"""
Pydantic schemas for network resources.
"""
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class SubnetCreate(BaseModel):
    """Schema for creating a subnet."""
    name: str = Field(..., description="Subnet name", min_length=1, max_length=80)
    address_prefix: str = Field(..., description="Subnet address prefix (e.g., 10.0.1.0/24)")


class SubnetResponse(BaseModel):
    """Schema for subnet response."""
    name: str
    address_prefix: str
    id: Optional[str] = None
    provisioning_state: Optional[str] = None


class VNetCreate(BaseModel):
    """Schema for creating a virtual network."""
    vnet_name: str = Field(..., description="Virtual network name", min_length=2, max_length=64)
    address_space: str = Field(..., description="Address space (e.g., 10.0.0.0/16)")
    location: Optional[str] = Field(None, description="Azure region (defaults to config)")
    subnets: List[SubnetCreate] = Field(..., min_items=1, description="List of subnets to create")
    tags: Optional[dict] = Field(default_factory=dict, description="Resource tags")


class VNetResponse(BaseModel):
    """Schema for virtual network response."""
    vnet_name: str
    resource_group: str
    location: str
    address_space: List[str]
    subnets: List[SubnetResponse]
    id: str
    provisioning_state: str
    created_at: str
    tags: Optional[dict] = None


class VNetListItem(BaseModel):
    """Schema for virtual network list item."""
    vnet_name: str
    resource_group: str
    location: str
    address_space: List[str]
    subnet_count: int
    created_at: str
    id: str


class Token(BaseModel):
    """Schema for authentication token response."""
    access_token: str
    token_type: str = "bearer"


class LoginRequest(BaseModel):
    """Schema for login request."""
    username: str
    password: str


class ErrorResponse(BaseModel):
    """Schema for error responses."""
    detail: str
    error_code: Optional[str] = None