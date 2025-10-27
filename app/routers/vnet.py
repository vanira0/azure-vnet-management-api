from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from app.schemas.network import (
    VNetCreate, VNetResponse, VNetListItem, Token, LoginRequest
)
from app.services.azure_service import AzureNetworkService
from app.services.storage_service import StorageService
from app.core.security import (
    get_current_user, verify_password, create_access_token, get_password_hash
)
from app.core.config import settings
from azure.core.exceptions import AzureError
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/vnet", tags=["Virtual Networks"])

# Service instances
azure_service = AzureNetworkService()
storage_service = StorageService()


@router.post("/login", response_model=Token, status_code=status.HTTP_200_OK)
async def login(login_data: LoginRequest):
    """
    Authenticate user and return JWT token.
    
    - **username**: API username
    - **password**: API password
    
    Returns JWT access token for API authentication.
    """
    # In production, retrieve hashed password from database
    if login_data.username != settings.API_USERNAME:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    
    # For demo: compare with plain password (use hashed in production)
    if login_data.password != settings.API_PASSWORD:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    
    # Create access token
    access_token = create_access_token(data={"sub": login_data.username})
    
    return Token(access_token=access_token, token_type="bearer")


@router.post(
    "/create",
    response_model=VNetResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Virtual Network with Subnets"
)
async def create_vnet(
    vnet_data: VNetCreate,
    current_user: dict = Depends(get_current_user)
):
    """
    Create a new virtual network with multiple subnets in Azure.
    
    This endpoint:
    1. Creates a VNET with specified address space
    2. Creates multiple subnets within the VNET
    3. Stores the resource metadata in Azure Table Storage
    
    - **vnet_name**: Name of the virtual network (2-64 characters)
    - **address_space**: CIDR notation for VNet (e.g., "10.0.0.0/16")
    - **location**: Azure region (optional, uses default from config)
    - **subnets**: List of subnets to create (minimum 1)
    - **tags**: Optional resource tags
    
    **Requires authentication**: Bearer token in Authorization header
    """
    try:
        logger.info(f"User {current_user['username']} creating VNet: {vnet_data.vnet_name}")
        
        # Create VNET in Azure
        vnet_response = await azure_service.create_vnet(vnet_data)
        
        # Store metadata in Table Storage
        await storage_service.store_vnet(vnet_response)
        
        return vnet_response
        
    except AzureError as e:
        logger.error(f"Azure error creating VNet: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create virtual network: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error creating VNet: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )


@router.get(
    "/{vnet_name}",
    response_model=VNetResponse,
    summary="Get Virtual Network Details"
)
async def get_vnet(
    vnet_name: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Retrieve details of a specific virtual network.
    
    Returns complete information about the VNET including:
    - Address space
    - All subnets
    - Location and resource group
    - Provisioning state
    - Resource tags
    
    **Requires authentication**: Bearer token in Authorization header
    """
    try:
        logger.info(f"User {current_user['username']} retrieving VNet: {vnet_name}")
        
        # Get from Azure (source of truth)
        vnet_response = await azure_service.get_vnet(vnet_name)
        
        # Update storage with latest data
        await storage_service.store_vnet(vnet_response)
        
        return vnet_response
        
    except AzureError as e:
        logger.error(f"Azure error retrieving VNet: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Virtual network '{vnet_name}' not found"
        )
    except Exception as e:
        logger.error(f"Unexpected error retrieving VNet: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )


@router.get(
    "/",
    response_model=List[VNetListItem],
    summary="List All Virtual Networks"
)
async def list_vnets(
    current_user: dict = Depends(get_current_user)
):
    """
    List all virtual networks in the resource group.
    
    Returns a summary list of all VNets including:
    - Name and location
    - Address space
    - Subnet count
    - Creation timestamp
    - Resource ID
    
    Data is retrieved from Azure Table Storage for fast access.
    
    **Requires authentication**: Bearer token in Authorization header
    """
    try:
        logger.info(f"User {current_user['username']} listing VNets")
        
        # Get from storage for fast listing
        vnets = await storage_service.list_vnets()
        
        return vnets
        
    except AzureError as e:
        logger.error(f"Error listing VNets: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list virtual networks: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error listing VNets: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )


@router.delete(
    "/{vnet_name}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Virtual Network"
)
async def delete_vnet(
    vnet_name: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Delete a virtual network and all its subnets.
    
    This operation:
    1. Deletes the VNET from Azure
    2. Removes metadata from Table Storage
    
    **Warning**: This operation cannot be undone.
    
    **Requires authentication**: Bearer token in Authorization header
    """
    try:
        logger.info(f"User {current_user['username']} deleting VNet: {vnet_name}")
        
        # Delete from Azure
        await azure_service.delete_vnet(vnet_name)
        
        # Delete from storage
        await storage_service.delete_vnet(vnet_name)
        
        return None
        
    except AzureError as e:
        logger.error(f"Azure error deleting VNet: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete virtual network: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error deleting VNet: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )