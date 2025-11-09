#!/usr/bin/env python3
"""
CPU vs GPU Image Classifier Performance Comparison

Tests the same image classification tasks on both CPU and GPU workers
to demonstrate the performance benefits of GPU acceleration.
"""

import asyncio
import ssl
import statistics
import time
from io import BytesIO
from typing import Any

import httpx
from PIL import Image, ImageDraw


# Create a test image
def create_test_image(size: tuple[int, int] = (800, 600)) -> Image.Image:
    """Create a test image with various objects for classification."""
    img = Image.new("RGB", size, color="lightblue")
    draw = ImageDraw.Draw(img)

    # Draw some shapes to test object detection
    draw.rectangle([50, 50, 200, 200], fill="red", outline="black", width=3)
    draw.ellipse([300, 100, 500, 300], fill="green", outline="black", width=3)
    draw.polygon([(600, 50), (750, 50), (675, 200)], fill="yellow", outline="black", width=3)

    # Add some text patterns
    draw.text((60, 350), "PERFORMANCE TEST IMAGE", fill="black")
    draw.text((60, 400), "GPU vs CPU Comparison", fill="darkblue")

    # Add more complex patterns
    for i in range(10):
        x = 60 + i * 60
        y = 450 + (i % 3) * 30
        draw.circle((x, y), 15, fill=f"rgb({50 + i * 20}, {100}, {200 - i * 15})")

    return img


def image_to_bytes(img: Image.Image) -> bytes:
    """Convert PIL image to bytes."""
    img_buffer = BytesIO()
    img.save(img_buffer, format="JPEG", quality=95)
    return img_buffer.getvalue()


async def _classifier_helper(
    endpoint: str,
    image_data: bytes,
    classification_types: str,
    label: str,
) -> tuple[float | None, dict[str, Any] | None]:
    """Helper function to test a classifier endpoint and measure response time."""

    # Create SSL context that ignores certificate verification (for self-signed certs)
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE

    async with httpx.AsyncClient(verify=False, timeout=60.0) as client:
        files = {"file": ("test_image.jpg", image_data, "image/jpeg")}
        data = {"classification_types": classification_types}

        start_time = time.time()
        try:
            response = await client.post(endpoint, files=files, data=data)
            end_time = time.time()

            if response.status_code == 200:
                result = response.json()
                duration = end_time - start_time

                print(f"\n🎯 {label} Results:")
                print(f"   ⏱️  Response Time: {duration:.3f} seconds")
                print(f"   📊 Status: {result.get('success', False)}")
                print(f"   🔍 Results Count: {len(result.get('results', []))}")

                # Show classification results
                for _i, res in enumerate(result.get("results", [])):
                    conf = res.get("confidence", 0)
                    pred = res.get("prediction", "unknown")
                    class_type = res.get("classification_type", "unknown")
                    print(f"   📋 {class_type}: {pred} (confidence: {conf:.3f})")

                # Show GPU stats if available
                gpu_stats = result.get("gpu_stats")
                if gpu_stats:
                    print(f"   🎮 GPU: {gpu_stats.get('gpu_name', 'Unknown')}")
                    print(
                        f"   💾 GPU Memory: {gpu_stats.get('memory_used', 'Unknown')}/{gpu_stats.get('memory_total', 'Unknown')}",
                    )
                    print(f"   🔥 GPU Utilization: {gpu_stats.get('gpu_utilization', 'Unknown')}")

                return duration, result

            print(f"❌ {label} Error: {response.status_code} - {response.text}")
            return None, None

        except Exception as e:
            end_time = time.time()
            duration = end_time - start_time
            print(f"❌ {label} Exception after {duration:.3f}s: {e}")
            return None, None


async def run_performance_comparison() -> None:
    """Run the performance comparison between CPU and GPU classifiers."""

    print("🚀 CPU vs GPU Image Classifier Performance Test")
    print("=" * 60)

    # Create test image
    print("📸 Creating test image...")
    test_img = create_test_image((1024, 768))  # Larger image for better test
    image_data = image_to_bytes(test_img)
    print(f"   Image size: {len(image_data):,} bytes ({test_img.size[0]}x{test_img.size[1]})")

    # Define endpoints
    cpu_endpoint = "https://localhost:8006/classify"  # CPU classifier
    gpu_endpoint = "https://localhost:8008/classify"  # GPU classifier

    # Test scenarios
    scenarios = [
        {
            "name": "Basic Classification",
            "types": "object_detection,scene_classification",
            "description": "Object detection and scene analysis",
        },
        {
            "name": "Advanced GPU Features",
            "types": "yolo_detection,clip_analysis,advanced_scene_classification",
            "description": "GPU-specific advanced features",
        },
    ]

    results: dict[str, list[Any]] = {
        "cpu_times": [],
        "gpu_times": [],
        "cpu_results": [],
        "gpu_results": [],
    }

    for scenario in scenarios:
        print(f"\n🔬 Testing Scenario: {scenario['name']}")
        print(f"   Description: {scenario['description']}")
        print(f"   Types: {scenario['types']}")

        # Test CPU classifier
        print("\n   Testing CPU Classifier...")
        cpu_time, cpu_result = await _classifier_helper(
            cpu_endpoint,
            image_data,
            scenario["types"],
            "CPU Classifier",
        )

        # Test GPU classifier
        print("\n   Testing GPU Classifier...")
        gpu_time, gpu_result = await _classifier_helper(
            gpu_endpoint,
            image_data,
            scenario["types"],
            "GPU Classifier",
        )

        # Store results
        if cpu_time is not None:
            results["cpu_times"].append(cpu_time)
            results["cpu_results"].append(cpu_result)

        if gpu_time is not None:
            results["gpu_times"].append(gpu_time)
            results["gpu_results"].append(gpu_result)

        # Show comparison for this scenario
        if cpu_time and gpu_time:
            speedup = cpu_time / gpu_time
            print("\n   📈 Scenario Performance:")
            print(f"      CPU Time: {cpu_time:.3f}s")
            print(f"      GPU Time: {gpu_time:.3f}s")
            print(f"      Speedup: {speedup:.2f}x {'🚀' if speedup > 1 else '🐌'}")

    # Overall performance summary
    print("\n🏆 OVERALL PERFORMANCE SUMMARY")
    print("=" * 60)

    if results["cpu_times"] and results["gpu_times"]:
        cpu_avg = statistics.mean(results["cpu_times"])
        gpu_avg = statistics.mean(results["gpu_times"])
        overall_speedup = cpu_avg / gpu_avg

        print(f"CPU Average Response Time: {cpu_avg:.3f}s")
        print(f"GPU Average Response Time: {gpu_avg:.3f}s")
        print(f"Overall GPU Speedup: {overall_speedup:.2f}x")

        if overall_speedup > 1:
            print(f"🎉 GPU is {overall_speedup:.2f}x FASTER than CPU!")
        elif overall_speedup < 1:
            print(f"⚠️  CPU is {1 / overall_speedup:.2f}x faster than GPU (unexpected)")
        else:
            print("🤝 CPU and GPU performance are similar")

        # Show individual times
        print("\n📊 Individual Response Times:")
        for i, (cpu_t, gpu_t) in enumerate(zip(results["cpu_times"], results["gpu_times"])):
            speedup = cpu_t / gpu_t
            print(f"   Test {i + 1}: CPU {cpu_t:.3f}s, GPU {gpu_t:.3f}s (speedup: {speedup:.2f}x)")

    else:
        print("❌ Could not complete performance comparison - some tests failed")

    print("\n✅ Performance test completed!")


if __name__ == "__main__":
    asyncio.run(run_performance_comparison())
