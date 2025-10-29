# Azure Deployment Strategy for Crank Platform

## 🎯 Deployment Architecture

```
Internet
    │
    ▼
┌─────────────────┐
│ Azure Front Door│  ← Global CDN + WAF + Load Balancing
│ + WAF           │
└─────────────────┘
    │
    ▼
┌─────────────────┐
│ Azure Container │  ← Container orchestration
│ Apps Environment│  ← Auto-scaling + Service discovery
└─────────────────┘
    │
    ├─ Gateway Service (8080)
    ├─ CrankDoc Service (8000)  
    ├─ CrankEmail Service (8001)
    └─ Support Services
           ├─ Redis (coordination)
           ├─ OPA (policy engine)
           └─ Monitoring stack
```

## 🚀 Phase 1: Basic Deployment (Tomorrow's Goal)

### Objectives
- Deploy mesh services to Azure Container Apps
- Test service discovery and communication
- Validate load balancing and auto-scaling
- Stress test with adversarial inputs

### Services to Deploy
1. **Gateway Service** - Single entry point
2. **CrankDoc Service** - Document processing
3. **CrankEmail Service** - Email processing  
4. **Redis** - Coordination and caching
5. **OPA** - Policy engine (basic)

### Resource Requirements

| Service | CPU | Memory | Replicas | Scaling |
|---------|-----|--------|----------|---------|
| Gateway | 0.5 | 1Gi | 1-3 | CPU > 70% |
| CrankDoc | 1.0 | 2Gi | 1-5 | CPU > 80% |
| CrankEmail | 0.5 | 1Gi | 1-3 | CPU > 70% |
| Redis | 0.25 | 512Mi | 1 | None |
| OPA | 0.25 | 256Mi | 1-2 | CPU > 60% |

## 🔧 Infrastructure as Code

### Azure Bicep Template Structure

```
azure/
├── main.bicep                 # Main deployment template
├── modules/
│   ├── container-apps.bicep   # Container Apps environment
│   ├── networking.bicep       # VNet, subnets, NSGs
│   ├── monitoring.bicep       # Log Analytics, App Insights
│   └── storage.bicep          # Storage accounts, Key Vault
├── parameters/
│   ├── dev.bicepparam         # Development environment
│   ├── staging.bicepparam     # Staging environment
│   └── prod.bicepparam        # Production environment
└── scripts/
    ├── deploy.sh              # Deployment script
    ├── test.sh                # Testing script
    └── cleanup.sh             # Resource cleanup
```

## 🧪 Testing Strategy

### 1. Deployment Testing
- [ ] Infrastructure provisioning time
- [ ] Service startup and health checks
- [ ] Inter-service communication
- [ ] External connectivity via Front Door

### 2. Functional Testing
- [ ] Document conversion end-to-end
- [ ] Email parsing and classification
- [ ] Gateway routing and load balancing
- [ ] Authentication and authorization

### 3. Performance Testing
- [ ] Concurrent request handling
- [ ] Auto-scaling behavior
- [ ] Response time under load
- [ ] Memory usage patterns

### 4. Adversarial Testing
- [ ] Malformed file uploads
- [ ] Oversized requests (>50MB)
- [ ] Authentication bypass attempts
- [ ] Resource exhaustion attacks
- [ ] Invalid input formats

### 5. Chaos Engineering
- [ ] Container instance failures
- [ ] Network partitions
- [ ] Dependency service outages
- [ ] Resource limit breaches

## 📊 Monitoring and Observability

### Application Insights Integration
```json
{
  "logging": {
    "level": "Info",
    "appInsights": {
      "instrumentationKey": "${APP_INSIGHTS_KEY}",
      "enablePerformanceCounters": true,
      "enableDependencyTracking": true
    }
  }
}
```

### Key Metrics to Track
- **Request Rate**: Requests per second per service
- **Response Time**: P50, P95, P99 latencies
- **Error Rate**: HTTP 4xx/5xx responses
- **Throughput**: Successful operations per minute
- **Resource Usage**: CPU, memory, disk utilization
- **Scaling Events**: Auto-scale triggers and responses

### Alerting Rules
```yaml
alerts:
  - name: "High Error Rate"
    condition: "error_rate > 5%"
    duration: "5m"
    action: "notify_team"
  
  - name: "High Response Time"
    condition: "p95_latency > 5s"
    duration: "3m"
    action: "scale_up"
  
  - name: "Service Down"
    condition: "health_check_failed"
    duration: "1m"
    action: "immediate_alert"
```

## 🔒 Security Configuration

### Container Security
- Non-root user execution
- Read-only root filesystem
- Resource limits enforced
- No privileged escalation
- Network policies applied

### Network Security
- Private VNet with subnet isolation
- Network Security Groups (NSGs)
- Application Gateway with WAF
- TLS 1.3 encryption in transit
- Private endpoints for dependencies

### Identity and Access
- Managed Identity for inter-service auth
- Azure Key Vault for secrets
- RBAC for Azure resources
- API key authentication for services
- Audit logging for all operations

## 🚀 Deployment Commands

### Prerequisites
```bash
# Login to Azure
az login

# Set subscription
az account set --subscription "Your-Subscription-Id"

# Install Bicep
az bicep install
```

### Deploy Infrastructure
```bash
# Deploy to development
./azure/scripts/deploy.sh dev

# Deploy to staging
./azure/scripts/deploy.sh staging

# Deploy to production
./azure/scripts/deploy.sh prod
```

### Test Deployment
```bash
# Run comprehensive tests
./azure/scripts/test.sh

# Run adversarial tests
./azure/scripts/adversarial-test.sh

# Monitor deployment
./azure/scripts/monitor.sh
```

## 🎛️ Environment Configuration

### Development Environment
- **Scale**: Minimal (1 replica each)
- **Resources**: Basic tier
- **Monitoring**: Essential only
- **Cost**: ~$50/month

### Staging Environment  
- **Scale**: Production-like (2-3 replicas)
- **Resources**: Standard tier
- **Monitoring**: Full observability
- **Cost**: ~$200/month

### Production Environment
- **Scale**: Auto-scaling (1-10 replicas)
- **Resources**: Premium tier
- **Monitoring**: Enterprise observability
- **Cost**: ~$500-2000/month (usage-based)

## 🔍 Success Criteria

### Performance Targets
- [ ] **Response Time**: <500ms for 95% of requests
- [ ] **Throughput**: 1000+ requests/minute sustained
- [ ] **Availability**: 99.9% uptime (8.77 hours downtime/year)
- [ ] **Scalability**: Handle 10x traffic spikes automatically

### Functional Targets
- [ ] **Document Conversion**: 100% success rate for valid inputs
- [ ] **Email Classification**: >95% accuracy on test dataset
- [ ] **Error Handling**: Graceful degradation for invalid inputs
- [ ] **Security**: Zero successful bypass attempts

### Operational Targets
- [ ] **Deployment Time**: <10 minutes from push to production
- [ ] **Recovery Time**: <5 minutes from failure to restoration
- [ ] **Monitoring Coverage**: 100% of critical paths instrumented
- [ ] **Cost Efficiency**: <$0.01 per successful request

## 🔄 Continuous Deployment Pipeline

### GitHub Actions Integration
```yaml
name: Deploy to Azure
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Test Services
        run: python services/test_mesh.py
  
  deploy:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to Azure
        run: ./azure/scripts/deploy.sh staging
```

## 📚 Documentation and Runbooks

### Operational Runbooks
- [ ] **Service Deployment**: Step-by-step deployment guide
- [ ] **Incident Response**: Troubleshooting common issues
- [ ] **Scaling Operations**: Manual and automatic scaling
- [ ] **Security Incidents**: Security breach response plan

### Monitoring Playbooks
- [ ] **Performance Degradation**: Response to slow services
- [ ] **Error Rate Spikes**: Debugging high error rates
- [ ] **Resource Exhaustion**: Handling resource limits
- [ ] **Dependency Failures**: Handling external service outages

## 🎯 Tomorrow's Checklist

### Morning (Setup)
- [ ] Create Azure resource group
- [ ] Deploy Bicep templates
- [ ] Verify service connectivity
- [ ] Configure monitoring

### Afternoon (Testing)
- [ ] Run functional tests
- [ ] Execute performance tests
- [ ] Perform adversarial testing
- [ ] Validate auto-scaling

### Evening (Optimization)
- [ ] Analyze performance results
- [ ] Optimize resource allocation
- [ ] Update monitoring alerts
- [ ] Document lessons learned

## 🔮 Future Enhancements

### Phase 2: Advanced Features
- Multi-region deployment
- Advanced service mesh (Istio)
- AI model serving integration
- Advanced security scanning

### Phase 3: Production Hardening
- Disaster recovery automation
- Advanced monitoring and AI-ops
- Cost optimization automation
- Compliance and audit automation