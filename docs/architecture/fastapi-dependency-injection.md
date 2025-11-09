# FastAPI Dependency Injection Strategy

## Overview

This document outlines the crank-platform strategy for handling FastAPI service dependencies while maintaining clean type safety and modern lifespan patterns.

## Problem Statement

### The Challenge

FastAPI modernized from deprecated `@app.on_event("startup")` patterns to `@asynccontextmanager` lifespan handlers. While architecturally superior, this creates type checking friction:

```python
# Modern lifespan pattern

@asynccontextmanager
async def lifespan(app: FastAPI):
    self.platform = PlatformService()     # Initialize during lifespan
    self.protocol = ProtocolService()
    yield
    # Cleanup

# Services defined as Optional for initialization

self.platform: Optional[PlatformService] = None

# Route handlers need services

@app.get("/endpoint")
async def handler(self):
    # ❌ Type error: "None" has no attribute "method"

    return await self.platform.method()

```

### Root Cause

Static analysis cannot understand FastAPI's runtime execution model where:

1. Lifespan runs before any route handlers

2. Services are guaranteed initialized when routes execute

3. Optional typing reflects initialization state, not runtime availability

## Solution Strategy

### Chosen Approach: Service-Level Dependency Injection

Move from instance attributes to FastAPI dependency injection with `app.state` storage:

```python
# services/dependencies.py

from fastapi import Request, Depends
from typing import cast

def get_platform_service(request: Request) -> PlatformService:
    """Get initialized platform service with type safety."""
    service = getattr(request.app.state, "platform", None)
    if service is None:
        raise RuntimeError("PlatformService not initialized")
    return cast(PlatformService, service)

# Modified lifespan - store in app.state

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.platform = PlatformService()
    app.state.protocol = ProtocolService()
    yield
    # Cleanup

# Route handlers get concrete types

@app.get("/endpoint")
async def handler(platform: PlatformService = Depends(get_platform_service)):
    # ✅ Perfect type inference, no Optional

    return await platform.method()

```

## Architecture Benefits

### Type Safety

- **Zero Optional types** in route handlers

- **Single cast location** per service (in DI function)

- **Runtime safety** via explicit initialization checks

- **Static analysis friendly** - handlers receive concrete types

### Testing Excellence

```python
# Easy service mocking in tests

def test_endpoint():
    mock_platform = MockPlatformService()
    app.state.platform = mock_platform

    with TestClient(app) as client:
        response = client.get("/endpoint")
        assert response.status_code == 200

```

### Scalability Design

#### Generic Service Helper

```python
from typing import TypeVar, Type, cast

T = TypeVar('T')

def get_service(request: Request, service_name: str, service_type: Type[T]) -> T:
    """Generic service getter - works for 1 service or 20."""
    service = getattr(request.app.state, service_name, None)
    if service is None:
        raise RuntimeError(f"{service_type.__name__} not initialized")
    return cast(service_type, service)

# Specific service getters use the generic helper

def get_platform_service(request: Request) -> PlatformService:
    return get_service(request, "platform", PlatformService)

```

## Migration Strategy

### Phase 1: Service-Level DI (Current)

**Use when**: Worker has ≤ 5 services
**Pattern**: Individual DI functions per service
**Codebase fit**: Perfect for current microservice architecture

### Phase 2: Container DI (Future)

**Migrate when**:

- Worker hits 6+ services

- Injecting 4+ services into most routes

- Services form logical clusters

**Container Pattern**:

```python
@dataclass
class ServicesContainer:
    platform: PlatformService
    protocol: ProtocolService
    discovery: DiscoveryService
    # ... other services

def get_services(request: Request) -> ServicesContainer:
    return get_service(request, "services", ServicesContainer)

# Handlers get bundled services

@app.get("/complex")
async def handler(services: ServicesContainer = Depends(get_services)):
    return await services.platform.complex_operation(services.protocol, services.discovery)

```

## Implementation Guidelines

### Service Organization by Complexity

#### Platform Service (Complex Hub)

- **Services**: 3-4 (Platform, Protocol, Discovery, Auth)

- **Pattern**: Service-level DI → Container DI when growth continues

- **Rationale**: Orchestration layer naturally more complex

#### Worker Services (Focused Components)

- **Services**: 1-2 typical (Parser + Config, Converter + Storage)

- **Pattern**: Service-level DI permanently

- **Rationale**: Microservice boundaries prevent complexity explosion

### Natural Growth Limits

The beauty of microservice architecture: when a worker becomes complex enough to need Container DI, that's the signal to split into multiple focused workers.

**Example Evolution**:

```text
EmailWorker (Simple)
├── Parser Service
└── Config Service
    ↓ (grows complex)
EmailWorker (Split Decision Point)
├── Parser Service
├── Config Service
├── Validation Service
├── Storage Service
├── Metrics Service
    ↓ (split instead of container)
EmailParserWorker        EmailStorageWorker
├── Parser Service      ├── Storage Service
└── Config Service      └── Metrics Service

```

## Error Handling Philosophy

### Progressive Type Safety

- **Perfect types where possible** (business logic)

- **Pragmatic types where necessary** (ML boundaries, external libraries)

- **Explicit runtime checks** (service initialization)

### Graceful Degradation

```python
def get_platform_service(request: Request) -> PlatformService:
    """Service getter with helpful error context."""
    service = getattr(request.app.state, "platform", None)
    if service is None:
        # Provide actionable error information

        available_services = [attr for attr in dir(request.app.state)
                            if not attr.startswith('_')]
        raise RuntimeError(
            f"PlatformService not initialized. "
            f"Available services: {available_services}. "
            f"Check lifespan startup sequence."
        )
    return cast(PlatformService, service)

```

## Comparison with Alternatives

### Why Not Global Singletons?

- Hard to test (global state)

- Import-time initialization issues

- No lifecycle management

### Why Not Class Attributes with Assertions?

```python
# Alternative: repeated assertions

async def handler(self):
    assert self.platform is not None
    assert self.protocol is not None
    return await self.platform.method()

```

- **Repetitive**: Every handler needs assertions

- **Verbose**: 14+ routes × 3 services = 42+ assert statements

- **Error-prone**: Easy to forget assertions in new routes

### Why Not Container Pattern Immediately?

- **Over-engineering**: Only 3 services currently

- **Premature optimization**: Microservices keep service counts low

- **Migration complexity**: Harder to change than add

## Testing Strategy

### Unit Testing

```python
def test_get_platform_service():
    # Mock app state

    mock_request = Mock()
    mock_request.app.state.platform = MockPlatformService()

    # Test DI function

    service = get_platform_service(mock_request)
    assert isinstance(service, MockPlatformService)

def test_get_platform_service_not_initialized():
    # Test error handling

    mock_request = Mock()
    mock_request.app.state = Mock(spec=[])  # No platform attribute

    with pytest.raises(RuntimeError, match="PlatformService not initialized"):
        get_platform_service(mock_request)

```

### Integration Testing

```python
def test_endpoint_with_services():
    with TestClient(app) as client:
        # Lifespan runs automatically, services initialized

        response = client.get("/endpoint")
        assert response.status_code == 200

def test_endpoint_with_mock_services():
    # Override services for controlled testing

    app.state.platform = MockPlatformService(return_value="test_data")

    with TestClient(app) as client:
        response = client.get("/endpoint")
        assert response.json() == {"data": "test_data"}

```

## Future Considerations

### Multi-Tenancy

```python
def get_tenant_platform_service(
    request: Request,
    tenant_id: str = Header(...)
) -> PlatformService:
    """Tenant-aware service injection."""
    services_by_tenant = getattr(request.app.state, "tenant_services", {})
    service = services_by_tenant.get(tenant_id)
    if service is None:
        raise HTTPException(404, f"Tenant {tenant_id} not found")
    return service.platform

```

### Plugin Architecture

```python
def get_plugin_registry(request: Request) -> PluginRegistry:
    """Dynamic plugin service injection."""
    return get_service(request, "plugins", PluginRegistry)

@app.get("/plugins/{plugin_name}/execute")
async def execute_plugin(
    plugin_name: str,
    registry: PluginRegistry = Depends(get_plugin_registry)
):
    plugin = await registry.get_plugin(plugin_name)
    return await plugin.execute()

```

## Conclusion

The Service-Level Dependency Injection pattern provides:

- **Immediate value**: Clean types for current 3-service platform

- **Scalability**: Generic helpers for easy Container migration

- **Maintainability**: Single responsibility per DI function

- **Testability**: Simple service mocking via app.state

- **Alignment**: Respects microservice architectural boundaries

This approach resolves the FastAPI lifespan typing issues while maintaining modern patterns and enabling future growth within the established microservice architecture.
