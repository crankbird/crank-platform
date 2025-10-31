#!/usr/bin/env python3
"""
Real Image Test - Download and test with actual photos
"""

import asyncio
import time
import httpx
import ssl
from pathlib import Path

async def test_with_real_image():
    """Test both classifiers with a real photo."""
    
    print("🌍 Testing with real image...")
    
    # Download a test image
    image_url = "https://upload.wikimedia.org/wikipedia/commons/thumb/4/47/PNG_transparency_demonstration_1.png/280px-PNG_transparency_demonstration_1.png"
    
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    
    async with httpx.AsyncClient(verify=False, timeout=60.0) as client:
        # Download image
        print(f"📥 Downloading test image...")
        response = await client.get(image_url)
        image_data = response.content
        print(f"   Image size: {len(image_data):,} bytes")
        
        # Test CPU classifier
        print(f"\n🖥️  Testing CPU Classifier...")
        files = {'file': ('real_image.png', image_data, 'image/png')}
        data = {'classification_types': 'object_detection,scene_classification,content_safety'}
        
        start_time = time.time()
        cpu_response = await client.post("https://localhost:8006/classify", files=files, data=data)
        cpu_time = time.time() - start_time
        
        if cpu_response.status_code == 200:
            cpu_result = cpu_response.json()
            print(f"   ⏱️  CPU Time: {cpu_time:.3f}s")
            print(f"   📊 CPU Results: {len(cpu_result.get('results', []))} classifications")
            for res in cpu_result.get('results', []):
                print(f"      {res.get('classification_type')}: {res.get('prediction')} ({res.get('confidence', 0):.3f})")
        
        # Test GPU classifier  
        print(f"\n🎮 Testing GPU Classifier...")
        files = {'file': ('real_image.png', image_data, 'image/png')}
        data = {'classification_types': 'yolo_detection,clip_analysis,advanced_scene_analysis'}
        
        start_time = time.time()
        gpu_response = await client.post("https://localhost:8008/classify", files=files, data=data)
        gpu_time = time.time() - start_time
        
        if gpu_response.status_code == 200:
            gpu_result = gpu_response.json()
            print(f"   ⏱️  GPU Time: {gpu_time:.3f}s")
            print(f"   📊 GPU Results: {len(gpu_result.get('results', []))} classifications")
            for res in gpu_result.get('results', []):
                print(f"      {res.get('classification_type')}: {res.get('prediction')} ({res.get('confidence', 0):.3f})")
            
            # Show GPU stats
            gpu_stats = gpu_result.get('gpu_stats', {})
            print(f"   🎮 GPU: {gpu_stats.get('gpu_name', 'Unknown')}")
            print(f"   💾 Memory: {gpu_stats.get('memory_used', '?')}/{gpu_stats.get('memory_total', '?')}")
            print(f"   🔥 Utilization: {gpu_stats.get('gpu_utilization', '?')}%")
        
        # Compare performance
        if cpu_response.status_code == 200 and gpu_response.status_code == 200:
            speedup = cpu_time / gpu_time if gpu_time > 0 else float('inf')
            print(f"\n📈 Performance Comparison:")
            print(f"   CPU: {cpu_time:.3f}s")
            print(f"   GPU: {gpu_time:.3f}s")
            print(f"   Speedup: {speedup:.2f}x {'🚀' if speedup > 1 else '🐌'}")

if __name__ == "__main__":
    asyncio.run(test_with_real_image())