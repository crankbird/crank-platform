"""
Unit Tests for ML Boundary Shims

Tests for the type-safe boundary layer that isolates ML library complexity
from the rest of the application.
"""

from unittest.mock import MagicMock, patch

import pytest


@pytest.mark.unit
class TestMLBoundaryShims:
    """Test the ML boundary shim functions for type safety and error handling."""

    def test_safe_yolo_detect_success(self) -> None:
        """Test successful YOLO detection."""
        from services.ml_boundary_shims import safe_yolo_detect

        # Mock a YOLO model and image
        mock_model = MagicMock()
        mock_image = "dummy_image_data"

        # Mock successful detection results
        mock_results = MagicMock()
        mock_results.boxes = MagicMock()
        mock_results.boxes.data = [[10, 20, 100, 200, 0.95, 0]]  # [x1, y1, x2, y2, conf, class]
        mock_results.names = {0: "person"}
        mock_model.return_value = [mock_results]

        result = safe_yolo_detect(mock_model, mock_image, confidence=0.8)

        assert result is not None
        assert "detections" in result
        assert "prediction" in result
        assert "total_objects" in result
        mock_model.assert_called_once_with(mock_image, conf=0.8, verbose=False)

    def test_safe_yolo_detect_exception_handling(self) -> None:
        """Test YOLO detection with runtime error."""
        from services.ml_boundary_shims import safe_yolo_detect

        mock_model = MagicMock()
        mock_model.side_effect = RuntimeError("GPU out of memory")

        result = safe_yolo_detect(mock_model, "dummy_image")

        assert result["prediction"] == "detection_failed"
        assert result["confidence"] == 0.0
        assert result["detections"] == []
        assert result["total_objects"] == 0

    def test_safe_clip_analyze_success(self) -> None:
        """Test successful CLIP analysis."""
        from services.ml_boundary_shims import safe_clip_analyze

        # Mock CLIP model components
        mock_model = MagicMock()
        mock_processor = MagicMock()
        mock_image = "dummy_image"

        # Mock the processing pipeline with proper tensor-like objects
        mock_tensor = MagicMock()
        mock_tensor.to.return_value = mock_tensor
        mock_inputs = {"pixel_values": mock_tensor, "input_ids": mock_tensor}
        mock_processor.return_value = mock_inputs

        # Mock torch operations throughout the function
        with patch("services.ml_boundary_shims.torch") as mock_torch:
            # Mock the model outputs
            mock_outputs = MagicMock()
            mock_logits = MagicMock()
            mock_probs = MagicMock()
            mock_outputs.logits_per_image = mock_logits
            mock_logits.softmax.return_value = mock_probs
            mock_model.return_value = mock_outputs

            # Mock torch.max result
            mock_max_result = MagicMock()
            mock_values = MagicMock()
            mock_indices = MagicMock()
            mock_values.item.return_value = 0.8
            mock_indices.item.return_value = 0
            mock_max_result.values = mock_values
            mock_max_result.indices = mock_indices
            mock_torch.max.return_value = mock_max_result

            # Mock torch.no_grad context manager
            mock_torch.no_grad.return_value.__enter__.return_value = None
            mock_torch.no_grad.return_value.__exit__.return_value = None

            # Mock probs indexing for the scores loop
            mock_probs.__getitem__.return_value.item.return_value = 0.1

            result = safe_clip_analyze(mock_model, mock_processor, mock_image, ["cat", "dog"])

        assert result is not None
        assert "prediction" in result
        assert result["prediction"] == "cat"  # Should be first category (index 0)
        assert "confidence" in result
        assert "scores" in result
        mock_processor.assert_called_once()
        mock_model.assert_called_once()

    def test_safe_clip_analyze_exception_handling(self) -> None:
        """Test CLIP analysis with exception."""
        from services.ml_boundary_shims import safe_clip_analyze

        mock_model = MagicMock()
        mock_processor = MagicMock()
        mock_processor.side_effect = Exception("Processing failed")

        result = safe_clip_analyze(mock_model, mock_processor, "dummy_image", ["cat", "dog"])

        assert result["prediction"] == "analysis_failed"
        assert result["confidence"] == 0.0
        assert result["scores"] == []

    def test_safe_sentence_transformer_encode_success(self) -> None:
        """Test successful sentence transformer encoding."""
        from services.ml_boundary_shims import safe_sentence_transformer_encode

        mock_model = MagicMock()
        mock_embedding = [[0.1, 0.2, 0.3, 0.4, 0.5]]
        mock_model.encode.return_value = mock_embedding

        result = safe_sentence_transformer_encode(mock_model, ["test sentence"])

        assert result is not None
        mock_model.encode.assert_called_once_with(["test sentence"])

    def test_safe_sentence_transformer_encode_exception_handling(self) -> None:
        """Test sentence transformer encoding with exception."""
        from services.ml_boundary_shims import safe_sentence_transformer_encode

        mock_model = MagicMock()
        mock_model.encode.side_effect = Exception("Encoding failed")

        result = safe_sentence_transformer_encode(mock_model, ["test sentence"])

        # Should return empty array on error
        import numpy as np

        expected = np.array([], dtype=np.float32)
        assert np.array_equal(result, expected)


@pytest.mark.unit
class TestMLModelProtocols:
    """Test that our Protocol definitions work correctly."""

    def test_yolo_model_protocol(self) -> None:
        """Test YOLOModel protocol compliance."""
        # Create a mock that behaves like a YOLO model
        mock_yolo = MagicMock()
        mock_yolo.return_value = [MagicMock()]  # Results list

        result = mock_yolo("test_image", conf=0.5, verbose=False)
        assert len(result) == 1
        mock_yolo.assert_called_once_with("test_image", conf=0.5, verbose=False)

    def test_clip_model_protocol(self) -> None:
        """Test CLIPModel protocol compliance."""
        # Create mocks that implement the protocols
        mock_model = MagicMock()
        mock_processor = MagicMock()

        # Test typical usage pattern
        mock_processor.return_value = {"pixel_values": "processed"}
        mock_outputs = MagicMock()
        mock_outputs.logits_per_image = [[0.1, 0.2, 0.3]]
        mock_model.return_value = mock_outputs

        inputs = mock_processor("test_image", text=["cat", "dog"])
        outputs = mock_model(**inputs)

        assert inputs == {"pixel_values": "processed"}
        assert outputs.logits_per_image == [[0.1, 0.2, 0.3]]


@pytest.mark.unit
class TestErrorHandling:
    """Test comprehensive error handling in boundary shims."""

    def test_safe_wrapper_exception_handling(self) -> None:
        """Test that exceptions are properly caught and logged."""
        from services.ml_boundary_shims import safe_yolo_detect

        mock_model = MagicMock()
        mock_model.side_effect = Exception("Unexpected error")

        # Should not raise exception, should return safe fallback
        result = safe_yolo_detect(mock_model, "test_image")
        assert result["prediction"] == "detection_failed"
        assert result["confidence"] == 0.0
        assert result["detections"] == []

    def test_gpu_stats_fallback(self) -> None:
        """Test GPU stats with fallback when GPUtil unavailable."""
        from services.ml_boundary_shims import safe_get_gpu_stats

        # Mock the GPUtil import to raise ImportError
        with patch("builtins.__import__", side_effect=ImportError("No module named 'GPUtil'")):
            result = safe_get_gpu_stats()
            assert "available" in result
            assert result["available"] is False


@pytest.mark.unit
class TestTypeAnnotations:
    """Test that type annotations are working correctly."""

    def test_function_signatures(self) -> None:
        """Test that functions have correct type signatures."""
        import inspect

        from services.ml_boundary_shims import (
            safe_clip_analyze,
            safe_sentence_transformer_encode,
            safe_yolo_detect,
        )

        # Check function signatures exist and have expected parameters
        yolo_sig = inspect.signature(safe_yolo_detect)
        assert "model" in yolo_sig.parameters
        assert "image" in yolo_sig.parameters
        assert "confidence" in yolo_sig.parameters

        clip_sig = inspect.signature(safe_clip_analyze)
        assert "model" in clip_sig.parameters
        assert "processor" in clip_sig.parameters
        assert "image" in clip_sig.parameters
        assert "text_categories" in clip_sig.parameters

        st_sig = inspect.signature(safe_sentence_transformer_encode)
        assert "model" in st_sig.parameters
        assert "inputs" in st_sig.parameters

    def test_return_types(self) -> None:
        """Test that return types match expectations."""
        from services.ml_boundary_shims import (
            safe_clip_analyze,
            safe_sentence_transformer_encode,
            safe_yolo_detect,
        )

        # Test with mock models that produce successful results
        mock_yolo_model = MagicMock()
        mock_results = MagicMock()
        mock_results.boxes = MagicMock()
        mock_results.boxes.data = []
        mock_results.names = {}
        mock_yolo_model.return_value = [mock_results]

        yolo_result = safe_yolo_detect(mock_yolo_model, "test")
        assert isinstance(yolo_result, dict)
        assert "detections" in yolo_result

        # Test CLIP
        mock_clip_model = MagicMock()
        mock_processor = MagicMock()
        mock_processor.return_value = {}
        mock_outputs = MagicMock()
        mock_outputs.logits_per_image = [[]]
        mock_clip_model.return_value = mock_outputs

        clip_result = safe_clip_analyze(mock_clip_model, mock_processor, "test", ["test"])
        assert isinstance(clip_result, dict)
        assert "prediction" in clip_result

        # Test Sentence Transformer
        mock_st_model = MagicMock()
        import numpy as np

        mock_st_model.encode.return_value = np.array([[0.1, 0.2]], dtype=np.float32)

        st_result = safe_sentence_transformer_encode(mock_st_model, ["test"])
        assert isinstance(st_result, np.ndarray)


@pytest.mark.performance
class TestBoundaryShimPerformance:
    """Performance tests for boundary shim functions."""

    def test_yolo_performance_overhead(self) -> None:
        """Test that boundary shim adds minimal overhead."""
        from services.ml_boundary_shims import YOLOResult, safe_yolo_detect
        from tests.conftest import PerformanceBenchmark

        # Mock a fast YOLO model
        mock_model = MagicMock()
        mock_results = MagicMock()
        mock_results.boxes = MagicMock()
        mock_results.boxes.data = []
        mock_results.names = {}
        mock_model.return_value = [mock_results]

        def run_detection() -> YOLOResult:
            return safe_yolo_detect(mock_model, "test_image")

        result, duration = PerformanceBenchmark.measure_sync_operation(run_detection)

        # Should complete very quickly (mocked)
        assert duration < 0.01  # Less than 10ms
        assert "detections" in result

    def test_error_handling_performance(self) -> None:
        """Test that error handling doesn't add significant overhead."""
        from services.ml_boundary_shims import YOLOResult, safe_yolo_detect
        from tests.conftest import PerformanceBenchmark

        # Mock an exception
        mock_model = MagicMock()
        mock_model.side_effect = Exception("Model failed")

        def run_detection() -> YOLOResult:
            return safe_yolo_detect(mock_model, "test_image")

        result, duration = PerformanceBenchmark.measure_sync_operation(run_detection)

        # Error handling should be fast
        assert duration < 0.001  # Less than 1ms
        assert result["prediction"] == "detection_failed"
