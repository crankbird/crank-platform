# 🚢 Port Configuration Strategy

## 🚨 **Current Problem: Hard-coded Port Hell**

### **Conflicts Identified:**
- Email Parser & Classifier both use `8003` internally
- All services have hard-coded ports in their code
- Docker-compose uses band-aid port remapping
- Deployment flexibility = ZERO 

### **Production Deployment Issues:**
- Can't deploy multiple instances on same host
- Kubernetes port conflicts
- Cloud scaling problems
- Development environment conflicts

---

## ✅ **Solution: Environment-Based Port Configuration**

### **Port Allocation Strategy:**

| Service | Default Port | Env Var | Production Range |
|---------|--------------|---------|------------------|
| **Platform** | 8000 | `PLATFORM_PORT` | 8000-8099 |
| **Doc Converter** | 8100 | `DOC_CONVERTER_PORT` | 8100-8199 |
| **Email Classifier** | 8200 | `EMAIL_CLASSIFIER_PORT` | 8200-8299 |
| **Email Parser** | 8300 | `EMAIL_PARSER_PORT` | 8300-8399 |
| **Image Classifier** | 8400 | `IMAGE_CLASSIFIER_PORT` | 8400-8499 |
| **Streaming** | 8500 | `STREAMING_PORT` | 8500-8599 |
| **GPU Services** | 8600+ | `GPU_SERVICE_PORT` | 8600-8699 |

### **HTTPS Ports (Production):**
- Base port + 443 offset
- Platform: 8443 (standard)
- Services: Use TLS termination at load balancer

---

## 🔧 **Implementation Plan**

### **Phase 1: Environment Variable Configuration**
```python
# Standard pattern for all services:
def get_port() -> int:
    return int(os.getenv("SERVICE_PORT", "8200"))  # Default varies by service

def get_host() -> str:
    return os.getenv("SERVICE_HOST", "0.0.0.0")
```

### **Phase 2: Update Docker Compose**
```yaml
# Use environment variables for ports
services:
  crank-email-classifier:
    ports:
      - "${EMAIL_CLASSIFIER_PORT:-8200}:${EMAIL_CLASSIFIER_PORT:-8200}"
    environment:
      - SERVICE_PORT=${EMAIL_CLASSIFIER_PORT:-8200}
```

### **Phase 3: Production Deployment**
```bash
# .env file for production
PLATFORM_PORT=8000
EMAIL_CLASSIFIER_PORT=8200  
EMAIL_PARSER_PORT=8300
STREAMING_PORT=8500
```

---

## 📦 **Kubernetes Compatibility**
```yaml
# ConfigMap for port configuration
apiVersion: v1
kind: ConfigMap
metadata:
  name: service-ports
data:
  EMAIL_CLASSIFIER_PORT: "8200"
  EMAIL_PARSER_PORT: "8300"
  STREAMING_PORT: "8500"
```

---

## 🎯 **Benefits**

✅ **Zero port conflicts** - Each service has dedicated range  
✅ **Flexible deployment** - Configure ports per environment  
✅ **Kubernetes ready** - ConfigMap integration  
✅ **Multiple instances** - Can run different ports on same host  
✅ **Cloud native** - Follows 12-factor app principles  
✅ **Development friendly** - Easy local testing  

---

## 🚀 **Migration Steps**

1. **Update service code** - Use environment variables for ports
2. **Update docker-compose** - Use parameterized ports  
3. **Create .env template** - Document port assignments
4. **Test multi-instance** - Verify no conflicts
5. **Update documentation** - Clear port allocation guide

This fixes the deployment nightmare and makes our services truly cloud-ready! 🌟