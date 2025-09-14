"""
Conditional Importer utility for safe service imports
"""
import logging
import importlib
import time
from typing import Any, Optional, Callable, Dict
from functools import wraps

logger = logging.getLogger(__name__)


class ImportError(Exception):
    """Custom exception for import errors"""
    pass


class ConditionalImporter:
    """
    Utility class for safely importing modules and services with fallback mechanisms
    """
    
    _import_cache: Dict[str, Any] = {}
    _failed_imports: Dict[str, str] = {}
    
    @staticmethod
    def safe_import(
        module_name: str, 
        fallback: Any = None, 
        attribute: str = None,
        cache: bool = True
    ) -> Any:
        """
        Safely import a module or attribute with fallback
        
        Args:
            module_name: Name of the module to import
            fallback: Fallback value if import fails
            attribute: Specific attribute to import from module
            cache: Whether to cache successful imports
            
        Returns:
            Imported module/attribute or fallback value
        """
        cache_key = f"{module_name}.{attribute}" if attribute else module_name
        
        # Check cache first
        if cache and cache_key in ConditionalImporter._import_cache:
            logger.debug(f"Using cached import for {cache_key}")
            return ConditionalImporter._import_cache[cache_key]
        
        # Check if this import previously failed
        if cache_key in ConditionalImporter._failed_imports:
            logger.debug(f"Skipping previously failed import: {cache_key}")
            return fallback
        
        try:
            logger.debug(f"Attempting to import: {module_name}")
            module = importlib.import_module(module_name)
            
            if attribute:
                if hasattr(module, attribute):
                    result = getattr(module, attribute)
                    logger.info(f"Successfully imported {attribute} from {module_name}")
                else:
                    raise ImportError(f"Attribute {attribute} not found in {module_name}")
            else:
                result = module
                logger.info(f"Successfully imported module: {module_name}")
            
            # Cache successful import
            if cache:
                ConditionalImporter._import_cache[cache_key] = result
            
            return result
            
        except Exception as e:
            error_msg = f"Failed to import {cache_key}: {str(e)}"
            logger.warning(error_msg)
            
            # Cache failed import to avoid repeated attempts
            ConditionalImporter._failed_imports[cache_key] = error_msg
            
            return fallback
    
    @staticmethod
    def import_with_retry(
        module_name: str, 
        max_retries: int = 3, 
        retry_delay: float = 1.0,
        attribute: str = None,
        fallback: Any = None
    ) -> Any:
        """
        Import with retry logic for transient failures
        
        Args:
            module_name: Name of the module to import
            max_retries: Maximum number of retry attempts
            retry_delay: Delay between retries in seconds
            attribute: Specific attribute to import from module
            fallback: Fallback value if all retries fail
            
        Returns:
            Imported module/attribute or fallback value
        """
        cache_key = f"{module_name}.{attribute}" if attribute else module_name
        
        for attempt in range(max_retries + 1):
            try:
                logger.debug(f"Import attempt {attempt + 1}/{max_retries + 1} for {cache_key}")
                
                module = importlib.import_module(module_name)
                
                if attribute:
                    if hasattr(module, attribute):
                        result = getattr(module, attribute)
                        logger.info(f"Successfully imported {attribute} from {module_name} on attempt {attempt + 1}")
                    else:
                        raise ImportError(f"Attribute {attribute} not found in {module_name}")
                else:
                    result = module
                    logger.info(f"Successfully imported module {module_name} on attempt {attempt + 1}")
                
                # Cache successful import
                ConditionalImporter._import_cache[cache_key] = result
                return result
                
            except Exception as e:
                error_msg = f"Import attempt {attempt + 1} failed for {cache_key}: {str(e)}"
                logger.warning(error_msg)
                
                if attempt < max_retries:
                    logger.info(f"Retrying import of {cache_key} in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                else:
                    logger.error(f"All import attempts failed for {cache_key}")
                    ConditionalImporter._failed_imports[cache_key] = error_msg
        
        return fallback
    
    @staticmethod
    def import_service_class(
        module_name: str, 
        class_name: str, 
        fallback_class: type = None
    ) -> Optional[type]:
        """
        Import a service class with fallback
        
        Args:
            module_name: Name of the module containing the service class
            class_name: Name of the service class
            fallback_class: Fallback class if import fails
            
        Returns:
            Service class or fallback class
        """
        return ConditionalImporter.safe_import(
            module_name=module_name,
            attribute=class_name,
            fallback=fallback_class
        )
    
    @staticmethod
    def clear_cache():
        """Clear the import cache"""
        ConditionalImporter._import_cache.clear()
        logger.info("Import cache cleared")
    
    @staticmethod
    def clear_failed_imports():
        """Clear the failed imports cache"""
        ConditionalImporter._failed_imports.clear()
        logger.info("Failed imports cache cleared")
    
    @staticmethod
    def get_cache_info() -> Dict[str, Any]:
        """
        Get information about cached imports
        
        Returns:
            Dict containing cache information
        """
        return {
            "cached_imports": list(ConditionalImporter._import_cache.keys()),
            "failed_imports": dict(ConditionalImporter._failed_imports),
            "cache_size": len(ConditionalImporter._import_cache),
            "failed_count": len(ConditionalImporter._failed_imports)
        }


def conditional_import(
    module_name: str, 
    fallback: Any = None, 
    attribute: str = None,
    max_retries: int = 0,
    retry_delay: float = 1.0
):
    """
    Decorator for conditional imports
    
    Args:
        module_name: Name of the module to import
        fallback: Fallback value if import fails
        attribute: Specific attribute to import from module
        max_retries: Maximum number of retry attempts
        retry_delay: Delay between retries in seconds
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            if max_retries > 0:
                imported = ConditionalImporter.import_with_retry(
                    module_name=module_name,
                    max_retries=max_retries,
                    retry_delay=retry_delay,
                    attribute=attribute,
                    fallback=fallback
                )
            else:
                imported = ConditionalImporter.safe_import(
                    module_name=module_name,
                    attribute=attribute,
                    fallback=fallback
                )
            
            # Add imported module/attribute to kwargs
            kwargs['imported'] = imported
            return func(*args, **kwargs)
        
        return wrapper
    return decorator


def require_service(service_name: str, fallback_response: Any = None):
    """
    Decorator to require a service for endpoint execution
    
    Args:
        service_name: Name of the required service
        fallback_response: Response to return if service is not available
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            from .service_manager import service_manager
            
            if not service_manager.is_service_healthy(service_name):
                logger.warning(f"Service {service_name} not available for endpoint {func.__name__}")
                if fallback_response is not None:
                    return fallback_response
                else:
                    from fastapi import HTTPException
                    raise HTTPException(
                        status_code=503,
                        detail=f"Service {service_name} is not available"
                    )
            
            # Add service instance to kwargs
            kwargs['service'] = service_manager.get_service(service_name)
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator