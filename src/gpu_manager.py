"""
Universal GPU Manager for Crank Platform
Handles CUDA, MPS (Apple Silicon), and CPU environments seamlessly
"""

import json
import logging
import platform
from pathlib import Path
from typing import Any, Optional, cast

import torch

logger = logging.getLogger(__name__)


class UniversalGPUManager:
    """
    Manages GPU detection and optimal PyTorch device selection
    Works across CUDA, MPS, and CPU environments
    """

    def __init__(self, prefer_device: Optional[str] = None):
        """
        Initialize GPU manager with automatic device detection

        Args:
            prefer_device: Optional device preference ('cuda', 'mps', 'cpu')
        """
        self.config_file = Path("gpu_config.json")
        self.device_info = self._detect_optimal_device(prefer_device)
        self.device = torch.device(self.device_info["device"])

        logger.info(
            f"Initialized UniversalGPUManager with {self.device_info['type']} on {self.device}",
        )

    def _detect_optimal_device(self, prefer_device: Optional[str] = None) -> dict[str, Any]:
        """Detect and return optimal PyTorch device information"""

        {
            "device": "cpu",
            "type": "CPU",
            "memory_gb": None,
            "compute_capability": None,
            "platform": platform.system(),
            "architecture": platform.machine(),
        }

        # If user has preference, try it first
        if prefer_device:
            if prefer_device == "cuda" and torch.cuda.is_available():
                return self._get_cuda_info()
            if prefer_device == "mps" and self._is_mps_available():
                return self._get_mps_info()
            if prefer_device == "cpu":
                return self._get_cpu_info()
            logger.warning("Preferred device '{prefer_device}' not available, auto-detecting...")

        # Auto-detection priority: CUDA > MPS > CPU
        if torch.cuda.is_available():
            return self._get_cuda_info()
        if self._is_mps_available():
            return self._get_mps_info()
        return self._get_cpu_info()

    def _is_mps_available(self) -> bool:
        """Check if MPS (Apple Silicon) is available"""
        try:
            if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
                # Test MPS with a small tensor
                torch.zeros(1, device="mps")
                return True
        except Exception as e:
            logger.debug(f"MPS test failed: {e}")
            return False
        return False

    def _get_cuda_info(self) -> dict[str, Any]:
        """Get CUDA device information"""
        device_props = torch.cuda.get_device_properties(0)

        return {
            "device": "cuda",
            "type": f"NVIDIA {device_props.name}",
            "memory_gb": device_props.total_memory / (1024**3),
            "compute_capability": f"{device_props.major}.{device_props.minor}",
            "platform": platform.system(),
            "architecture": platform.machine(),
            "device_count": torch.cuda.device_count(),
        }

    def _get_mps_info(self) -> dict[str, Any]:
        """Get MPS (Apple Silicon) device information"""
        # Get system memory for unified memory systems
        try:
            import psutil

            total_memory = psutil.virtual_memory().total / (1024**3)
        except ImportError:
            total_memory = None

        return {
            "device": "mps",
            "type": "Apple Metal Performance Shaders",
            "memory_gb": total_memory,  # Unified memory
            "compute_capability": "Apple Silicon",
            "platform": platform.system(),
            "architecture": platform.machine(),
        }

    def _get_cpu_info(self) -> dict[str, Any]:
        """Get CPU device information"""
        try:
            import psutil

            total_memory = psutil.virtual_memory().total / (1024**3)
            cpu_count = psutil.cpu_count()
            cpu_info = f"CPU ({cpu_count} cores)"
        except ImportError:
            total_memory = None
            cpu_info = "CPU"

        return {
            "device": "cpu",
            "type": cpu_info,
            "memory_gb": total_memory,
            "compute_capability": platform.processor(),
            "platform": platform.system(),
            "architecture": platform.machine(),
        }

    def get_device(self) -> torch.device:
        """Return optimal PyTorch device"""
        return self.device

    def get_device_str(self) -> str:
        """Return device as string"""
        return str(self.device)

    def get_info(self) -> dict[str, Any]:
        """Return comprehensive device information"""
        return self.device_info.copy()

    def optimize_model_for_device(self, model: torch.nn.Module) -> torch.nn.Module:
        """Apply device-specific optimizations to model"""

        # Move model to optimal device
        model = model.to(self.device)

        if self.device.type == "cuda":
            # CUDA optimizations
            model.eval()  # Set to eval mode for inference

            # Enable torch.compile if available (PyTorch 2.0+)
            if hasattr(torch, "compile"):
                try:
                    compiled_model = torch.compile(model, mode="reduce-overhead")
                    model = cast(torch.nn.Module, compiled_model)
                    logger.info("Applied torch.compile optimization for CUDA")
                except Exception as e:
                    logger.debug(f"torch.compile failed: {e}")

        elif self.device.type == "mps":
            # MPS optimizations for Apple Silicon
            model.eval()

            # Use half precision if model supports it for memory efficiency
            if hasattr(model, "half") and self.device_info.get("memory_gb", 0) < 64:
                try:
                    model = model.half()
                    logger.info("Applied half precision optimization for MPS")
                except Exception as e:
                    logger.debug(f"Half precision failed: {e}")

        elif self.device.type == "cpu":
            # CPU optimizations
            model.eval()

            # Enable JIT compilation for CPU
            try:
                # Set number of threads for CPU inference
                torch.set_num_threads(torch.get_num_threads())
                logger.info("Using {torch.get_num_threads()} CPU threads")
            except Exception as e:
                logger.debug(f"CPU optimization failed: {e}")

        return model

    def optimize_tensor_for_device(self, tensor: torch.Tensor) -> torch.Tensor:
        """Optimize tensor for current device"""

        tensor = tensor.to(self.device)

        # Apply device-specific tensor optimizations
        if self.device.type == "mps" and tensor.dtype == torch.float32:
            # Use half precision on MPS for memory efficiency
            try:
                tensor = tensor.half()
            except Exception:
                pass  # Keep original precision if conversion fails

        return tensor

    def get_memory_info(self) -> dict[str, Any]:
        """Get memory information for current device"""

        if self.device.type == "cuda":
            return {
                "allocated_gb": torch.cuda.memory_allocated() / (1024**3),
                "reserved_gb": torch.cuda.memory_reserved() / (1024**3),
                "total_gb": torch.cuda.get_device_properties(0).total_memory / (1024**3),
                "utilization": torch.cuda.memory_allocated()
                / torch.cuda.get_device_properties(0).total_memory,
            }

        if self.device.type == "mps":
            try:
                import psutil

                memory = psutil.virtual_memory()
                return {
                    "allocated_gb": None,  # Not directly available for MPS
                    "reserved_gb": None,
                    "total_gb": memory.total / (1024**3),
                    "utilization": memory.percent / 100.0,
                }
            except ImportError:
                return {"error": "psutil not available for memory info"}

        else:  # CPU
            try:
                import psutil

                memory = psutil.virtual_memory()
                return {
                    "allocated_gb": None,
                    "reserved_gb": None,
                    "total_gb": memory.total / (1024**3),
                    "utilization": memory.percent / 100.0,
                }
            except ImportError:
                return {"error": "psutil not available for memory info"}

    def save_config(self) -> None:
        """Save current configuration to file"""
        config = {
            "device_info": self.device_info,
            "pytorch_version": torch.__version__,
            "timestamp": str(torch.utils.data.get_worker_info() or "unknown"),
        }

        with open(self.config_file, "w") as f:
            json.dump(config, f, indent=2, default=str)

        logger.info("Configuration saved to {self.config_file}")

    def load_config(self) -> Optional[dict[str, Any]]:
        """Load configuration from file"""
        if self.config_file.exists():
            try:
                with open(self.config_file) as f:
                    data = json.load(f)
                if isinstance(data, dict):
                    return cast(dict[str, Any], data)
            except Exception:
                logger.exception("Failed to load config: {e}")
        return None

    def benchmark_device(
        self,
        size: int = 1000,
        iterations: int = 10,
    ) -> dict[str, float | int | str]:
        """Benchmark device performance"""
        import time

        logger.info("Benchmarking {self.device} with {size}x{size} matrices...")

        # Warm up
        x = torch.randn(size, size, device=self.device)
        y = torch.randn(size, size, device=self.device)
        _ = torch.mm(x, y)

        # Benchmark matrix multiplication
        start_time = time.time()
        for _ in range(iterations):
            torch.mm(x, y)
            if self.device.type == "cuda":
                torch.cuda.synchronize()  # Wait for GPU operations

        total_time = time.time() - start_time

        benchmark_results = {
            "device": str(self.device),
            "matrix_size": size,
            "iterations": iterations,
            "total_time_seconds": total_time,
            "average_time_ms": (total_time / iterations) * 1000,
            "operations_per_second": iterations / total_time,
        }

        logger.info(
            f"Benchmark results: {benchmark_results['average_time_ms']:.2f}ms per operation",
        )

        return cast(dict[str, float | int | str], benchmark_results)

    def __str__(self) -> str:
        """String representation of GPU manager"""
        return f"UniversalGPUManager(device={self.device}, type={self.device_info['type']})"

    def __repr__(self) -> str:
        """Detailed representation of GPU manager"""
        return f"UniversalGPUManager(device_info={self.device_info})"


# Convenience function for quick setup
def get_optimal_device(prefer_device: Optional[str] = None) -> torch.device:
    """Quick function to get optimal PyTorch device"""
    manager = UniversalGPUManager(prefer_device)
    return manager.get_device()


# Example usage
if __name__ == "__main__":
    # Initialize GPU manager
    gpu_manager = UniversalGPUManager()

    print(f"Optimal device: {gpu_manager.get_device()}")
    print(f"Device info: {gpu_manager.get_info()}")
    print(f"Memory info: {gpu_manager.get_memory_info()}")

    # Benchmark performance
    benchmark = gpu_manager.benchmark_device(size=500, iterations=5)
    print(f"Benchmark: {benchmark}")

    # Save configuration
    gpu_manager.save_config()
