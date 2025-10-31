# Worker Separation Strategy 🏗️

## Current Development Approach
**Status**: Workers temporarily in platform repo for rapid development  
**Goal**: Architect for future separation into independent repositories

## 🎯 Separation Readiness Checklist

### Phase 1: Clean Boundaries (Current)
- [x] **Plugin Architecture Foundation**: `plugin_architecture.py` defines interfaces
- [x] **Worker Self-Containment**: Each worker is independent module
- [x] **Standardized Communication**: HTTPS + mTLS for all worker interactions
- [ ] **Worker Metadata**: Each worker defines `plugin.yaml` with capabilities
- [ ] **Isolated Dependencies**: Worker-specific `requirements.txt` per service
- [ ] **Independent Dockerfiles**: Each worker has dedicated container config

### Phase 2: Plugin Registration (Next)
- [ ] **Dynamic Discovery**: Platform discovers workers via plugin registry
- [ ] **Version Compatibility**: Workers declare platform version requirements  
- [ ] **Health Monitoring**: Platform monitors worker health independently
- [ ] **Capability Advertising**: Workers advertise their conversion capabilities

### Phase 3: Repository Separation (Future)
- [ ] **Extract Workers**: Move each worker to separate git repository
- [ ] **Independent CI/CD**: Each worker has own build/test/deploy pipeline
- [ ] **Plugin Distribution**: Workers published as installable plugins
- [ ] **Platform Registry**: Central registry for discovering/installing workers

## 🛠 Implementation Strategy

### Current Development (Platform Repo)
```
services/
├── crank_doc_converter.py    # Future: crank-doc-converter repo
├── crankemail_mesh.py        # Future: crank-email-processor repo
├── plugin_architecture.py    # Stays in platform
└── plugin_manager.py         # Stays in platform
```

### Future Separation
```
crank-platform/               # Core platform only
├── services/
│   ├── platform_app.py
│   ├── plugin_manager.py
│   └── plugin_registry.py

crank-doc-converter/          # Independent worker repo
├── src/crank_doc_converter.py
├── Dockerfile
├── requirements.txt
├── plugin.yaml              # Metadata for platform integration
└── tests/

crank-email-processor/        # Independent worker repo  
├── src/crankemail_mesh.py
├── Dockerfile
├── requirements.txt
├── plugin.yaml
└── tests/
```

## 📋 Development Guidelines

### Worker Development Rules
1. **No Platform Dependencies**: Workers should not import platform modules
2. **Standardized Interfaces**: All workers implement `PluginInterface`
3. **Self-Describing**: Each worker provides metadata about capabilities
4. **Independent Testing**: Workers can be tested without platform running
5. **Container Ready**: Each worker has complete Docker configuration

### Platform Development Rules
1. **Plugin Agnostic**: Platform discovers workers dynamically
2. **Version Tolerance**: Handle worker version mismatches gracefully
3. **Health Monitoring**: Monitor worker availability independently
4. **Capability Registry**: Maintain registry of available worker capabilities

## 🎪 Migration Benefits

### Development Velocity
- **Parallel Development**: Teams can work on workers independently
- **Faster CI/CD**: Smaller repos = faster builds and tests
- **Independent Versioning**: Workers can release on their own schedule

### Operational Benefits
- **Selective Deployment**: Deploy only needed workers per environment
- **Resource Scaling**: Scale workers independently based on demand
- **Fault Isolation**: Worker failures don't impact platform core

### Plugin Ecosystem
- **Third-Party Workers**: External developers can create workers
- **Worker Marketplace**: Central registry of available workers
- **Modular Installation**: Install only needed functionality

## 🚦 Current Development Decision

**For Now**: Continue developing workers in platform repo for velocity  
**Architecture**: Build with separation interfaces from day one  
**Timeline**: Separate when we have 3+ workers or external contributors  

This approach gives us rapid development now while setting up clean separation later! 🎯