# Docker Deployment Configurations

## Strategy: Minimal, Clean, Purpose-Driven

### Core Configurations (Keep)

#### 1. `docker-compose.dev.yml` - Local Development
- **Purpose**: Fast iteration, debugging, hot reload
- **Features**: 
  - Direct volume mounts for code changes
  - Debug ports exposed
  - Relaxed security for development speed
  - Local file system integration

#### 2. `docker-compose.local-prod.yml` - Local Production Simulation  
- **Purpose**: Test production-like environment locally
- **Features**:
  - Production-like networking and security
  - Certificate validation (self-signed acceptable)
  - Performance optimization enabled
  - Simulates production constraints

#### 3. `docker-compose.azure.yml` - Azure Container Services
- **Purpose**: Cloud deployment (when ready)
- **Status**: ⚠️ REBUILD REQUIRED - Previous attempts failed with:
  - Host naming issues
  - Certificate problems  
  - General deployment ugliness
- **Requirements**: Must be production-ready art, not hack

---

## Cleanup Plan

### Files to Archive/Remove
- `docker-compose.enterprise.yml` - Failed ACS attempt with CA service
- `docker-compose.gpu-workers.yml` - Unnecessary complexity for local dev
- `docker-compose.production.yml` - Rename to local-prod.yml for clarity

### Rationale
- **Less is More**: Three clear purposes vs. confusing matrix of options
- **Local GPU**: Can be handled via environment variables in dev config
- **Enterprise**: Was over-engineered ACS attempt, not needed