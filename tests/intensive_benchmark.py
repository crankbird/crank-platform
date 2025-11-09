#!/usr/bin/env python3
"""
GPU vs CPU Intensive Processing Test
Tests the difference in processing intensive tasks between CPU and GPU
"""

import asyncio
import random
import ssl
import time
from io import BytesIO

import httpx
from PIL import Image, ImageDraw, ImageFilter


def create_complex_test_image(size: tuple[int, int] = (1920, 1080)) -> Image.Image:
    """Create a complex image that will exercise the classifiers."""
    img = Image.new("RGB", size, color="white")
    draw = ImageDraw.Draw(img)

    # Create a complex scene with many objects
    colors = ["red", "blue", "green", "yellow", "purple", "orange", "pink", "cyan"]

    # Add background gradient
    for y in range(size[1]):
        color_val = int(255 * (y / size[1]))
        for x in range(0, size[0], 10):
            draw.line([(x, y), (x + 10, y)], fill=(color_val // 3, color_val // 2, color_val))

    # Add many random objects
    for i in range(50):
        x = random.randint(0, size[0] - 200)
        y = random.randint(0, size[1] - 200)
        w = random.randint(50, 150)
        h = random.randint(50, 150)
        color = random.choice(colors)

        if i % 4 == 0:
            # Rectangle
            draw.rectangle([x, y, x + w, y + h], fill=color, outline="black", width=2)
        elif i % 4 == 1:
            # Circle
            draw.ellipse([x, y, x + w, y + h], fill=color, outline="black", width=2)
        elif i % 4 == 2:
            # Triangle
            draw.polygon(
                [(x, y + h), (x + w // 2, y), (x + w, y + h)],
                fill=color,
                outline="black",
                width=2,
            )
        else:
            # Star
            points = []
            for angle in range(0, 360, 36):
                r = w // 2 if angle % 72 == 0 else w // 4
                px = x + w // 2 + int(r * 0.8)
                py = y + h // 2 + int(r * 0.6)
                points.append((px, py))
            draw.polygon(points, fill=color, outline="black", width=2)

    # Add text
    draw.text((50, 50), "GPU PERFORMANCE TEST", fill="black")
    draw.text((50, 100), "Complex Scene Analysis", fill="darkblue")

    # Apply some filters to make it more interesting
    return img.filter(ImageFilter.DETAIL)


def image_to_bytes(img: Image.Image, quality: int = 90) -> bytes:
    """Convert PIL image to bytes."""
    img_buffer = BytesIO()
    img.save(img_buffer, format="JPEG", quality=quality)
    return img_buffer.getvalue()


async def benchmark_performance() -> None:
    """Run an intensive performance benchmark."""

    print("🔥 INTENSIVE GPU vs CPU PERFORMANCE BENCHMARK")
    print("=" * 70)

    # Create large, complex image
    print("🎨 Creating complex test image (1920x1080)...")
    complex_img = create_complex_test_image((1920, 1080))
    image_data = image_to_bytes(complex_img, quality=95)
    print(f"   Complex image size: {len(image_data):,} bytes")

    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE

    # Test multiple rounds
    cpu_times: list[float] = []
    gpu_times: list[float] = []

    async with httpx.AsyncClient(verify=False, timeout=120.0) as client:
        for round_num in range(3):
            print(f"\n🏁 Round {round_num + 1}/3")
            print("-" * 40)

            # CPU Test
            print("🖥️  CPU Intensive Processing...")
            files = {"file": ("complex_image.jpg", image_data, "image/jpeg")}
            data = {
                "classification_types": "object_detection,scene_classification,content_safety,image_quality,dominant_colors,text_detection",
            }

            start_time = time.time()
            try:
                cpu_response = await client.post(
                    "https://localhost:8006/classify",
                    files=files,
                    data=data,
                )
                cpu_time = time.time() - start_time

                if cpu_response.status_code == 200:
                    cpu_result = cpu_response.json()
                    cpu_times.append(cpu_time)
                    print(f"   ✅ CPU completed in {cpu_time:.3f}s")
                    print(
                        f"   📊 Processed {len(cpu_result.get('results', []))} classification types",
                    )
                else:
                    print(f"   ❌ CPU failed: {cpu_response.status_code}")

            except Exception as e:
                cpu_time = time.time() - start_time
                print(f"   ❌ CPU error after {cpu_time:.3f}s: {e}")

            # GPU Test
            print("\n🎮 GPU Intensive Processing...")
            files = {"file": ("complex_image.jpg", image_data, "image/jpeg")}
            data = {
                "classification_types": "yolo_detection,clip_analysis,advanced_scene_analysis,image_embeddings",
            }

            start_time = time.time()
            try:
                gpu_response = await client.post(
                    "https://localhost:8008/classify",
                    files=files,
                    data=data,
                )
                gpu_time = time.time() - start_time

                if gpu_response.status_code == 200:
                    gpu_result = gpu_response.json()
                    gpu_times.append(gpu_time)
                    print(f"   ✅ GPU completed in {gpu_time:.3f}s")
                    print(
                        f"   📊 Processed {len(gpu_result.get('results', []))} classification types",
                    )

                    # Show GPU utilization
                    gpu_stats = gpu_result.get("gpu_stats", {})
                    if gpu_stats:
                        print(f"   🎮 GPU Utilization: {gpu_stats.get('gpu_utilization', '?')}%")
                        print(
                            f"   💾 GPU Memory: {gpu_stats.get('memory_used', '?')}/{gpu_stats.get('memory_total', '?')}",
                        )
                else:
                    print(f"   ❌ GPU failed: {gpu_response.status_code}")

            except Exception as e:
                gpu_time = time.time() - start_time
                print(f"   ❌ GPU error after {gpu_time:.3f}s: {e}")

            # Round comparison
            if cpu_times and gpu_times and len(cpu_times) == len(gpu_times):
                current_speedup = cpu_times[-1] / gpu_times[-1]
                print(
                    f"\n   📈 Round {round_num + 1} Speedup: {current_speedup:.2f}x {'🚀' if current_speedup > 1 else '🐌'}",
                )

            await asyncio.sleep(1)  # Brief pause between rounds

    # Final analysis
    print("\n🏆 FINAL BENCHMARK RESULTS")
    print("=" * 70)

    if cpu_times and gpu_times:
        avg_cpu = sum(cpu_times) / len(cpu_times)
        avg_gpu = sum(gpu_times) / len(gpu_times)
        avg_speedup = avg_cpu / avg_gpu

        print(
            f"CPU Average: {avg_cpu:.3f}s (best: {min(cpu_times):.3f}s, worst: {max(cpu_times):.3f}s)",
        )
        print(
            f"GPU Average: {avg_gpu:.3f}s (best: {min(gpu_times):.3f}s, worst: {max(gpu_times):.3f}s)",
        )
        print(f"\n🎯 Average GPU Speedup: {avg_speedup:.2f}x")

        if avg_speedup > 2:
            print("🚀 SIGNIFICANT GPU ADVANTAGE! GPU is much faster for complex processing.")
        elif avg_speedup > 1.2:
            print("⚡ MODERATE GPU ADVANTAGE! GPU shows performance benefits.")
        elif avg_speedup > 0.8:
            print("🤝 SIMILAR PERFORMANCE! Both CPU and GPU perform comparably.")
        else:
            print("🖥️  CPU ADVANTAGE! CPU performs better for this workload.")

        print("\nDetailed timings:")
        for i, (cpu_t, gpu_t) in enumerate(zip(cpu_times, gpu_times)):
            speedup = cpu_t / gpu_t
            print(f"  Round {i + 1}: CPU {cpu_t:.3f}s, GPU {gpu_t:.3f}s ({speedup:.2f}x)")

    else:
        print("❌ Could not complete benchmark - some tests failed")


if __name__ == "__main__":
    asyncio.run(benchmark_performance())
