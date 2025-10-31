"""
Crank Platform - Modular Monolith

This evolves the diagnostic container into a full platform with:
- Authentication service (stub)
- Billing service (stub)  
- Service discovery and worker registry
- Request routing to workers
- Original diagnostics functionality

Built with JEMM principle - clean module boundaries that can be extracted later.
"""

from typing import Dict, List, Optional, Any
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from dataclasses import dataclass, asdict
import asyncio
import json

# Import security configuration for zero-trust architecture
from security_config import SecurePlatformService

# =============================================================================
# SHARED INTERFACES (Extract-Ready)
# =============================================================================

@dataclass
@dataclass
class User:
    """User identity."""
    user_id: str
    username: str
    roles: List[str]
    tier: str = "free"
    is_active: bool = True

@dataclass
class WorkerInfo:
    """Information about a registered worker."""
    worker_id: str
    service_type: str
    endpoint: str
    health_url: str
    capabilities: List[str]
    last_seen: datetime
    load_score: float = 0.0
    
@dataclass
class UsageRecord:
    """Usage tracking record."""
    user_id: str
    operation: str
    service_type: str
    timestamp: datetime
    duration_ms: int
    tokens_used: int = 0
    cost_cents: int = 0

# =============================================================================
# SERVICE INTERFACES
# =============================================================================

class AuthServiceInterface(ABC):
    """Interface for authentication service."""
    
    @abstractmethod
    async def authenticate(self, token: str) -> Optional[User]:
        """Authenticate user from token."""
        pass
    
    @abstractmethod
    async def authorize(self, user: User, operation: str, resource: str) -> bool:
        """Check if user can perform operation on resource."""
        pass

class BillingServiceInterface(ABC):
    """Interface for billing service."""
    
    @abstractmethod
    async def track_usage(self, user_id: str, operation: str, 
                         service_type: str, duration_ms: int) -> UsageRecord:
        """Track usage and generate billing record."""
        pass
    
    @abstractmethod
    async def get_user_balance(self, user_id: str) -> Dict[str, Any]:
        """Get user's current balance and usage stats."""
        pass

class DiscoveryServiceInterface(ABC):
    """Interface for service discovery."""
    
    @abstractmethod
    async def register_worker(self, worker_info: WorkerInfo) -> bool:
        """Register a worker service."""
        pass
    
    @abstractmethod
    async def find_worker(self, service_type: str) -> Optional[WorkerInfo]:
        """Find best available worker for service type."""
        pass
    
    @abstractmethod
    async def get_workers(self) -> Dict[str, List[WorkerInfo]]:
        """Get all registered workers grouped by service type."""
        pass

# =============================================================================
# STUB IMPLEMENTATIONS (JEMM - Start Simple)
# =============================================================================

class AuthServiceStub(AuthServiceInterface):
    """Stub auth service - basic token validation."""
    
    def __init__(self):
        # In-memory user store for development
        self.users = {
            "dev-user": User("dev-user", "developer", ["admin"], "premium"),
            "test-user": User("test-user", "tester", ["user"], "free")
        }
        self.dev_tokens = {
            "dev-mesh-key": "dev-user",
            "test-key": "test-user"
        }
    
    async def authenticate(self, token: str) -> Optional[User]:
        """Authenticate using simple token lookup."""
        user_id = self.dev_tokens.get(token)
        if user_id:
            return self.users.get(user_id)
        return None
    
    async def authorize(self, user: User, operation: str, resource: str) -> bool:
        """Basic role-based authorization."""
        if "admin" in user.roles:
            return True
        if operation in ["ping", "health", "capabilities"]:
            return True
        if user.tier == "premium":
            return True
        return operation in ["ping"]  # Free tier limited

class BillingServiceStub(BillingServiceInterface):
    """Stub billing service - tracks usage but no real billing."""
    
    def __init__(self):
        self.usage_records: List[UsageRecord] = []
        self.pricing = {
            "ping": 0,  # Free
            "convert": 5,  # 5 cents
            "parse": 3,   # 3 cents
            "classify": 10  # 10 cents
        }
    
    async def track_usage(self, user_id: str, operation: str, 
                         service_type: str, duration_ms: int) -> UsageRecord:
        """Track usage and calculate cost."""
        cost_cents = self.pricing.get(operation, 1)
        
        record = UsageRecord(
            user_id=user_id,
            operation=operation,
            service_type=service_type,
            timestamp=datetime.now(timezone.utc),
            duration_ms=duration_ms,
            cost_cents=cost_cents
        )
        
        self.usage_records.append(record)
        return record
    
    async def get_user_balance(self, user_id: str) -> Dict[str, Any]:
        """Get user balance and usage summary."""
        user_records = [r for r in self.usage_records if r.user_id == user_id]
        total_cost = sum(r.cost_cents for r in user_records)
        
        return {
            "user_id": user_id,
            "total_cost_cents": total_cost,
            "total_operations": len(user_records),
            "recent_operations": len([r for r in user_records 
                                    if (datetime.now(timezone.utc) - r.timestamp).days < 1])
        }

class DiscoveryServiceStub(DiscoveryServiceInterface):
    """Stub service discovery - in-memory registry."""
    
    def __init__(self):
        self.workers: Dict[str, List[WorkerInfo]] = {}
    
    async def register_worker(self, worker_info: WorkerInfo) -> bool:
        """Register worker in memory."""
        service_type = worker_info.service_type
        if service_type not in self.workers:
            self.workers[service_type] = []
        
        # Remove existing worker with same ID
        self.workers[service_type] = [
            w for w in self.workers[service_type] 
            if w.worker_id != worker_info.worker_id
        ]
        
        # Add new/updated worker
        self.workers[service_type].append(worker_info)
        return True
    
    async def find_worker(self, service_type: str) -> Optional[WorkerInfo]:
        """Find best worker - simple round-robin for now."""
        workers = self.workers.get(service_type, [])
        if not workers:
            return None
        
        # Simple load balancing - pick least loaded
        return min(workers, key=lambda w: w.load_score)
    
    async def get_workers(self) -> Dict[str, List[WorkerInfo]]:
        """Get all workers."""
        return self.workers.copy()

# =============================================================================
# PLATFORM SERVICE
# =============================================================================

class PlatformService:
    """Main platform service - coordinates all modules."""
    
    def __init__(self, 
                 auth_service: AuthServiceInterface = None,
                 billing_service: BillingServiceInterface = None,
                 discovery_service: DiscoveryServiceInterface = None):
        self.auth = auth_service or AuthServiceStub()
        self.billing = billing_service or BillingServiceStub()
        self.discovery = discovery_service or DiscoveryServiceStub()
    
    async def authenticate_request(self, token: str) -> Optional[User]:
        """Authenticate incoming request."""
        return await self.auth.authenticate(token)
    
    async def route_request(self, service_type: str, operation: str, 
                          request_data: Dict[str, Any], user: User) -> Dict[str, Any]:
        """Route request to appropriate worker."""
        
        # Check authorization
        if not await self.auth.authorize(user, operation, service_type):
            raise ValueError(f"User {user.username} not authorized for {operation}")
        
        # Find worker
        worker = await self.discovery.find_worker(service_type)
        if not worker:
            raise ValueError(f"No workers available for {service_type}")
        
        # Actually call worker via HTTP
        start_time = datetime.now()
        
        try:
            # Import httpx for HTTP calls
            import httpx
            
            # Map operations to worker endpoints
            endpoint_map = {
                "convert": "/convert",
                "validate": "/validate"
            }
            
            worker_endpoint = endpoint_map.get(operation)
            if not worker_endpoint:
                raise ValueError(f"Unknown operation: {operation}")
            
            # Call worker
            async with httpx.AsyncClient(timeout=30.0) as client:
                url = f"{worker.endpoint}{worker_endpoint}"
                
                # For document operations, handle file data specially
                if operation == "convert" and "file" in request_data:
                    # Create form data for file upload
                    files = {"file": ("document", request_data["file"])}
                    form_data = {
                        "source_format": request_data.get("source_format", "auto"),
                        "target_format": request_data.get("target_format", "pdf")
                    }
                    
                    response = await client.post(url, files=files, data=form_data)
                else:
                    # Standard JSON request
                    response = await client.post(url, json=request_data)
                
                response.raise_for_status()
                worker_result = response.json()
                
        except Exception as e:
            # If worker call fails, return error
            end_time = datetime.now()
            duration_ms = int((end_time - start_time).total_seconds() * 1000)
            
            # Still track usage for failed requests
            usage = await self.billing.track_usage(
                user.user_id, operation, service_type, duration_ms
            )
            
            return {
                "status": "error",
                "worker_id": worker.worker_id,
                "service_type": service_type,
                "operation": operation,
                "duration_ms": duration_ms,
                "cost_cents": usage.cost_cents,
                "error": f"Worker call failed: {str(e)}"
            }
        
        end_time = datetime.now()
        duration_ms = int((end_time - start_time).total_seconds() * 1000)
        
        # Track usage for successful requests
        usage = await self.billing.track_usage(
            user.user_id, operation, service_type, duration_ms
        )
        
        return {
            "status": "success",
            "worker_id": worker.worker_id,
            "service_type": service_type,
            "operation": operation,
            "duration_ms": duration_ms,
            "cost_cents": usage.cost_cents,
            "data": worker_result
        }
    
    async def route_document_request(self, operation: str, file_content: bytes, 
                                   filename: str, source_format: str, 
                                   target_format: str, user: User) -> Dict[str, Any]:
        """Route document processing request to CrankDoc worker with HTTPS security."""
        
        # Check authorization
        if not await self.auth.authorize(user, operation, "document"):
            raise ValueError(f"User {user.username} not authorized for document {operation}")
        
        # Find document worker
        worker = await self.discovery.find_worker("document")
        if not worker:
            raise ValueError("No document workers available")
        
        start_time = datetime.now()
        
        try:
            # Initialize secure platform service
            import os
            environment = os.getenv("CRANK_ENVIRONMENT", "development")
            secure_service = SecurePlatformService(environment)
            
            # Create file-like object for upload
            from io import BytesIO
            files = {"file": (filename, BytesIO(file_content), "application/octet-stream")}
            data = {
                "source_format": source_format,
                "target_format": target_format
            }
            
            # Make secure call to worker
            response = await secure_service.secure_worker_call(
                worker.endpoint, 
                "/convert",
                files=files,
                data=data
            )
            
            worker_result = response.json()
                
        except Exception as e:
            # If worker call fails, return error
            end_time = datetime.now()
            duration_ms = int((end_time - start_time).total_seconds() * 1000)
            
            # Still track usage for failed requests
            usage = await self.billing.track_usage(
                user.user_id, operation, "document", duration_ms
            )
            
            return {
                "status": "error",
                "worker_id": worker.worker_id,
                "service_type": "document",
                "operation": operation,
                "duration_ms": duration_ms,
                "cost_cents": usage.cost_cents,
                "error": f"Document worker call failed: {str(e)}"
            }
        
        end_time = datetime.now()
        duration_ms = int((end_time - start_time).total_seconds() * 1000)
        
        # Track usage for successful requests
        usage = await self.billing.track_usage(
            user.user_id, operation, "document", duration_ms
        )
        
        return {
            "status": "success",
            "worker_id": worker.worker_id,
            "service_type": "document",
            "operation": operation,
            "duration_ms": duration_ms,
            "cost_cents": usage.cost_cents,
            "result": worker_result
        }