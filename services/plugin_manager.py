"""
Platform Plugin Manager

Integrates the plugin architecture with the platform's governance layer.
Handles plugin lifecycle, routing, and compatibility.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

from plugin_architecture import (
    PlatformPlugin, PluginRegistry, PluginRequest, PluginResponse, 
    PluginMetadata, CrankDocPlugin
)

logger = logging.getLogger(__name__)


class PluginManager:
    """Manages plugins within the platform governance layer."""
    
    def __init__(self):
        self.registry = PluginRegistry()
        self.loaded_plugins: Dict[str, PlatformPlugin] = {}
        
    async def initialize_plugins(self, plugin_configs: Dict[str, Dict[str, Any]]):
        """Initialize plugins from configuration."""
        
        for plugin_name, config in plugin_configs.items():
            try:
                if plugin_name == "crankdoc":
                    plugin = CrankDocPlugin(
                        crankdoc_service_url=config.get("service_url", "http://crankdoc:8000")
                    )
                elif plugin_name == "crankemail":
                    # Future: CrankEmailPlugin(config)
                    logger.info(f"CrankEmail plugin not yet implemented")
                    continue
                else:
                    logger.warning(f"Unknown plugin type: {plugin_name}")
                    continue
                
                # Register plugin
                if self.registry.register_plugin(plugin):
                    self.loaded_plugins[plugin_name] = plugin
                    logger.info(f"Successfully loaded plugin: {plugin_name}")
                else:
                    logger.error(f"Failed to register plugin: {plugin_name}")
                    
            except Exception as e:
                logger.error(f"Failed to initialize plugin {plugin_name}: {e}")
    
    async def route_to_plugin(self, service_type: str, operation: str, 
                            data: Dict[str, Any], request_id: str) -> PluginResponse:
        """Route request to appropriate plugin."""
        
        # Map service types to plugin names
        service_to_plugin = {
            "document": "crankdoc",
            "email": "crankemail"
        }
        
        plugin_name = service_to_plugin.get(service_type)
        if not plugin_name:
            raise ValueError(f"No plugin available for service type: {service_type}")
        
        plugin = self.loaded_plugins.get(plugin_name)
        if not plugin:
            raise ValueError(f"Plugin not loaded: {plugin_name}")
        
        # Create plugin request
        request = PluginRequest(
            operation=operation,
            data=data,
            request_id=request_id
        )
        
        # Process through plugin
        response = await plugin.process(request)
        return response
    
    async def get_plugin_capabilities(self) -> Dict[str, PluginMetadata]:
        """Get capabilities of all loaded plugins."""
        capabilities = {}
        
        for name, plugin in self.loaded_plugins.items():
            try:
                metadata = plugin.get_metadata()
                capabilities[name] = metadata
            except Exception as e:
                logger.error(f"Failed to get capabilities for {name}: {e}")
        
        return capabilities
    
    async def health_check_plugins(self) -> Dict[str, Dict[str, Any]]:
        """Check health of all loaded plugins."""
        health_status = {}
        
        for name, plugin in self.loaded_plugins.items():
            try:
                health = await plugin.health_check()
                health_status[name] = health
            except Exception as e:
                health_status[name] = {"status": "error", "error": str(e)}
        
        return health_status
    
    def list_available_plugins(self) -> List[str]:
        """List names of all loaded plugins."""
        return list(self.loaded_plugins.keys())


# Platform integration example
class PlatformWithPlugins:
    """Enhanced platform service with plugin support."""
    
    def __init__(self):
        self.plugin_manager = PluginManager()
        
    async def initialize(self):
        """Initialize platform with plugins."""
        
        # Plugin configuration 
        plugin_configs = {
            "crankdoc": {
                "service_url": "http://crankdoc-service:8000"  # Real CrankDoc service
            },
            # "crankemail": {
            #     "service_url": "http://crankemail-service:8000"
            # }
        }
        
        await self.plugin_manager.initialize_plugins(plugin_configs)
    
    async def route_request_via_plugins(self, service_type: str, operation: str, 
                                      data: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Route request through plugin architecture."""
        
        request_id = f"{user_id}-{datetime.now().isoformat()}"
        
        try:
            # Route to plugin
            response = await self.plugin_manager.route_to_plugin(
                service_type, operation, data, request_id
            )
            
            return {
                "status": "success" if response.success else "error",
                "data": response.data,
                "error": response.error,
                "duration_ms": response.duration_ms,
                "worker_id": response.worker_id,
                "plugin_architecture": True
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": f"Plugin routing failed: {str(e)}",
                "plugin_architecture": True
            }