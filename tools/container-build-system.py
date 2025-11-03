#!/usr/bin/env python3
"""
Container-First Build System

Reads build.json manifests for each service and generates:
- Validated Docker Compose configurations
- Build dependency checks
- Environment-specific deployments

This ensures all container builds are consistent and self-documenting.
"""

import json
import os
import sys
import yaml
from pathlib import Path
from typing import Dict, List, Any

class ContainerBuildSystem:
    def __init__(self, services_dir: str = "services"):
        self.services_dir = Path(services_dir)
        self.manifests = {}
        self.load_manifests()
    
    def load_manifests(self):
        """Load all build.json manifests from services directory"""
        for manifest_file in self.services_dir.glob("*.build.json"):
            with open(manifest_file) as f:
                manifest = json.load(f)
                service_name = manifest["service"]
                self.manifests[service_name] = manifest
                print(f"✅ Loaded manifest for {service_name}")
    
    def validate_dependencies(self, manifest: Dict[str, Any]) -> List[str]:
        """Validate that all required files exist"""
        missing_files = []
        
        # Check runtime files
        for file_path in manifest["dependencies"]["runtime_files"]:
            if not Path(file_path).exists():
                missing_files.append(file_path)
        
        # Check requirements file
        req_file = manifest["dependencies"]["requirements_file"]
        if not Path(req_file).exists():
            missing_files.append(req_file)
        
        # Check configuration files
        for config_file in manifest["dependencies"].get("configuration_files", []):
            if not Path(config_file).exists():
                missing_files.append(config_file)
        
        return missing_files
    
    def generate_compose_service(self, service_name: str, environment: str = "development") -> Dict[str, Any]:
        """Generate docker-compose service definition from manifest"""
        manifest = self.manifests[service_name]
        
        service_def = {
            "build": {
                "context": manifest["build_context"],
                "dockerfile": manifest["dockerfile"]
            },
            "container_name": f"{manifest['container_name']}-{environment[:3]}",
            "environment": []
        }
        
        # Add environment variables
        env_vars = manifest["environment"].get(environment, {})
        for key, value in env_vars.items():
            service_def["environment"].append(f"{key}={value}")
        
        # Add platform URL for workers
        if manifest["depends_on"]:
            service_def["environment"].append("PLATFORM_URL=https://crank-platform-dev:8443")
            service_def["environment"].append("PLATFORM_AUTH_TOKEN=${PLATFORM_AUTH_TOKEN:-local-dev-key}")
        
        # Add ports
        ports = []
        for port_name, port_num in manifest["ports"].items():
            env_var = f"{service_name.upper().replace('-', '_')}_{port_name.upper()}_PORT"
            ports.append(f"${{{env_var}:-{port_num}}}:{port_num}")
        service_def["ports"] = ports
        
        # Add volumes for development
        if environment == "development":
            service_def["volumes"] = manifest["volumes"]["development"]
        
        # Add healthcheck
        health = manifest["healthcheck"]
        port = manifest["ports"][health["port"]]
        curl_args = ["CMD", "curl", "-f"]
        
        # Add -k flag for HTTPS to ignore self-signed certificates
        if health["protocol"] == "https":
            curl_args.append("-k")
            
        curl_args.append(f"{health['protocol']}://localhost:{port}{health['endpoint']}")
        
        service_def["healthcheck"] = {
            "test": curl_args,
            "interval": "30s",
            "timeout": "10s", 
            "retries": 3,
            "start_period": "15s"
        }
        
        # Add dependencies
        if manifest["depends_on"]:
            service_def["depends_on"] = {}
            for dep in manifest["depends_on"]:
                service_def["depends_on"][f"{dep}-{environment[:3]}"] = {
                    "condition": "service_healthy"
                }
        
        # Add GPU configuration if needed
        if manifest.get("gpu_required", False):
            gpu_config = manifest.get("gpu_config", {})
            service_def["deploy"] = {
                "resources": {
                    "reservations": {
                        "devices": [{
                            "driver": gpu_config.get("driver", "nvidia"),
                            "count": gpu_config.get("count", "all"),
                            "capabilities": gpu_config.get("capabilities", ["gpu"])
                        }]
                    }
                }
            }
        
        service_def["restart"] = "unless-stopped"
        service_def["networks"] = ["crank-local-net"]
        
        return service_def
    
    def validate_all_services(self) -> bool:
        """Validate all service dependencies"""
        all_valid = True
        
        for service_name, manifest in self.manifests.items():
            print(f"\n🔍 Validating {service_name}...")
            missing_files = self.validate_dependencies(manifest)
            
            if missing_files:
                print(f"❌ Missing files for {service_name}:")
                for file_path in missing_files:
                    print(f"   - {file_path}")
                all_valid = False
            else:
                print(f"✅ All dependencies satisfied for {service_name}")
        
        return all_valid
    
    def generate_compose_file(self, environment: str = "development") -> Dict[str, Any]:
        """Generate complete docker-compose configuration"""
        compose_config = {
            "services": {},
            "networks": {
                "crank-local-net": {
                    "driver": "bridge",
                    "name": "crank-local-network"
                }
            },
            "volumes": {
                "local-data": {"name": "crank-local-data"},
                "local-logs": {"name": "crank-local-logs"}
            }
        }
        
        # Generate services in dependency order
        service_order = self._get_dependency_order()
        
        for service_name in service_order:
            service_def = self.generate_compose_service(service_name, environment)
            compose_config["services"][f"{service_name}-{environment[:3]}"] = service_def
        
        return compose_config
    
    def _get_dependency_order(self) -> List[str]:
        """Get services ordered by dependencies (platform first, workers after)"""
        platform_services = []
        worker_services = []
        
        for service_name, manifest in self.manifests.items():
            if manifest["depends_on"]:
                worker_services.append(service_name)
            else:
                platform_services.append(service_name)
        
        return platform_services + worker_services

def main():
    if len(sys.argv) > 1:
        environment = sys.argv[1]
    else:
        environment = "development"
    
    print(f"🏗️  Container-First Build System")
    print(f"📦 Environment: {environment}")
    
    build_system = ContainerBuildSystem()
    
    if not build_system.manifests:
        print("❌ No build manifests found!")
        return 1
    
    # Validate all dependencies
    if not build_system.validate_all_services():
        print("\n❌ Dependency validation failed!")
        return 1
    
    print(f"\n✅ All dependencies validated!")
    
    # Generate compose file
    compose_config = build_system.generate_compose_file(environment)
    
    output_file = f"docker-compose.{environment}.yml"
    with open(output_file, 'w') as f:
        # Add header comment
        f.write(f"# 🏗️ Auto-generated by Container-First Build System\n")
        f.write(f"# Environment: {environment}\n")
        f.write(f"# Generated from service build manifests\n\n")
        yaml.dump(compose_config, f, default_flow_style=False, sort_keys=False)
    
    print(f"📦 Generated {output_file}")
    print(f"🚀 Ready to deploy: docker-compose -f {output_file} up --build")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())