"""
Crank Platform Plugin Architecture

Defines the interface for integrating standalone worker services
(like CrankDoc, CrankEmail) into the governance platform.

This enables:
- Clean separation: governance (platform) vs. business logic (workers)
- Independent development of worker modules
- Versioned plugin compatibility
- Drop-in/plug-in capability
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from pydantic import BaseModel
from datetime import datetime


class PluginCapability(BaseModel):
    """Describes what a plugin can do."""
    operation: str
    description: str
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]
    version: str
    

class PluginMetadata(BaseModel):
    """Plugin identification and compatibility info."""
    name: str
    version: str
    description: str
    author: str
    platform_version_min: str
    platform_version_max: str
    capabilities: List[PluginCapability]
    health_endpoint: str
    

class PluginRequest(BaseModel):
    """Standard request format for all plugins."""
    operation: str
    data: Dict[str, Any]
    metadata: Optional[Dict[str, Any]] = None
    request_id: str
    

class PluginResponse(BaseModel):
    """Standard response format from all plugins."""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    request_id: str
    duration_ms: int
    worker_id: str


class PlatformPlugin(ABC):
    """Abstract base class for platform plugins."""
    
    @abstractmethod
    def get_metadata(self) -> PluginMetadata:
        """Return plugin metadata and capabilities."""
        pass
    
    @abstractmethod
    async def process(self, request: PluginRequest) -> PluginResponse:
        """Process a request using the plugin's business logic."""
        pass
    
    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """Return plugin health status."""
        pass
    

class PluginRegistry:
    """Registry for managing platform plugins."""
    
    def __init__(self):
        self.plugins: Dict[str, PlatformPlugin] = {}
    
    def register_plugin(self, plugin: PlatformPlugin) -> bool:
        """Register a plugin with the platform."""
        metadata = plugin.get_metadata()
        
        # Version compatibility check
        if not self._is_compatible(metadata):
            return False
            
        self.plugins[metadata.name] = plugin
        return True
    
    def get_plugin(self, name: str) -> Optional[PlatformPlugin]:
        """Get a registered plugin by name."""
        return self.plugins.get(name)
    
    def list_plugins(self) -> List[PluginMetadata]:
        """List all registered plugins."""
        return [plugin.get_metadata() for plugin in self.plugins.values()]
    
    def _is_compatible(self, metadata: PluginMetadata) -> bool:
        """Check if plugin is compatible with current platform version."""
        # TODO: Implement semantic version checking
        return True


# Example: CrankDoc Plugin Implementation
class CrankDocPlugin(PlatformPlugin):
    """Plugin adapter for CrankDoc service."""
    
    def __init__(self, crankdoc_service_url: str):
        self.service_url = crankdoc_service_url
        self.worker_id = f"crankdoc-plugin-{datetime.now().strftime('%Y%m%d')}"
    
    def get_metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="crankdoc",
            version="1.0.0",
            description="Document conversion and processing",
            author="CrankDoc Team",
            platform_version_min="1.0.0",
            platform_version_max="2.0.0",
            capabilities=[
                PluginCapability(
                    operation="convert",
                    description="Convert documents between formats",
                    input_schema={
                        "type": "object",
                        "properties": {
                            "file": {"type": "string", "format": "binary"},
                            "source_format": {"type": "string"},
                            "target_format": {"type": "string"}
                        }
                    },
                    output_schema={
                        "type": "object", 
                        "properties": {
                            "converted_file": {"type": "string", "format": "binary"},
                            "metadata": {"type": "object"}
                        }
                    },
                    version="1.0.0"
                )
            ],
            health_endpoint="/health"
        )
    
    async def process(self, request: PluginRequest) -> PluginResponse:
        """Forward request to actual CrankDoc service."""
        start_time = datetime.now()
        
        try:
            # Call real CrankDoc service
            import httpx
            async with httpx.AsyncClient() as client:
                # Forward to actual CrankDoc API
                response = await client.post(
                    f"{self.service_url}/api/convert",
                    json=request.dict()
                )
                response.raise_for_status()
                result = response.json()
            
            duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            
            return PluginResponse(
                success=True,
                data=result,
                request_id=request.request_id,
                duration_ms=duration_ms,
                worker_id=self.worker_id
            )
            
        except Exception as e:
            duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            
            return PluginResponse(
                success=False,
                error=str(e),
                request_id=request.request_id,
                duration_ms=duration_ms,
                worker_id=self.worker_id
            )
    
    async def health_check(self) -> Dict[str, Any]:
        """Check if CrankDoc service is healthy."""
        try:
            import httpx
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.service_url}/health")
                return response.json()
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}