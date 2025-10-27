"""
Azure Table Storage Service.
Stores VNET resource metadata.
"""
from azure.data.tables import TableServiceClient, TableEntity
from azure.core.exceptions import ResourceNotFoundError, AzureError
from datetime import datetime
from typing import List, Dict, Optional
from app.core.config import settings
from app.schemas.network import VNetResponse, VNetListItem
import logging
import json

logger = logging.getLogger(__name__)


class StorageService:
    """Service for storing VNET metadata in Azure Table Storage."""
    
    def __init__(self):
        """Initialize Azure Table Storage client."""
        self.table_service = TableServiceClient.from_connection_string(
            conn_str=settings.AZURE_STORAGE_CONNECTION_STRING
        )
        self.table_client = self.table_service.get_table_client(
            table_name=settings.AZURE_STORAGE_TABLE_NAME
        )
        self._ensure_table_exists()
    
    def _ensure_table_exists(self):
        """Create table if it doesn't exist."""
        try:
            self.table_service.create_table(settings.AZURE_STORAGE_TABLE_NAME)
            logger.info(f"Table {settings.AZURE_STORAGE_TABLE_NAME} created")
        except AzureError:
            # Table already exists
            pass
    
    async def store_vnet(self, vnet_data: VNetResponse) -> bool:
        """
        Store VNET metadata in Table Storage.
        
        Args:
            vnet_data: Virtual network response data
            
        Returns:
            True if storage successful
        """
        try:
            entity = {
                "PartitionKey": settings.AZURE_RESOURCE_GROUP,
                "RowKey": vnet_data.vnet_name,
                "VNetName": vnet_data.vnet_name,
                "ResourceGroup": vnet_data.resource_group,
                "Location": vnet_data.location,
                "AddressSpace": json.dumps(vnet_data.address_space),
                "SubnetCount": len(vnet_data.subnets),
                "Subnets": json.dumps([
                    {
                        "name": subnet.name,
                        "address_prefix": subnet.address_prefix,
                        "id": subnet.id,
                        "provisioning_state": subnet.provisioning_state
                    }
                    for subnet in vnet_data.subnets
                ]),
                "VNetId": vnet_data.id,
                "ProvisioningState": vnet_data.provisioning_state,
                "CreatedAt": datetime.utcnow().isoformat(),
                "Tags": json.dumps(vnet_data.tags or {})
            }
            
            self.table_client.upsert_entity(entity=entity)
            logger.info(f"Stored VNet metadata: {vnet_data.vnet_name}")
            return True
            
        except AzureError as e:
            logger.error(f"Failed to store VNet metadata: {str(e)}")
            raise
    
    async def get_vnet(self, vnet_name: str) -> Optional[Dict]:
        """
        Retrieve VNET metadata from Table Storage.
        
        Args:
            vnet_name: Name of the virtual network
            
        Returns:
            VNet metadata dictionary or None if not found
        """
        try:
            entity = self.table_client.get_entity(
                partition_key=settings.AZURE_RESOURCE_GROUP,
                row_key=vnet_name
            )
            return self._entity_to_dict(entity)
        except ResourceNotFoundError:
            logger.warning(f"VNet not found in storage: {vnet_name}")
            return None
        except AzureError as e:
            logger.error(f"Failed to retrieve VNet metadata: {str(e)}")
            raise
    
    async def list_vnets(self) -> List[VNetListItem]:
        """
        List all VNET metadata from Table Storage.
        
        Returns:
            List of VNet metadata
        """
        try:
            query_filter = f"PartitionKey eq '{settings.AZURE_RESOURCE_GROUP}'"
            entities = self.table_client.query_entities(query_filter=query_filter)
            
            vnets = []
            for entity in entities:
                vnet_dict = self._entity_to_dict(entity)
                vnets.append(VNetListItem(
                    vnet_name=vnet_dict['VNetName'],
                    resource_group=vnet_dict['ResourceGroup'],
                    location=vnet_dict['Location'],
                    address_space=json.loads(vnet_dict['AddressSpace']),
                    subnet_count=vnet_dict['SubnetCount'],
                    created_at=vnet_dict['CreatedAt'],
                    id=vnet_dict['VNetId']
                ))
            
            return vnets
            
        except AzureError as e:
            logger.error(f"Failed to list VNet metadata: {str(e)}")
            raise
    
    async def delete_vnet(self, vnet_name: str) -> bool:
        """
        Delete VNET metadata from Table Storage.
        
        Args:
            vnet_name: Name of the virtual network
            
        Returns:
            True if deletion successful
        """
        try:
            self.table_client.delete_entity(
                partition_key=settings.AZURE_RESOURCE_GROUP,
                row_key=vnet_name
            )
            logger.info(f"Deleted VNet metadata: {vnet_name}")
            return True
        except ResourceNotFoundError:
            logger.warning(f"VNet not found in storage: {vnet_name}")
            return False
        except AzureError as e:
            logger.error(f"Failed to delete VNet metadata: {str(e)}")
            raise
    
    def _entity_to_dict(self, entity: TableEntity) -> Dict:
        """Convert Table Entity to dictionary."""
        return {
            "VNetName": entity.get("VNetName"),
            "ResourceGroup": entity.get("ResourceGroup"),
            "Location": entity.get("Location"),
            "AddressSpace": entity.get("AddressSpace"),
            "SubnetCount": entity.get("SubnetCount"),
            "Subnets": entity.get("Subnets"),
            "VNetId": entity.get("VNetId"),
            "ProvisioningState": entity.get("ProvisioningState"),
            "CreatedAt": entity.get("CreatedAt"),
            "Tags": entity.get("Tags")
        }