"""
Boundary shims for ML libraries to isolate type issues.

These Protocol and TypedDict wrappers provide clean type boundaries
between our typed code and external ML libraries with unknown types.
"""

from typing import Any, Protocol, TypedDict, Union

import numpy as np
import torch
from PIL import Image


# GPU Monitoring Protocol
class GPUDevice(Protocol):
    """Type protocol for GPU device information."""
    name: str
    load: float  # Utilization as a fraction (0-1)
    memoryUsed: int  # Memory used in MB
    memoryTotal: int  # Total memory in MB
    memoryUtil: float  # Memory utilization as a fraction (0-1)
    temperature: int  # Temperature in Celsius


# YOLO Detection Types
class YOLOBox(TypedDict):
    """Bounding box detection result."""
    class_name: str
    confidence: float
    bbox: list[int]  # [x1, y1, x2, y2]


class YOLOResult(TypedDict):
    """Complete YOLO detection result."""
    prediction: str
    confidence: float
    detections: list[YOLOBox]
    model: str
    total_objects: int


class YOLOModel(Protocol):
    """Type protocol for YOLO model interface."""
    names: dict[int, str]

    def __call__(
        self,
        source: Any,
        conf: float = 0.5,
        verbose: bool = False,
        **kwargs: Any
    ) -> list[Any]: ...


# CLIP Analysis Types
class CLIPResult(TypedDict):
    """CLIP image analysis result."""
    prediction: str
    confidence: float
    scores: list[dict[str, Any]]
    model: str


class CLIPModel(Protocol):
    """Type protocol for CLIP model interface."""

    def encode_image(self, tensor: torch.Tensor) -> torch.Tensor: ...
    def encode_text(self, tokens: torch.Tensor) -> torch.Tensor: ...


# Preprocessing Protocol
class ImagePreprocessor(Protocol):
    """Type protocol for image preprocessing functions."""

    def __call__(self, image: Image.Image) -> torch.Tensor: ...


# Sentence Transformer Types
class SentenceTransformerModel(Protocol):
    """Type protocol for sentence transformer interface."""

    def encode(self, inputs: list[Union[str, Image.Image]]) -> np.ndarray[Any, np.dtype[np.float32]]: ...


# GPU Manager safe wrapper functions
def safe_get_gpu_stats() -> dict[str, Any]:
    """Safely get GPU statistics with type isolation."""
    try:
        import GPUtil  # type: ignore[import]
        gpus: list[Any] = GPUtil.getGPUs()  # type: ignore[attr-defined]
        if not gpus:
            return {"available": False, "error": "No GPUs found"}

        gpu: Any = gpus[0]  # Get first GPU
        return {
            "available": True,
            "gpu_name": str(gpu.name),
            "gpu_utilization": f"{float(gpu.load) * 100:.1f}%",
            "memory_used": f"{int(gpu.memoryUsed)}MB",
            "memory_total": f"{int(gpu.memoryTotal)}MB",
            "memory_utilization": f"{float(gpu.memoryUtil) * 100:.1f}%",
            "temperature": f"{int(gpu.temperature)}°C",
        }
    except Exception as e:
        return {"available": False, "error": str(e)}


# YOLO safe wrapper functions
def safe_yolo_detect(
    model: Any,  # Accept any model and handle safely
    image: Any,  # More flexible for YOLO input
    confidence: float = 0.5
) -> YOLOResult:
    """Safely perform YOLO detection with type isolation."""
    try:
        results = model(image, conf=confidence, verbose=False)
        detections: list[YOLOBox] = []
        total_confidence = 0.0

        for result in results:
            if hasattr(result, 'boxes') and result.boxes is not None:
                for box in result.boxes:
                    # Extract data safely with explicit type conversion
                    class_id = int(box.cls[0].item())
                    class_name = str(model.names[class_id])
                    conf = float(box.conf[0].item())
                    coords = box.xyxy[0].cpu().numpy()
                    x1, y1, x2, y2 = map(int, coords)

                    detections.append(YOLOBox(
                        class_name=class_name,
                        confidence=conf,
                        bbox=[x1, y1, x2, y2]
                    ))
                    total_confidence += conf

        if detections:
            # Sort by confidence
            detections.sort(key=lambda x: x["confidence"], reverse=True)
            top_detection = detections[0]
            prediction = f"{len(detections)} objects: {top_detection['class_name']}"
            confidence = min(0.99, total_confidence / len(detections))
        else:
            prediction = "no_objects_detected"
            confidence = 0.1

        return YOLOResult(
            prediction=prediction,
            confidence=confidence,
            detections=detections,
            model="YOLOv8n",
            total_objects=len(detections)
        )

    except Exception:
        return YOLOResult(
            prediction="detection_failed",
            confidence=0.0,
            detections=[],
            model="YOLOv8n",
            total_objects=0
        )


# CLIP safe wrapper functions
def safe_clip_analyze(
    model: Any,  # Accept any model and handle safely
    processor: Any,
    image: Any,
    text_categories: list[str],
    device: str = "cpu"
) -> CLIPResult:
    """Safely perform CLIP image analysis with type isolation."""
    try:
        inputs = processor(
            text=text_categories,
            images=image,
            return_tensors="pt",
            padding=True
        )
        inputs = {k: v.to(device) for k, v in inputs.items()}

        with torch.no_grad():
            outputs = model(**inputs)
            logits_per_image = outputs.logits_per_image
            probs = logits_per_image.softmax(dim=1)

        # Get top prediction with explicit type handling
        max_result = torch.max(probs, dim=1)  # type: ignore[call-overload]
        max_prob = max_result.values
        max_idx = max_result.indices

        prediction = str(text_categories[int(max_idx.item())])
        confidence = float(max_prob.item())

        # Create full scores list with explicit typing
        scores: list[dict[str, Any]] = []
        for i, category in enumerate(text_categories):
            score_dict: dict[str, Any] = {
                "category": str(category),
                "confidence": float(probs[0][i].item())
            }
            scores.append(score_dict)

        # Sort by confidence
        scores.sort(key=lambda x: float(x["confidence"]), reverse=True)

        return CLIPResult(
            prediction=prediction,
            confidence=confidence,
            scores=scores,
            model="CLIP"
        )

    except Exception:
        return CLIPResult(
            prediction="analysis_failed",
            confidence=0.0,
            scores=[],
            model="CLIP"
        )


def safe_sentence_transformer_encode(
    model: Any,
    inputs: Union[str, list[str], Image.Image, list[Image.Image]],
    **kwargs: Any
) -> np.ndarray[Any, np.dtype[np.float32]]:
    """Safely encode inputs with sentence transformer model."""
    try:
        # Handle the complex overload signature by passing through
        result = model.encode(inputs, **kwargs)
        if isinstance(result, np.ndarray):
            return result.astype(np.float32)
        else:
            # Convert tensor to numpy if needed
            return np.array(result, dtype=np.float32)
    except Exception:
        # Return empty embedding on failure
        return np.array([]).astype(np.float32)
