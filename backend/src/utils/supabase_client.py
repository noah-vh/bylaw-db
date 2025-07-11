"""
Supabase client wrapper for the Bylaw Database API.
"""
import asyncio
import logging
from typing import Optional, Dict, Any, List
from contextlib import asynccontextmanager

from supabase import create_client, Client
from supabase.client import ClientOptions
from postgrest import APIError
from gotrue.errors import AuthError

from ..config import settings

logger = logging.getLogger(__name__)


class SupabaseClient:
    """
    Wrapper around Supabase client with additional functionality.
    """
    
    def __init__(self, use_service_key: bool = False):
        """
        Initialize Supabase client.
        
        Args:
            use_service_key: Whether to use service key (for admin operations)
        """
        self.url = settings.supabase_url
        self.key = settings.supabase_service_key if use_service_key else settings.supabase_anon_key
        self.client: Optional[Client] = None
        self._is_connected = False
    
    def connect(self) -> Client:
        """Create and return Supabase client."""
        if self.client is None:
            options = ClientOptions(
                auto_refresh_token=True,
                persist_session=True,
                detect_session_in_url=True,
                headers={
                    "User-Agent": settings.scraper_user_agent
                }
            )
            
            self.client = create_client(self.url, self.key, options)
            self._is_connected = True
            logger.info("Connected to Supabase")
        
        return self.client
    
    def disconnect(self):
        """Close Supabase client connection."""
        if self.client:
            # Supabase client doesn't have explicit close method
            # but we can clear the reference
            self.client = None
            self._is_connected = False
            logger.info("Disconnected from Supabase")
    
    @property
    def is_connected(self) -> bool:
        """Check if client is connected."""
        return self._is_connected and self.client is not None
    
    async def execute_rpc(self, function_name: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """
        Execute a stored procedure/function.
        
        Args:
            function_name: Name of the RPC function
            params: Parameters to pass to the function
            
        Returns:
            Result of the function call
        """
        if not self.client:
            raise RuntimeError("Client not connected")
        
        try:
            response = self.client.rpc(function_name, params or {})
            return response.execute()
        except APIError as e:
            logger.error(f"RPC error calling {function_name}: {e}")
            raise
    
    async def get_user_info(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get user information from auth.users table.
        
        Args:
            user_id: User ID
            
        Returns:
            User information or None if not found
        """
        if not self.client:
            raise RuntimeError("Client not connected")
        
        try:
            response = self.client.auth.admin.get_user_by_id(user_id)
            return response.user.model_dump() if response.user else None
        except AuthError as e:
            logger.error(f"Auth error getting user {user_id}: {e}")
            return None
    
    async def health_check(self) -> bool:
        """
        Check if Supabase connection is healthy.
        
        Returns:
            True if healthy, False otherwise
        """
        if not self.client:
            return False
        
        try:
            # Try a simple query to verify connection
            response = self.client.table("municipalities").select("id").limit(1).execute()
            return True
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False
    
    @asynccontextmanager
    async def transaction(self):
        """
        Context manager for database transactions.
        Note: Supabase doesn't support explicit transactions in the Python client,
        so this is a placeholder for future implementation.
        """
        if not self.client:
            raise RuntimeError("Client not connected")
        
        # For now, just yield the client
        # In the future, we might implement transaction support
        yield self.client


class SupabaseManager:
    """
    Singleton manager for Supabase connections.
    """
    
    _instance: Optional['SupabaseManager'] = None
    _clients: Dict[str, SupabaseClient] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def get_client(self, use_service_key: bool = False) -> SupabaseClient:
        """
        Get or create a Supabase client.
        
        Args:
            use_service_key: Whether to use service key
            
        Returns:
            SupabaseClient instance
        """
        key = "service" if use_service_key else "anon"
        
        if key not in self._clients:
            self._clients[key] = SupabaseClient(use_service_key=use_service_key)
        
        return self._clients[key]
    
    def get_connected_client(self, use_service_key: bool = False) -> Client:
        """
        Get a connected Supabase client.
        
        Args:
            use_service_key: Whether to use service key
            
        Returns:
            Connected Supabase Client
        """
        client = self.get_client(use_service_key)
        if not client.is_connected:
            client.connect()
        return client.client
    
    def disconnect_all(self):
        """Disconnect all clients."""
        for client in self._clients.values():
            client.disconnect()
        self._clients.clear()
    
    async def health_check_all(self) -> Dict[str, bool]:
        """
        Check health of all clients.
        
        Returns:
            Dictionary with health status for each client
        """
        results = {}
        for key, client in self._clients.items():
            results[key] = await client.health_check()
        return results


# Global instance
supabase_manager = SupabaseManager()


def get_supabase_client(use_service_key: bool = False) -> Client:
    """
    Get a connected Supabase client.
    
    Args:
        use_service_key: Whether to use service key for admin operations
        
    Returns:
        Connected Supabase Client
    """
    return supabase_manager.get_connected_client(use_service_key=use_service_key)


def get_admin_client() -> Client:
    """
    Get admin Supabase client with service key.
    
    Returns:
        Connected admin Supabase Client
    """
    return get_supabase_client(use_service_key=True)