# Platform Services

## Current Implementation (November 2025)

### Mesh Interface Architecture

- Universal `MeshInterface` base class with standardized patterns

- Authentication middleware with Bearer token support

- Policy enforcement engine (OPA/Rego ready)

- Receipt generation system for audit trails

- Health check endpoints and service discovery

### Production Services

- **CrankDoc Mesh Service**: Document conversion, validation, analysis

- **CrankEmail Mesh Service**: Email parsing, classification, message analysis

- **Platform Gateway**: Unified routing, capability aggregation, health monitoring

### Infrastructure Ready

- Docker containers with security hardening (non-root, read-only filesystems)

- Docker Compose orchestration for local development

- Azure Container Apps deployment strategy with auto-scaling

- Adversarial testing suite for security and performance validation

## Planned Services

- **CrankClassify**: Text and image classification

- **CrankExtract**: Entity extraction and data mining

- **CrankValidate**: Schema validation and data quality

- **CrankRoute**: API gateway and transformation

- **CrankAnalyze**: Data analytics and insights

## The Universal Pattern

Every service follows the same architecture:

```python
@crank_service
def process_transaction(input_data, policies, context):
    # Your original Python logic here

    result = do_something(input_data)
    return result

# Automatically gets

# - FastAPI endpoint with authentication

# - Security isolation in containers

# - Audit logging and receipts

# - Policy enforcement via OPA/Rego

# - Chargeback tracking

# - Multi-deployment options (laptop to cloud)

```

## Service Categories

### Document Processing Services

**CrankDoc** - Document conversion and analysis

```python
class CrankDoc(MeshInterface):
    """Universal document processing service."""

    def convert_document(self, input_doc: bytes, target_format: str) -> bytes:
        """Convert documents between formats (PDF, DOCX, HTML, etc.)."""
        return self.pandoc_converter.convert(input_doc, target_format)

    def analyze_document(self, document: bytes) -> Dict:
        """Extract metadata, structure, and content analysis."""
        return {
            "metadata": self.extract_metadata(document),
            "structure": self.analyze_structure(document),
            "content_analysis": self.analyze_content(document)
        }

```

**CrankEmail** - Email archive processing

```python
class CrankEmail(MeshInterface):
    """Email parsing and classification service."""

    def parse_mbox(self, mbox_data: bytes) -> List[Dict]:
        """Parse mbox format email archives."""
        return self.mbox_parser.parse(mbox_data)

    def classify_email(self, email_content: str) -> Dict:
        """Classify email type, priority, and content."""
        return self.classifier.predict(email_content)

```

### AI and Classification Services

**CrankClassify** - Universal classification

```python
class CrankClassify(MeshInterface):
    """Text and image classification service."""

    def classify_text(self, text: str, categories: List[str]) -> Dict:
        """Classify text into provided categories."""
        return self.text_classifier.predict(text, categories)

    def classify_image(self, image: bytes, model_type: str = "general") -> Dict:
        """Classify images using specified model."""
        return self.image_classifier.predict(image, model_type)

```

**CrankExtract** - Entity and data extraction

```python
class CrankExtract(MeshInterface):
    """Entity extraction and data mining."""

    def extract_entities(self, text: str, entity_types: List[str]) -> Dict:
        """Extract named entities from text."""
        return self.ner_model.extract(text, entity_types)

    def extract_structured_data(self, document: bytes) -> Dict:
        """Extract tables, forms, and structured data."""
        return self.structure_extractor.extract(document)

```

### Validation and Quality Services

**CrankValidate** - Data validation and quality

```python
class CrankValidate(MeshInterface):
    """Schema validation and data quality service."""

    def validate_schema(self, data: Dict, schema: Dict) -> Dict:
        """Validate data against JSON schema."""
        return self.schema_validator.validate(data, schema)

    def check_data_quality(self, dataset: List[Dict]) -> Dict:
        """Analyze data quality metrics."""
        return self.quality_checker.analyze(dataset)

```

## Service Discovery and Registration

### Automatic Registration

```python
class ServiceRegistry:
    """Automatic service discovery and registration."""

    def register_service(self, service_info: Dict):
        """Register service with platform."""
        self.registry[service_info["name"]] = {
            "url": service_info["url"],
            "capabilities": service_info["capabilities"],
            "health_check": service_info["health_check"],
            "last_seen": datetime.now()
        }

    def discover_services(self, capability: str) -> List[Dict]:
        """Find services with specific capability."""
        return [
            service for service in self.registry.values()
            if capability in service["capabilities"]
        ]

```

### Health Monitoring

```python
class HealthMonitor:
    """Monitor service health and availability."""

    async def check_service_health(self, service_url: str) -> Dict:
        """Check if service is healthy and responsive."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{service_url}/health/live")
                return {
                    "status": "healthy" if response.status_code == 200 else "unhealthy",
                    "response_time": response.elapsed.total_seconds(),
                    "last_check": datetime.now()
                }
        except Exception as e:
            return {"status": "unreachable", "error": str(e)}

```

## Economic Model

### Pay-Per-Use Architecture

Each service tracks usage and generates receipts:

```python
class UsageTracker:
    """Track service usage for billing."""

    def record_transaction(self, service: str, operation: str,
                          input_size: int, processing_time: float):
        """Record billable transaction."""
        cost = self.calculate_cost(operation, input_size, processing_time)

        receipt = {
            "transaction_id": str(uuid.uuid4()),
            "service": service,
            "operation": operation,
            "input_size_bytes": input_size,
            "processing_time_ms": processing_time * 1000,
            "cost_credits": cost,
            "timestamp": datetime.now().isoformat()
        }

        self.audit_logger.log_transaction(receipt)
        return receipt

```

### Resource Optimization

Services automatically optimize for available hardware:

```python
class ResourceOptimizer:
    """Optimize service performance for available resources."""

    def optimize_for_hardware(self, model_config: Dict) -> Dict:
        """Adjust model configuration for current hardware."""
        gpu_memory = self.get_available_gpu_memory()
        cpu_cores = self.get_cpu_core_count()

        if gpu_memory > 8000:  # 8GB+ GPU
            return {"batch_size": 32, "precision": "float16", "device": "cuda"}
        elif gpu_memory > 4000:  # 4-8GB GPU
            return {"batch_size": 16, "precision": "float16", "device": "cuda"}
        else:  # CPU only
            return {"batch_size": 8, "precision": "float32", "device": "cpu"}

```

## Deployment Patterns

### Local Development

```bash
# Start all services locally

docker compose -f docker-compose.development.yml up

# Services available at

# - CrankDoc: http://localhost:8000

# - CrankEmail: http://localhost:8001

# - Gateway: http://localhost:8080

```

### Production Cloud

```yaml
# kubernetes/crank-platform.yaml

apiVersion: apps/v1
kind: Deployment
metadata:
  name: crank-doc-service
spec:
  replicas: 3
  selector:
    matchLabels:
      app: crank-doc
  template:
    metadata:
      labels:
        app: crank-doc
    spec:
      containers:

      - name: crank-doc
        image: crank-platform/doc-service:latest
        ports:

        - containerPort: 8000
        env:

        - name: CRANK_ENVIRONMENT
          value: "production"

```

### Edge Deployment

```bash
# Single container on edge device

docker run -d \
  --name crank-platform \
  -p 8080:8080 \
  -v /data:/app/data \
  crank-platform/gateway:latest

```

This unified architecture enables the same services to run efficiently from laptop development to cloud production to edge devices.
