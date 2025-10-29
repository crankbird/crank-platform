# Crank Mesh Interface Design

## 🎯 Universal Service Pattern

Every Crank service follows the same mesh interface pattern, regardless of the underlying processing (document conversion, email parsing, classification, etc.).

## 🏗️ The Mesh Interface Architecture

```python
from typing import Any, Dict, Optional
from fastapi import FastAPI, UploadFile
from pydantic import BaseModel

class MeshRequest(BaseModel):
    """Universal request format for any mesh service."""
    job_id: Optional[str] = None
    service_type: str  # "document", "email", "classify", etc.
    operation: str     # "convert", "parse", "predict", etc.
    parameters: Dict[str, Any] = {}
    policy_profile: str = "default"

class MeshResponse(BaseModel):
    """Universal response format for any mesh service."""
    job_id: str
    service_type: str
    operation: str
    status: str  # "accepted", "processing", "completed", "failed"
    result: Optional[Dict[str, Any]] = None
    receipt_hash: Optional[str] = None
    processing_time_ms: Optional[int] = None

class MeshInterface:
    """Universal interface that every Crank service implements."""
    
    def __init__(self, service_type: str):
        self.service_type = service_type
        self.app = FastAPI(title=f"Crank{service_type.title()}")
        self._setup_routes()
        self._setup_middleware()
    
    def _setup_routes(self):
        """Standard routes every mesh service provides."""
        
        @self.app.post("/v1/process", response_model=MeshResponse)
        async def process_request(
            request: MeshRequest,
            file: Optional[UploadFile] = None
        ) -> MeshResponse:
            return await self.handle_request(request, file)
        
        @self.app.get("/v1/capabilities")
        async def get_capabilities():
            return await self.get_service_capabilities()
        
        @self.app.get("/v1/receipts/{job_id}")
        async def get_receipt(job_id: str):
            return await self.get_processing_receipt(job_id)
        
        @self.app.get("/health/live")
        async def health_live():
            return {"status": "alive", "service": self.service_type}
        
        @self.app.get("/health/ready")
        async def health_ready():
            return await self.check_readiness()
    
    def _setup_middleware(self):
        """Standard middleware every mesh service uses."""
        # Authentication, CORS, logging, etc.
        pass
    
    # Abstract methods each service implements
    async def handle_request(self, request: MeshRequest, file: Optional[UploadFile]) -> MeshResponse:
        raise NotImplementedError
    
    async def get_service_capabilities(self) -> Dict[str, Any]:
        raise NotImplementedError
    
    async def get_processing_receipt(self, job_id: str) -> Dict[str, Any]:
        raise NotImplementedError
    
    async def check_readiness(self) -> Dict[str, Any]:
        raise NotImplementedError
```

## 🚀 Service Implementations

### CrankDoc Mesh Interface

```python
class CrankDocService(MeshInterface):
    """Document conversion service implementing mesh interface."""
    
    def __init__(self):
        super().__init__("document")
        self.orchestrator = DocumentOrchestrator()
    
    async def handle_request(self, request: MeshRequest, file: UploadFile) -> MeshResponse:
        if request.operation == "convert":
            return await self._handle_conversion(request, file)
        else:
            raise ValueError(f"Unknown operation: {request.operation}")
    
    async def _handle_conversion(self, request: MeshRequest, file: UploadFile) -> MeshResponse:
        # Extract conversion parameters
        source_format = request.parameters.get("source_format")
        target_format = request.parameters.get("target_format")
        
        # Use existing CrankDoc orchestrator
        job_id = request.job_id or str(uuid4())
        conversion_request = ConversionRequest(
            source_format=source_format,
            target_format=target_format,
            policy_profile=request.policy_profile
        )
        
        job_meta = self.orchestrator.submit_job(
            job_id=job_id, 
            request=conversion_request, 
            upload=file
        )
        
        return MeshResponse(
            job_id=job_id,
            service_type="document",
            operation="convert",
            status="accepted"
        )
    
    async def get_service_capabilities(self) -> Dict[str, Any]:
        return {
            "service_type": "document",
            "operations": ["convert"],
            "supported_formats": {
                "input": ["md", "docx", "pdf", "html"],
                "output": ["md", "docx", "pdf", "html", "latex"]
            },
            "max_file_size": "50MB",
            "processing_time_limit": "5min"
        }
```

### CrankEmail Mesh Interface

```python
class CrankEmailService(MeshInterface):
    """Email parsing and classification service implementing mesh interface."""
    
    def __init__(self):
        super().__init__("email")
        self.classifier = EmailClassifier.load("models/email_classifier.joblib")
    
    async def handle_request(self, request: MeshRequest, file: UploadFile) -> MeshResponse:
        if request.operation == "parse":
            return await self._handle_parsing(request, file)
        elif request.operation == "classify":
            return await self._handle_classification(request, file)
        else:
            raise ValueError(f"Unknown operation: {request.operation}")
    
    async def _handle_parsing(self, request: MeshRequest, file: UploadFile) -> MeshResponse:
        # Parse mbox file using existing parser
        mbox_content = await file.read()
        
        # Use existing streaming parser
        parsed_messages = list(iter_parsed_messages(
            BytesIO(mbox_content),
            keywords=request.parameters.get("keywords"),
            body_snippet_chars=request.parameters.get("snippet_length", 200)
        ))
        
        job_id = request.job_id or str(uuid4())
        
        return MeshResponse(
            job_id=job_id,
            service_type="email",
            operation="parse",
            status="completed",
            result={
                "message_count": len(parsed_messages),
                "messages": parsed_messages[:100],  # Limit response size
                "has_more": len(parsed_messages) > 100
            }
        )
    
    async def _handle_classification(self, request: MeshRequest, file: UploadFile) -> MeshResponse:
        # Single email classification
        email_data = await file.read()
        email_text = email_data.decode('utf-8')
        
        # Extract subject and body (simplified)
        lines = email_text.split('\n')
        subject = next((line[8:] for line in lines if line.startswith('Subject:')), "")
        body = '\n'.join(lines[10:])[:500]  # First 500 chars
        
        # Use existing AI classifier
        is_receipt = self.classifier.predict(subject, body)
        confidence = self.classifier.predict_proba(subject, body)
        
        job_id = request.job_id or str(uuid4())
        
        return MeshResponse(
            job_id=job_id,
            service_type="email",
            operation="classify",
            status="completed",
            result={
                "is_receipt": is_receipt,
                "confidence": confidence,
                "subject": subject,
                "body_snippet": body[:100]
            }
        )
    
    async def get_service_capabilities(self) -> Dict[str, Any]:
        return {
            "service_type": "email",
            "operations": ["parse", "classify"],
            "supported_formats": {
                "input": ["mbox", "eml", "msg"],
                "output": ["jsonl", "json"]
            },
            "classification_models": ["receipt_detector", "invoice_detector"],
            "max_file_size": "500MB",
            "processing_time_limit": "10min"
        }
```

## 🔧 Shared Infrastructure Components

### Universal Authentication

```python
class MeshAuthMiddleware(BaseHTTPMiddleware):
    """Shared authentication for all mesh services."""
    
    async def dispatch(self, request: Request, call_next):
        # Check for API key or mesh token
        auth_header = request.headers.get("Authorization")
        
        if not auth_header or not self.validate_mesh_token(auth_header):
            return JSONResponse(
                status_code=401,
                content={"error": "Invalid mesh authentication"}
            )
        
        response = await call_next(request)
        return response
```

### Universal Policy Engine

```python
class MeshPolicyEngine:
    """Shared policy enforcement for all mesh services."""
    
    def __init__(self, opa_url: str = "http://opa:8181"):
        self.opa_url = opa_url
    
    async def evaluate_request(self, request: MeshRequest, user_context: dict) -> bool:
        """Evaluate if request is allowed by policy."""
        policy_data = {
            "service_type": request.service_type,
            "operation": request.operation,
            "parameters": request.parameters,
            "user": user_context,
            "policy_profile": request.policy_profile
        }
        
        # Query OPA for decision
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.opa_url}/v1/data/mesh/allow",
                json={"input": policy_data}
            )
            
        result = response.json()
        return result.get("result", False)
```

### Universal Receipt System

```python
class MeshReceiptSystem:
    """Shared receipt generation for all mesh services."""
    
    def generate_receipt(self, request: MeshRequest, response: MeshResponse, 
                        processing_details: dict) -> dict:
        """Generate verifiable receipt for any mesh operation."""
        receipt = {
            "job_id": response.job_id,
            "service_type": response.service_type,
            "operation": response.operation,
            "timestamp": datetime.utcnow().isoformat(),
            "input_hash": self._hash_input(request),
            "output_hash": self._hash_output(response.result),
            "processing_time_ms": response.processing_time_ms,
            "policy_profile": request.policy_profile,
            "mesh_node_id": self.get_node_id(),
            "version": "1.0"
        }
        
        # Sign receipt
        receipt["signature"] = self._sign_receipt(receipt)
        return receipt
```

## 🌐 Deployment Configuration

### Universal Docker Pattern

```dockerfile
# Base image for all mesh services
FROM python:3.12-slim as mesh-base

# Create non-root user (consistent across all services)
RUN addgroup --gid 1000 mesh && \
    adduser --uid 1000 --gid 1000 --disabled-password mesh

# Install common dependencies
RUN pip install fastapi uvicorn httpx pydantic

# Security hardening (consistent across all services)
USER mesh
WORKDIR /mesh
EXPOSE 8000

# Service-specific layers inherit from mesh-base
FROM mesh-base as crank-doc
COPY --chown=mesh:mesh ./crankdoc/ /mesh/
CMD ["uvicorn", "mesh_service:app", "--host", "0.0.0.0", "--port", "8000"]

FROM mesh-base as crank-email  
COPY --chown=mesh:mesh ./email-parser/ /mesh/
CMD ["uvicorn", "mesh_service:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Universal Kubernetes Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: crank-doc
  labels:
    app: crank-doc
    mesh.crank.ai/service-type: document
spec:
  replicas: 3
  selector:
    matchLabels:
      app: crank-doc
  template:
    metadata:
      labels:
        app: crank-doc
        mesh.crank.ai/service-type: document
    spec:
      containers:
      - name: crank-doc
        image: crank-doc:latest
        ports:
        - containerPort: 8000
        env:
        - name: MESH_SERVICE_TYPE
          value: "document"
        - name: MESH_NODE_ID
          valueFrom:
            fieldRef:
              fieldPath: metadata.name
        resources:
          requests:
            memory: "256Mi"
            cpu: "100m"
          limits:
            memory: "1Gi" 
            cpu: "500m"
        securityContext:
          runAsNonRoot: true
          runAsUser: 1000
          readOnlyRootFilesystem: true
          allowPrivilegeEscalation: false
---
apiVersion: v1
kind: Service
metadata:
  name: crank-doc-service
  labels:
    mesh.crank.ai/service-type: document
spec:
  selector:
    app: crank-doc
  ports:
  - port: 8000
    targetPort: 8000
```

## 🎯 Benefits of the Mesh Interface

1. **Unified API**: All services use the same request/response format
2. **Consistent Security**: Shared authentication, authorization, and audit
3. **Easy Integration**: Drop any service into the mesh with minimal changes
4. **Future-Proof**: Ready for distributed mesh deployment
5. **Policy Enforcement**: Centralized governance across all services
6. **Receipt System**: Verifiable audit trails for compliance
7. **Health Monitoring**: Standard health checks and readiness probes
8. **Auto-Discovery**: Services self-register capabilities

## 🚀 Migration Path

1. **Phase 1**: Wrap existing CrankDoc and email parser with mesh interface
2. **Phase 2**: Extract shared components (auth, policy, receipts)
3. **Phase 3**: Add new services using the mesh interface pattern
4. **Phase 4**: Deploy to production with service mesh (Istio/Linkerd)