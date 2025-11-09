# Crank Platform Mesh Services

This directory contains the implementation of the Crank Platform mesh interface and services. The mesh interface provides a unified API pattern that all Crank services implement, enabling consistent security, governance, and integration.

## 🏗️ Architecture

```text
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Gateway       │───▶│   CrankDoc      │    │   CrankEmail    │
│   :8080         │    │   :8000         │    │   :8001         │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Mesh          │    │   Document      │    │   Email         │
│   Interface     │    │   Processing    │    │   Processing    │
└─────────────────┘    └─────────────────┘    └─────────────────┘

```

## 📋 Services

### Gateway (`gateway.py`)

- **Port**: 8080

- **Purpose**: Unified entry point for all mesh services

- **Features**: Request routing, service discovery, health aggregation

### CrankDoc Mesh Service (`crankdoc_mesh.py`)

- **Port**: 8000

- **Purpose**: Document conversion and processing

- **Operations**: `convert`, `validate`, `analyze`

- **Formats**: Markdown, DOCX, PDF, HTML, LaTeX, TXT

### CrankEmail Mesh Service (`crankemail_mesh.py`)

- **Port**: 8001

- **Purpose**: Email parsing and classification

- **Operations**: `parse`, `classify`, `analyze`, `extract`

- **Formats**: MBOX, EML, MSG, TXT

### Mesh Interface (`mesh_interface.py`)

- **Purpose**: Universal base class for all mesh services

- **Features**: Authentication, policy enforcement, receipts, health checks

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt

```

### 2. Run Services Locally

```bash
# Terminal 1: CrankDoc service

python crankdoc_mesh.py

# Terminal 2: CrankEmail service

python crankemail_mesh.py

# Terminal 3: Gateway

python gateway.py

```

### 3. Test Services

```bash
python test_mesh.py

```

### 4. Run with Docker Compose

```bash
docker-compose up --build

```

## 📡 API Reference

### Universal Mesh Interface

All services implement the same interface:

#### POST `/v1/process`

Process a request through the mesh service.

**Form Parameters:**

- `service_type`: Service to use (`document`, `email`)

- `operation`: Operation to perform (`convert`, `parse`, `classify`, etc.)

- `job_id`: Optional job identifier

- `policy_profile`: Policy profile to apply (default: `default`)

- `parameters`: JSON string with operation-specific parameters

- `file`: File to process (multipart upload)

**Response:**

```json
{
  "job_id": "uuid",
  "service_type": "document|email",
  "operation": "convert|parse|etc",
  "status": "accepted|processing|completed|failed",
  "result": {...},
  "receipt_hash": "hash",
  "processing_time_ms": 123,
  "mesh_node_id": "node-id"
}

```

#### GET `/v1/capabilities`

Get service capabilities and supported operations.

#### GET `/v1/receipts/{job_id}`

Get verifiable processing receipt for a job.

#### GET `/health/live`

Basic liveness check.

#### GET `/health/ready`

Detailed readiness check including dependencies.

## 🔧 Configuration

### Environment Variables

- `MESH_SERVICE_TYPE`: Type of service (`document`, `email`)

- `MESH_NODE_ID`: Unique node identifier

- `MESH_GATEWAY`: Set to `true` for gateway mode

### Authentication

Services use Bearer token authentication:

```bash
curl -H "Authorization: Bearer dev-mesh-key" \
     http://localhost:8080/v1/capabilities

```

## 🧪 Testing

### Manual Testing

```bash
# Test document validation

curl -X POST http://localhost:8080/v1/process \
  -H "Authorization: Bearer dev-mesh-key" \
  -F "service_type=document" \
  -F "operation=validate" \
  -F "parameters={}" \
  -F "file=@test.md"

# Test email classification

curl -X POST http://localhost:8080/v1/process \
  -H "Authorization: Bearer dev-mesh-key" \
  -F "service_type=email" \
  -F "operation=classify" \
  -F "parameters={}" \
  -F "file=@receipt.eml"

```

### Automated Testing

```bash
python test_mesh.py

```

## 🔒 Security Features

- **Authentication**: Bearer token authentication on all endpoints

- **Authorization**: Policy-based access control (OPA integration planned)

- **Audit**: Verifiable receipts for all processing

- **Isolation**: Container-based service isolation

- **Non-root**: All services run as non-root users

## 📊 Monitoring

### Health Checks

- **Liveness**: Basic service availability

- **Readiness**: Service and dependency health

- **Gateway**: Aggregated health of all services

### Metrics (Planned)

- Request count and latency

- Processing time per operation

- Error rates by service

- Queue length and throughput

## 🛠️ Development

### Adding a New Service

1. Create service class inheriting from `MeshInterface`

2. Implement required methods:

   - `handle_request()`

   - `get_service_capabilities()`

   - `get_processing_receipt()`

   - `check_readiness()`

3. Add service to gateway registry

4. Create Dockerfile and update docker-compose.yml

### Example Service

```python
from mesh_interface import MeshInterface, MeshRequest, MeshResponse

class MyMeshService(MeshInterface):
    def __init__(self):
        super().__init__("myservice")

    async def handle_request(self, request: MeshRequest, file) -> MeshResponse:
        # Implement your processing logic

        return MeshResponse(
            job_id=request.job_id,
            service_type=self.service_type,
            operation=request.operation,
            status="completed",
            result={"message": "Hello from my service!"}
        )

    # Implement other required methods...

```

## 🚀 Deployment

### Local Development

```bash
docker-compose up

```

### Production (Azure Container Apps)

```bash
# TODO: Add Azure deployment instructions

```

### Kubernetes

```bash
# TODO: Add Kubernetes manifests

```

## 🔮 Roadmap

- [ ] **Policy Engine**: OPA/Rego integration for governance

- [ ] **Service Discovery**: Automatic service registration

- [ ] **Load Balancing**: Multiple instances per service type

- [ ] **Metrics**: Prometheus/Grafana monitoring

- [ ] **Tracing**: Distributed tracing with Jaeger

- [ ] **Message Queue**: Async processing with Redis/RabbitMQ

- [ ] **AI Integration**: Direct AI model serving

- [ ] **Mesh Networking**: Service mesh with Istio/Linkerd

## 🤝 Contributing

1. Fork the repository

2. Create a feature branch

3. Implement your changes

4. Add tests

5. Create a pull request

## 📚 Related Documentation

- [Platform Vision](../README.md)

- [Mesh Interface Design](../mesh-interface-design.md)

- [CrankDoc Documentation](../../crankdoc/README.md)

- [Email Parser Documentation](../../parse-email-archive/README.md)
