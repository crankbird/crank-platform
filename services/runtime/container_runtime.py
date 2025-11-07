"""
🦙 Kevin's Container Runtime Abstraction

The foundation for runtime nirvana - seamless portability across Docker, Podman, and Containerd.
Kevin believes in elegant abstractions that just work™.
"""

import json
import logging
import os
import subprocess
from abc import ABC, abstractmethod
from typing import Any, Optional

logger = logging.getLogger(__name__)


class ContainerRuntime(ABC):
    """Kevin's abstract container runtime interface"""

    @abstractmethod
    def is_available(self) -> bool:
        """Check if this runtime is available on the system"""

    @abstractmethod
    def run(self, image: str, config: dict[str, Any]) -> str:
        """Run a container, return container ID"""

    @abstractmethod
    def build(self, dockerfile_path: str, tag: str, context: str = ".") -> bool:
        """Build an image from Dockerfile"""

    @abstractmethod
    def stop(self, container_id: str) -> bool:
        """Stop a running container"""

    @abstractmethod
    def remove(self, container_id: str, force: bool = False) -> bool:
        """Remove a container"""

    @abstractmethod
    def logs(self, container_id: str, follow: bool = False) -> str:
        """Get container logs"""

    @abstractmethod
    def inspect(self, container_id: str) -> dict[str, Any]:
        """Get detailed container information"""

    @property
    @abstractmethod
    def name(self) -> str:
        """Runtime name for identification"""


class DockerRuntime(ContainerRuntime):
    """Kevin's Docker implementation - the familiar friend"""

    @property
    def name(self) -> str:
        return "docker"

    def is_available(self) -> bool:
        try:
            result = subprocess.run(
                ["docker", "--version"],
                capture_output=True,
                check=True,
                timeout=5,
            )
            logger.debug(f"Docker version: {result.stdout.decode().strip()}")
            return True
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def run(self, image: str, config: dict[str, Any]) -> str:
        """Run container with Docker"""
        cmd = ["docker", "run"]

        # Detached mode (default for services)
        if config.get("detach", True):
            cmd.append("-d")

        # Container name
        if "name" in config:
            cmd.extend(["--name", config["name"]])

        # Port mappings
        for port_map in config.get("ports", []):
            cmd.extend(["-p", port_map])

        # Environment variables
        for env_var in config.get("environment", []):
            cmd.extend(["-e", env_var])

        # Volume mounts
        for volume in config.get("volumes", []):
            cmd.extend(["-v", volume])

        # Network configuration
        if "network" in config:
            cmd.extend(["--network", config["network"]])

        # Resource limits
        if "memory" in config:
            cmd.extend(["--memory", config["memory"]])
        if "cpus" in config:
            cmd.extend(["--cpus", str(config["cpus"])])

        # Restart policy
        if "restart" in config:
            cmd.extend(["--restart", config["restart"]])

        # Security options
        if config.get("read_only", False):
            cmd.append("--read-only")

        cmd.append(image)

        # Command arguments
        if "command" in config:
            if isinstance(config["command"], list):
                cmd.extend(config["command"])
            else:
                cmd.append(config["command"])

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            container_id = result.stdout.strip()
            logger.info("🐳 Started Docker container: {container_id}")
            return container_id
        except subprocess.CalledProcessError as e:
            logger.exception("Docker run failed: {e.stderr}")
            raise RuntimeError(f"Docker run failed: {e.stderr}")

    def build(self, dockerfile_path: str, tag: str, context: str = ".") -> bool:
        """Build image with Docker"""
        try:
            cmd = ["docker", "build", "-f", dockerfile_path, "-t", tag, context]
            subprocess.run(cmd, check=True, capture_output=True)
            logger.info("🏗️ Built Docker image: {tag}")
            return True
        except subprocess.CalledProcessError:
            logger.exception("Docker build failed: {e.stderr.decode()}")
            return False

    def stop(self, container_id: str) -> bool:
        """Stop Docker container"""
        try:
            subprocess.run(["docker", "stop", container_id], check=True, capture_output=True)
            logger.info("🛑 Stopped Docker container: {container_id}")
            return True
        except subprocess.CalledProcessError:
            logger.exception("Docker stop failed: {e.stderr.decode()}")
            return False

    def remove(self, container_id: str, force: bool = False) -> bool:
        """Remove Docker container"""
        try:
            cmd = ["docker", "rm"]
            if force:
                cmd.append("-f")
            cmd.append(container_id)
            subprocess.run(cmd, check=True, capture_output=True)
            logger.info("🗑️ Removed Docker container: {container_id}")
            return True
        except subprocess.CalledProcessError:
            logger.exception("Docker remove failed: {e.stderr.decode()}")
            return False

    def logs(self, container_id: str, follow: bool = False) -> str:
        """Get Docker container logs"""
        try:
            cmd = ["docker", "logs"]
            if follow:
                cmd.append("-f")
            cmd.append(container_id)
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return result.stdout
        except subprocess.CalledProcessError:
            logger.exception("Docker logs failed: {e.stderr}")
            return ""

    def inspect(self, container_id: str) -> dict[str, Any]:
        """Inspect Docker container"""
        try:
            result = subprocess.run(
                ["docker", "inspect", container_id],
                capture_output=True,
                text=True,
                check=True,
            )
            return json.loads(result.stdout)[0]  # Docker returns array
        except (subprocess.CalledProcessError, json.JSONDecodeError, IndexError):
            logger.exception("Docker inspect failed: {e}")
            return {}


class PodmanRuntime(ContainerRuntime):
    """Kevin's Podman implementation - the security-conscious alternative"""

    @property
    def name(self) -> str:
        return "podman"

    def is_available(self) -> bool:
        try:
            result = subprocess.run(
                ["podman", "--version"],
                capture_output=True,
                check=True,
                timeout=5,
            )
            logger.debug(f"Podman version: {result.stdout.decode().strip()}")
            return True
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def run(self, image: str, config: dict[str, Any]) -> str:
        """Run container with Podman - almost identical to Docker!"""
        cmd = ["podman", "run"]

        # Detached mode
        if config.get("detach", True):
            cmd.append("-d")

        # Container name
        if "name" in config:
            cmd.extend(["--name", config["name"]])

        # Port mappings
        for port_map in config.get("ports", []):
            cmd.extend(["-p", port_map])

        # Environment variables
        for env_var in config.get("environment", []):
            cmd.extend(["-e", env_var])

        # Volume mounts
        for volume in config.get("volumes", []):
            cmd.extend(["-v", volume])

        # Network configuration
        if "network" in config:
            cmd.extend(["--network", config["network"]])

        # Resource limits
        if "memory" in config:
            cmd.extend(["--memory", config["memory"]])
        if "cpus" in config:
            cmd.extend(["--cpus", str(config["cpus"])])

        # Restart policy
        if "restart" in config:
            cmd.extend(["--restart", config["restart"]])

        # Security options
        if config.get("read_only", False):
            cmd.append("--read-only")

        cmd.append(image)

        # Command arguments
        if "command" in config:
            if isinstance(config["command"], list):
                cmd.extend(config["command"])
            else:
                cmd.append(config["command"])

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            container_id = result.stdout.strip()
            logger.info("🦭 Started Podman container: {container_id}")
            return container_id
        except subprocess.CalledProcessError as e:
            logger.exception("Podman run failed: {e.stderr}")
            raise RuntimeError(f"Podman run failed: {e.stderr}")

    def build(self, dockerfile_path: str, tag: str, context: str = ".") -> bool:
        """Build image with Podman"""
        try:
            cmd = ["podman", "build", "-f", dockerfile_path, "-t", tag, context]
            subprocess.run(cmd, check=True, capture_output=True)
            logger.info("🏗️ Built Podman image: {tag}")
            return True
        except subprocess.CalledProcessError:
            logger.exception("Podman build failed: {e.stderr.decode()}")
            return False

    def stop(self, container_id: str) -> bool:
        """Stop Podman container"""
        try:
            subprocess.run(["podman", "stop", container_id], check=True, capture_output=True)
            logger.info("🛑 Stopped Podman container: {container_id}")
            return True
        except subprocess.CalledProcessError:
            logger.exception("Podman stop failed: {e.stderr.decode()}")
            return False

    def remove(self, container_id: str, force: bool = False) -> bool:
        """Remove Podman container"""
        try:
            cmd = ["podman", "rm"]
            if force:
                cmd.append("-f")
            cmd.append(container_id)
            subprocess.run(cmd, check=True, capture_output=True)
            logger.info("🗑️ Removed Podman container: {container_id}")
            return True
        except subprocess.CalledProcessError:
            logger.exception("Podman remove failed: {e.stderr.decode()}")
            return False

    def logs(self, container_id: str, follow: bool = False) -> str:
        """Get Podman container logs"""
        try:
            cmd = ["podman", "logs"]
            if follow:
                cmd.append("-f")
            cmd.append(container_id)
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return result.stdout
        except subprocess.CalledProcessError:
            logger.exception("Podman logs failed: {e.stderr}")
            return ""

    def inspect(self, container_id: str) -> dict[str, Any]:
        """Inspect Podman container"""
        try:
            result = subprocess.run(
                ["podman", "inspect", container_id],
                capture_output=True,
                text=True,
                check=True,
            )
            return json.loads(result.stdout)[0]  # Podman returns array
        except (subprocess.CalledProcessError, json.JSONDecodeError, IndexError):
            logger.exception("Podman inspect failed: {e}")
            return {}


class RuntimeManager:
    """Kevin's intelligent runtime manager - the orchestrator of nirvana"""

    def __init__(self, preferred_runtime: str = "auto"):
        self.preferred_runtime = preferred_runtime
        self.runtime = self._detect_best_runtime()
        logger.info("🦙 Kevin selected runtime: {self.runtime.name}")

    def _detect_best_runtime(self) -> ContainerRuntime:
        """Kevin's intelligent runtime detection"""

        # Available runtime implementations
        available_runtimes = {
            "docker": DockerRuntime(),
            "podman": PodmanRuntime(),
        }

        # If user specified a preference and it's available, use it
        if self.preferred_runtime != "auto" and self.preferred_runtime in available_runtimes:
            runtime = available_runtimes[self.preferred_runtime]
            if runtime.is_available():
                logger.info("🎯 Using preferred runtime: {self.preferred_runtime}")
                return runtime
            logger.warning(
                f"⚠️ Preferred runtime {self.preferred_runtime} not available, falling back...",
            )

        # Auto-detection priority order (Kevin's preferences)
        priority_order = ["docker", "podman"]  # Docker first for ecosystem compatibility

        for runtime_name in priority_order:
            runtime = available_runtimes[runtime_name]
            if runtime.is_available():
                logger.info("🔍 Auto-detected runtime: {runtime_name}")
                return runtime

        # No runtime available - Kevin is sad
        available_names = [
            name for name, runtime in available_runtimes.items() if runtime.is_available()
        ]
        raise RuntimeError(
            f"🦙💔 Kevin couldn't find any container runtime! "
            f"Please install Docker or Podman. Available: {available_names}",
        )

    def run_service(self, image: str, **kwargs) -> str:
        """Kevin's universal service runner"""
        config = {
            "ports": kwargs.get("ports", []),
            "environment": kwargs.get("environment", []),
            "volumes": kwargs.get("volumes", []),
            "name": kwargs.get("name"),
            "network": kwargs.get("network"),
            "memory": kwargs.get("memory"),
            "cpus": kwargs.get("cpus"),
            "restart": kwargs.get("restart", "unless-stopped"),
            "read_only": kwargs.get("read_only", False),
            "command": kwargs.get("command"),
            "detach": kwargs.get("detach", True),
        }

        # Remove None values
        config = {k: v for k, v in config.items() if v is not None}

        try:
            container_id = self.runtime.run(image, config)
            logger.info("🚀 Service deployed: {image} -> {container_id[:12]}")
            return container_id
        except Exception:
            logger.exception("❌ Service deployment failed: {e}")
            raise

    def build_service(self, dockerfile_path: str, tag: str, context: str = ".") -> bool:
        """Kevin's universal service builder"""
        try:
            success = self.runtime.build(dockerfile_path, tag, context)
            if success:
                logger.info("🏗️ Built service image: {tag}")
            else:
                logger.error("❌ Failed to build service image: {tag}")
            return success
        except Exception:
            logger.exception("❌ Build error: {e}")
            return False

    def stop_service(self, container_id: str) -> bool:
        """Kevin's universal service stopper"""
        return self.runtime.stop(container_id)

    def remove_service(self, container_id: str, force: bool = False) -> bool:
        """Kevin's universal service remover"""
        return self.runtime.remove(container_id, force)

    def get_service_logs(self, container_id: str, follow: bool = False) -> str:
        """Kevin's universal log viewer"""
        return self.runtime.logs(container_id, follow)

    def inspect_service(self, container_id: str) -> dict[str, Any]:
        """Kevin's universal service inspector"""
        return self.runtime.inspect(container_id)

    @property
    def current_runtime(self) -> str:
        """Get currently active runtime name"""
        return self.runtime.name

    def get_runtime_info(self) -> dict[str, Any]:
        """Kevin's runtime status report"""
        return {
            "current_runtime": self.runtime.name,
            "preferred_runtime": self.preferred_runtime,
            "runtime_available": self.runtime.is_available(),
            "kevin_happiness": "😊" if self.runtime.is_available() else "😢",
        }


# Convenience function for quick usage
def create_runtime_manager(preferred: Optional[str] = None) -> RuntimeManager:
    """Kevin's convenience factory"""
    preference = preferred or os.getenv("CRANK_CONTAINER_RUNTIME", "auto")
    return RuntimeManager(preferred_runtime=preference)
