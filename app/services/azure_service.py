"""
Azure Network Management Service.
Handles VNET and subnet creation using Azure SDK.
"""
from azure.identity import ClientSecretCredential
from azure.mgmt.network import NetworkManagementClient
from azure.mgmt.network.models import VirtualNetwork, AddressSpace, Subnet
from azure.core.exceptions import AzureError
from typing import List, Dict
from app.core.config import settings
from app.schemas.network import VNetCreate, VNetResponse, SubnetResponse
import logging

logger = logging.getLogger(__name__)


class AzureNetworkService:
    """Service for managing Azure Virtual Networks."""
    
    def __init__(self):
        """Initialize Azure Network Management Client."""
        self.credential = ClientSecretCredential(
            tenant_id=settings.AZURE_TENANT_ID,
            client_id=settings.AZURE_CLIENT_ID,
            client_secret=settings.AZURE_CLIENT_SECRET
        )
        self.network_client = NetworkManagementClient(
            credential=self.credential,
            subscription_id=settings.AZURE_SUBSCRIPTION_ID
        )
        self.resource_group = settings.AZURE_RESOURCE_GROUP
    
    async def create_vnet(self, vnet_data: VNetCreate) -> VNetResponse:
        """
        Create a virtual network with subnets.
        
        Args:
            vnet_data: Virtual network creation data
            
        Returns:
            VNetResponse with created resource details
            
        Raises:
            AzureError: If creation fails
        """
        try:
            location = vnet_data.location or settings.AZURE_LOCATION
            
            # Prepare subnet configurations
            subnet_configs = [
                Subnet(
                    name=subnet.name,
                    address_prefix=subnet.address_prefix
                )
                for subnet in vnet_data.subnets
            ]
            
            # Create VNet parameters
            vnet_params = VirtualNetwork(
                location=location,
                address_space=AddressSpace(
                    address_prefixes=[vnet_data.address_space]
                ),
                subnets=subnet_configs,
                tags=vnet_data.tags or {}
            )
            
            logger.info(f"Creating VNet: {vnet_data.vnet_name} in {location}")
            
            # Create the virtual network
            poller = self.network_client.virtual_networks.begin_create_or_update(
                resource_group_name=self.resource_group,
                virtual_network_name=vnet_data.vnet_name,
                parameters=vnet_params
            )
            
            # Wait for completion
            vnet_result = poller.result()
            
            logger.info(f"VNet created successfully: {vnet_result.id}")
            
            # Prepare response
            return self._build_vnet_response(vnet_result)
            
        except AzureError as e:
            logger.error(f"Failed to create VNet: {str(e)}")
            raise
    
    async def get_vnet(self, vnet_name: str) -> VNetResponse:
        """
        Get virtual network details.
        
        Args:
            vnet_name: Name of the virtual network
            
        Returns:
            VNetResponse with resource details
            
        Raises:
            AzureError: If retrieval fails
        """
        try:
            vnet = self.network_client.virtual_networks.get(
                resource_group_name=self.resource_group,
                virtual_network_name=vnet_name
            )
            return self._build_vnet_response(vnet)
        except AzureError as e:
            logger.error(f"Failed to get VNet {vnet_name}: {str(e)}")
            raise
    
    async def list_vnets(self) -> List[VNetResponse]:
        """
        List all virtual networks in the resource group.
        
        Returns:
            List of VNetResponse objects
        """
        try:
            vnets = self.network_client.virtual_networks.list(
                resource_group_name=self.resource_group
            )
            return [self._build_vnet_response(vnet) for vnet in vnets]
        except AzureError as e:
            logger.error(f"Failed to list VNets: {str(e)}")
            raise
    
    async def delete_vnet(self, vnet_name: str) -> bool:
        """
        Delete a virtual network.
        
        Args:
            vnet_name: Name of the virtual network to delete
            
        Returns:
            True if deletion successful
            
        Raises:
            AzureError: If deletion fails
        """
        try:
            logger.info(f"Deleting VNet: {vnet_name}")
            poller = self.network_client.virtual_networks.begin_delete(
                resource_group_name=self.resource_group,
                virtual_network_name=vnet_name
            )
            poller.result()
            logger.info(f"VNet deleted successfully: {vnet_name}")
            return True
        except AzureError as e:
            logger.error(f"Failed to delete VNet {vnet_name}: {str(e)}")
            raise
    
    def _build_vnet_response(self, vnet) -> VNetResponse:
        """Build VNetResponse from Azure VirtualNetwork object."""
        subnets = [
            SubnetResponse(
                name=subnet.name,
                address_prefix=subnet.address_prefix,
                id=subnet.id,
                provisioning_state=subnet.provisioning_state
            )
            for subnet in (vnet.subnets or [])
        ]
        
        return VNetResponse(
            vnet_name=vnet.name,
            resource_group=self.resource_group,
            location=vnet.location,
            address_space=vnet.address_space.address_prefixes or [],
            subnets=subnets,
            id=vnet.id,
            provisioning_state=vnet.provisioning_state,
            created_at=str(vnet.id.split('/')[-1]),  # Simplified timestamp
            tags=vnet.tags or {}
        )