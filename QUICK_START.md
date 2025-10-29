# Quick Reference - Azure VM Setup

## 🚀 **1-Minute Bootstrap**

```bash
# Clone main repo
git clone git@github.com:crankbird/crank-platform.git
cd crank-platform

# Read the full guide
cat AZURE_SETUP_GUIDE.md
```

## ⚡ **Critical Commands**

### Start Local Services
```bash
cd services
docker-compose up --build
```

### Test Mesh Interface
```bash
curl -H "Authorization: Bearer dev-mesh-key" http://localhost:8080/v1/capabilities
```

### Graphite Auth
```bash
gt auth --token c7l1GB3uOrGp9USp1Y42iG4snP26C9HKS868xBRdJn5GLiX2pbZ0hiiCDB6m
```

### Run Security Tests
```bash
python azure/adversarial-test.py --target http://localhost:8080
```

## 📁 **Key Files**
- `AZURE_SETUP_GUIDE.md` - Complete setup guide
- `services/` - Mesh implementation  
- `azure/deployment-strategy.md` - Azure deployment plan
- `ENHANCEMENT_ROADMAP.md` - Development roadmap

## 🎯 **Today's Goal**
Deploy mesh services to Azure Container Apps and run adversarial testing.

## 👨‍💻 **About the Code**
Built by **John R** with a focus on efficiency over scale. The gaming laptop constraints aren't bugs - they're features that drive elegant solutions.

**Everything you need is in the repo - no external context required!** 🎉