# Crank Platform Requirements

## 🏗️ Core Architecture Requirements

### JEMM Principle Compliance

- **Modular Monolith Design**: Clean internal boundaries with extract-ready interfaces
- **Constraint-Driven Decisions**: Extract services only when measurements prove necessity
- **Reversible Architecture**: Can consolidate back to monolith if microservices add complexity
- **Business Value Focus**: Architecture serves product goals, not resume building

### Three-Tier Architecture

- **IaaS Layer**: Environment provisioning and infrastructure (crank-infrastructure)
- **PaaS Layer**: Platform services, mesh, governance (crank-platform)
- **SaaS Layer**: Business applications and AI services (crankdoc, parse-email-archive)

## 🔌 Universal Protocol Support (Critical Innovation)

**REQUIREMENT**: The platform MUST support multiple communication protocols through a unified mesh interface.

### Protocol Adapter Architecture

```
Protocol Input → Adapter → MeshInterface → Business Logic → Adapter → Protocol Output
     ↓              ↓           ↓              ↓            ↓           ↓
   [REST]       [RESTAdapter] [Universal]  [Any Service] [RESTAdapter] [JSON]
   [gRPC]       [gRPCAdapter]    API       [Document]    [gRPCAdapter] [Proto]
   [MCP]        [MCPAdapter]               [Email]       [MCPAdapter]  [JSON-RPC]
   [RS422]      [RS422Adapter]             [Diagnostic]  [RS422Adapter][Binary]
```

### Supported Protocols (Minimum)

1. **REST API** - Standard HTTP/JSON for web integration
2. **MCP (Model Context Protocol)** - AI agent discovery and tool usage  
3. **gRPC** - High-performance binary protocol for services
4. **Legacy Protocol Framework** - Extensible for industrial protocols (RS422, Modbus, etc.)

### Protocol-Agnostic Benefits

- **Future-Proof**: New protocols can be added without changing business logic
- **Legacy Integration**: Industrial systems can connect via their native protocols
- **AI Agent Ready**: MCP enables automatic service discovery by AI agents
- **Performance Optimization**: Use optimal protocol per use case (gRPC for speed, REST for simplicity)

## 🔐 Security Requirements

### Authentication & Authorization

- **Multi-tier Auth**: Support for API keys, JWT tokens, role-based access
- **Per-Protocol Security**: Each protocol adapter handles its security model
- **Audit Trail**: All requests logged with user, operation, cost tracking

### Policy Enforcement

- **OPA/Rego Integration**: Policy-as-code for governance
- **Resource Limits**: Per-user quotas and rate limiting
- **Security Receipts**: Cryptographic proof of processing for compliance

## 📊 Economic Layer Requirements

### Usage Tracking & Billing

- **Granular Metering**: Track compute time, tokens, operations per user
- **Multi-currency Support**: Traditional payments + cryptocurrency settlement
- **Performance-based Pricing**: Cost adjustments based on SLA delivery
- **Economic Routing**: Route requests based on cost/performance tradeoffs

### Agent Economy Integration

- **Service Discovery**: Workers advertise capabilities and pricing
- **Autonomous Negotiation**: Services negotiate pricing and SLAs
- **Reputation System**: Track service quality and reliability metrics

## 🔧 Platform Services Requirements

### Service Mesh Capabilities

- **Worker Registration**: Dynamic service discovery and health checking
- **Load Balancing**: Intelligent routing based on worker capacity
- **Circuit Breakers**: Fault tolerance and graceful degradation
- **Request Routing**: Route operations to appropriate service types

### Observability & Monitoring

- **Health Endpoints**: Liveness and readiness checks
- **Metrics Collection**: Performance, usage, and error rate tracking
- **Distributed Tracing**: Request flow tracking across services
- **Log Aggregation**: Centralized logging with correlation IDs

## 🏭 Worker Service Requirements

### Worker Container Pattern

- **Stateless Design**: Workers should be pure business logic
- **Platform Registration**: Auto-register capabilities with platform on startup
- **Health Reporting**: Periodic health and capacity reporting
- **Graceful Shutdown**: Handle termination signals properly

### Supported Service Types (Minimum)

1. **Document Processing** (CrankDoc) - Convert, validate, analyze documents
2. **Email Processing** (CrankEmail) - Parse, classify, extract from email archives
3. **AI Classification** (CrankClassify) - Text and image classification services
4. **Data Extraction** (CrankExtract) - Entity extraction and data mining

## 🌐 Deployment Requirements

### Container Orchestration

- **Docker Compose**: Local development and testing
- **Kubernetes Ready**: Production deployment with auto-scaling
- **Multi-cloud Support**: Azure, AWS, GCP deployment strategies
- **Edge Deployment**: Support for gaming laptops and mobile devices

### Development Environment

- **Hot Reload**: Fast iteration during development
- **Local Testing**: Complete stack runnable on developer machines
- **Integration Tests**: Automated testing of protocol adapters and service integration
- **Performance Benchmarks**: Baseline metrics for regression testing

## 📋 Compliance Requirements

### Data Governance

- **Privacy by Design**: GDPR, CCPA compliance built-in
- **Data Residency**: Control over data location and movement
- **Audit Compliance**: SOX, HIPAA audit trail capabilities
- **Retention Policies**: Configurable data lifecycle management

### Quality Assurance

- **Error Handling**: Graceful error propagation across protocol boundaries
- **Input Validation**: Schema validation at protocol adapter level
- **Output Consistency**: Guaranteed response format regardless of protocol
- **Version Compatibility**: Backward compatible protocol evolution

## 🎯 Success Metrics

### Technical KPIs

- **Protocol Coverage**: All major protocols supported (REST, gRPC, MCP, +1 legacy)
- **Response Time**: <100ms for ping operations across all protocols
- **Throughput**: 1000+ operations/second per worker
- **Availability**: 99.9% uptime for platform services

### Business KPIs

- **Developer Adoption**: 10+ external integrations using different protocols
- **Cost Efficiency**: 90% reduction in integration effort vs custom APIs
- **Revenue Generation**: $1M+ in mesh transactions tracked by economic layer

## 🔄 Upgrade & Migration Requirements

### Version Management

- **Protocol Versioning**: Support multiple protocol versions simultaneously
- **Service Evolution**: Workers can be updated without platform changes
- **Database Migration**: Automated schema evolution for service registry
- **Configuration Management**: Environment-specific configuration injection

### Backward Compatibility

- **Legacy API Support**: Existing integrations continue working
- **Graceful Degradation**: New features fail back to basic functionality
- **Migration Tooling**: Automated migration from monolith to microservices when needed
