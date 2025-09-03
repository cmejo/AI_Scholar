"""
Middleware for Zotero API authentication and credential validation
"""
import logging
from typing import Optional, Dict, Any
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from services.zotero.zotero_auth_service import ZoteroAuthService, ZoteroAuthError
from services.zotero.zotero_client import ZoteroAPIClient, ZoteroAPIError
from models.zotero_models import ZoteroConnection
from services.auth_service import AuthService

logger = logging.getLogger(__name__)

# Initialize services
zotero_auth_service = ZoteroAuthService()
auth_service = AuthService()
security = HTTPBearer()


class ZoteroAuthMiddleware:
    """Middleware for handling Zotero authentication and credential validation"""
    
    def __init__(self):
        self.zotero_auth_service = ZoteroAuthService()
        self.auth_service = AuthService()
    
    async def get_current_user(self, credentials: HTTPAuthorizationCredentials = Depends(security)):
        """
        Get current authenticated user from JWT token
        
        Args:
            credentials: HTTP Bearer credentials
            
        Returns:
            User object
            
        Raises:
            HTTPException: If authentication fails
        """
        try:
            user = await self.auth_service.verify_token(credentials.credentials)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid authentication credentials",
                    headers={"WWW-Authenticate": "Bearer"}
                )
            return user
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"}
            )
    
    async def get_zotero_connection(self, user) -> ZoteroConnection:
        """
        Get active Zotero connection for user with token validation
        
        Args:
            user: Authenticated user object
            
        Returns:
            Valid ZoteroConnection
            
        Raises:
            HTTPException: If no valid connection found
        """
        try:
            connection = await self.zotero_auth_service.get_connection_with_valid_token(user.id)
            
            if not connection:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="No active Zotero connection found. Please connect your Zotero account first."
                )
            
            return connection
            
        except ZoteroAuthError as e:
            logger.error(f"Zotero connection error for user {user.id}: {e.message}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Zotero connection error: {e.message}"
            )
        except Exception as e:
            logger.error(f"Unexpected error getting Zotero connection for user {user.id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve Zotero connection"
            )
    
    async def validate_zotero_credentials(self, connection: ZoteroConnection) -> Dict[str, Any]:
        """
        Validate Zotero credentials and return connection test results
        
        Args:
            connection: ZoteroConnection to validate
            
        Returns:
            Dictionary with validation results
            
        Raises:
            HTTPException: If validation fails
        """
        try:
            async with ZoteroAPIClient() as client:
                test_result = await client.test_connection(
                    connection.access_token,
                    connection.zotero_user_id
                )
                
                if not test_result["is_valid"]:
                    # Update connection status
                    await self.zotero_auth_service._mark_connection_error(
                        connection,
                        f"Token validation failed: {test_result.get('error', {}).get('message', 'Unknown error')}"
                    )
                    
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Zotero credentials are invalid or expired. Please reconnect your account."
                    )
                
                return test_result
                
        except ZoteroAPIError as e:
            logger.error(f"Zotero API error during validation: {e.message}")
            
            # Update connection status
            await self.zotero_auth_service._mark_connection_error(
                connection,
                f"API validation failed: {e.message}"
            )
            
            if e.status_code == 401:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Zotero credentials are invalid or expired. Please reconnect your account."
                )
            elif e.status_code == 403:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Insufficient permissions for Zotero API access."
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Zotero API is temporarily unavailable. Please try again later."
                )
        except Exception as e:
            logger.error(f"Unexpected error validating Zotero credentials: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to validate Zotero credentials"
            )
    
    async def get_validated_zotero_client(self, user) -> tuple[ZoteroAPIClient, ZoteroConnection]:
        """
        Get validated Zotero API client and connection for user
        
        Args:
            user: Authenticated user object
            
        Returns:
            Tuple of (ZoteroAPIClient, ZoteroConnection)
            
        Raises:
            HTTPException: If validation fails
        """
        # Get connection
        connection = await self.get_zotero_connection(user)
        
        # Validate credentials
        await self.validate_zotero_credentials(connection)
        
        # Return client and connection
        client = ZoteroAPIClient()
        return client, connection


# Create middleware instance
zotero_auth_middleware = ZoteroAuthMiddleware()


# Dependency functions for FastAPI
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Dependency to get current authenticated user"""
    return await zotero_auth_middleware.get_current_user(credentials)


async def get_zotero_connection(user=Depends(get_current_user)) -> ZoteroConnection:
    """Dependency to get validated Zotero connection"""
    return await zotero_auth_middleware.get_zotero_connection(user)


async def get_validated_zotero_client(user=Depends(get_current_user)) -> tuple[ZoteroAPIClient, ZoteroConnection]:
    """Dependency to get validated Zotero API client and connection"""
    return await zotero_auth_middleware.get_validated_zotero_client(user)


class ZoteroPermissionChecker:
    """Helper class for checking Zotero API permissions"""
    
    @staticmethod
    async def check_library_access(
        connection: ZoteroConnection,
        library_type: str,
        library_id: str,
        required_permission: str = "read"
    ) -> bool:
        """
        Check if connection has access to a specific library
        
        Args:
            connection: ZoteroConnection to check
            library_type: Type of library (user/group)
            library_id: Library ID
            required_permission: Required permission level
            
        Returns:
            True if access is allowed, False otherwise
        """
        try:
            async with ZoteroAPIClient() as client:
                # For user libraries, check if user_id matches
                if library_type == "user":
                    return connection.zotero_user_id == library_id
                
                # For group libraries, check group membership
                elif library_type == "group":
                    groups = await client.get_user_groups(
                        connection.access_token,
                        connection.zotero_user_id
                    )
                    
                    # Check if user is member of the group
                    group_ids = [str(group["id"]) for group in groups]
                    return library_id in group_ids
                
                return False
                
        except Exception as e:
            logger.error(f"Error checking library access: {e}")
            return False
    
    @staticmethod
    async def check_item_access(
        connection: ZoteroConnection,
        library_type: str,
        library_id: str,
        item_key: str,
        required_permission: str = "read"
    ) -> bool:
        """
        Check if connection has access to a specific item
        
        Args:
            connection: ZoteroConnection to check
            library_type: Type of library (user/group)
            library_id: Library ID
            item_key: Item key
            required_permission: Required permission level
            
        Returns:
            True if access is allowed, False otherwise
        """
        try:
            # First check library access
            has_library_access = await ZoteroPermissionChecker.check_library_access(
                connection, library_type, library_id, required_permission
            )
            
            if not has_library_access:
                return False
            
            # Try to fetch the item to verify access
            async with ZoteroAPIClient() as client:
                try:
                    await client.get_item(
                        connection.access_token,
                        library_type,
                        library_id,
                        item_key
                    )
                    return True
                except ZoteroAPIError as e:
                    if e.status_code == 404:
                        return False  # Item doesn't exist or no access
                    elif e.status_code in [401, 403]:
                        return False  # No permission
                    else:
                        raise  # Other errors should be handled upstream
                
        except Exception as e:
            logger.error(f"Error checking item access: {e}")
            return False


# Permission checker instance
permission_checker = ZoteroPermissionChecker()


async def require_library_access(
    library_type: str,
    library_id: str,
    required_permission: str = "read",
    connection: ZoteroConnection = Depends(get_zotero_connection)
) -> ZoteroConnection:
    """
    Dependency that requires library access
    
    Args:
        library_type: Type of library (user/group)
        library_id: Library ID
        required_permission: Required permission level
        connection: ZoteroConnection (injected)
        
    Returns:
        ZoteroConnection if access is allowed
        
    Raises:
        HTTPException: If access is denied
    """
    has_access = await permission_checker.check_library_access(
        connection, library_type, library_id, required_permission
    )
    
    if not has_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access denied to {library_type} library {library_id}"
        )
    
    return connection


async def require_item_access(
    library_type: str,
    library_id: str,
    item_key: str,
    required_permission: str = "read",
    connection: ZoteroConnection = Depends(get_zotero_connection)
) -> ZoteroConnection:
    """
    Dependency that requires item access
    
    Args:
        library_type: Type of library (user/group)
        library_id: Library ID
        item_key: Item key
        required_permission: Required permission level
        connection: ZoteroConnection (injected)
        
    Returns:
        ZoteroConnection if access is allowed
        
    Raises:
        HTTPException: If access is denied
    """
    has_access = await permission_checker.check_item_access(
        connection, library_type, library_id, item_key, required_permission
    )
    
    if not has_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access denied to item {item_key} in {library_type} library {library_id}"
        )
    
    return connection