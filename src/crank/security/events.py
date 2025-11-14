"""
Certificate Lifecycle Events and Observability

Provides event emission, structured logging, and metrics hooks for
certificate operations. All certificate lifecycle transitions emit
events that can be consumed for alerting, metrics, and audit trails.
"""

import logging
import uuid
from datetime import UTC, datetime
from enum import Enum
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)


class CertificateEvent(str, Enum):
    """Certificate lifecycle events for observability."""

    # Successful operations
    CERT_ISSUED = "cert_issued"
    CERT_RENEWED = "cert_renewed"
    CSR_GENERATED = "csr_generated"
    CSR_SUBMITTED = "csr_submitted"

    # Warning states
    CERT_EXPIRING_SOON = "cert_expiring_soon"

    # Error states
    CERT_EXPIRED = "cert_expired"
    CERT_VALIDATION_FAILED = "cert_validation_failed"
    CSR_FAILED = "csr_failed"
    CA_UNAVAILABLE = "ca_unavailable"

    # Future (post OPA/CAP integration)
    CERT_REVOKED = "cert_revoked"


class CertificateEventContext:
    """
    Structured context for certificate events.

    Provides correlation IDs, timestamps, and metadata for all
    certificate lifecycle events to enable distributed tracing
    and audit trails.
    """

    def __init__(
        self,
        event: CertificateEvent,
        worker_id: str,
        correlation_id: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> None:
        """
        Initialize event context.

        Args:
            event: Type of certificate event
            worker_id: Identifier of worker/component
            correlation_id: Optional correlation ID for distributed tracing
            metadata: Additional event-specific metadata
        """
        self.event = event
        self.worker_id = worker_id
        self.correlation_id = correlation_id or self._generate_correlation_id()
        self.timestamp = datetime.now(UTC).isoformat()
        self.metadata = metadata or {}

    @staticmethod
    def _generate_correlation_id() -> str:
        """Generate unique correlation ID for request tracing."""
        return f"cert_{uuid.uuid4().hex[:12]}"

    def to_dict(self) -> dict[str, Any]:
        """Convert event context to dictionary for logging/metrics."""
        return {
            "event": self.event.value,
            "correlation_id": self.correlation_id,
            "worker_id": self.worker_id,
            "timestamp": self.timestamp,
            **self.metadata,
        }

    def log(self, level: int = logging.INFO, message: Optional[str] = None) -> None:
        """
        Emit structured log entry for this event.

        Args:
            level: Logging level (INFO, WARNING, ERROR, etc.)
            message: Optional human-readable message
        """
        log_data = self.to_dict()
        if message:
            log_data["message"] = message

        logger.log(level, "Certificate event: %s", self.event.value, extra=log_data)


# Event handler registry
_event_handlers: dict[CertificateEvent, list[Callable[[CertificateEventContext], None]]] = {
    event: [] for event in CertificateEvent
}


def register_event_handler(
    event: CertificateEvent, handler: Callable[[CertificateEventContext], None]
) -> None:
    """
    Register callback for certificate events.

    Allows external systems (metrics, alerting, audit) to hook into
    certificate lifecycle events.

    Args:
        event: Event type to listen for
        handler: Callback function receiving event context

    Example:
        >>> def alert_on_expiry(ctx: CertificateEventContext):
        ...     send_pagerduty_alert(ctx.worker_id)
        >>> register_event_handler(CertificateEvent.CERT_EXPIRING_SOON, alert_on_expiry)
    """
    _event_handlers[event].append(handler)


def emit_certificate_event(
    event: CertificateEvent,
    worker_id: str,
    correlation_id: Optional[str] = None,
    metadata: Optional[dict[str, Any]] = None,
    log_level: int = logging.INFO,
) -> CertificateEventContext:
    """
    Emit certificate lifecycle event.

    Creates event context, logs structured data, and notifies
    registered handlers.

    Args:
        event: Type of certificate event
        worker_id: Identifier of worker/component
        correlation_id: Optional correlation ID for distributed tracing
        metadata: Additional event-specific metadata
        log_level: Logging level for this event

    Returns:
        Event context for further processing

    Example:
        >>> emit_certificate_event(
        ...     CertificateEvent.CERT_ISSUED,
        ...     worker_id="streaming-1",
        ...     metadata={"expires_at": "2026-11-15T00:00:00Z"}
        ... )
    """
    ctx = CertificateEventContext(
        event=event,
        worker_id=worker_id,
        correlation_id=correlation_id,
        metadata=metadata,
    )

    # Structured logging
    ctx.log(level=log_level)

    # Notify registered handlers
    for handler in _event_handlers[event]:
        try:
            handler(ctx)
        except Exception:
            logger.exception(
                "Event handler failed for %s (worker=%s, correlation=%s)",
                event.value,
                worker_id,
                ctx.correlation_id,
            )

    return ctx


# Metrics helpers (Prometheus integration points)
# These are placeholder functions that can be implemented with
# prometheus_client library or OpenTelemetry SDK


def record_cert_issuance(worker_id: str, success: bool) -> None:
    """
    Record certificate issuance attempt.

    Future implementation: Prometheus counter
    crank_cert_issuance_total{worker_id, status}
    """
    # TODO: Implement with prometheus_client.Counter
    logger.debug("Cert issuance: worker=%s, success=%s", worker_id, success)


def record_cert_expiration(worker_id: str, days_until_expiry: int) -> None:
    """
    Record certificate expiration time.

    Future implementation: Prometheus histogram
    crank_cert_expiration_seconds{worker_id}
    """
    # TODO: Implement with prometheus_client.Histogram
    logger.debug("Cert expiration: worker=%s, days=%d", worker_id, days_until_expiry)


def record_ca_unavailable(worker_id: str) -> None:
    """
    Record CA service unavailability.

    Future implementation: Prometheus counter
    crank_ca_unavailable_total{worker_id}
    """
    # TODO: Implement with prometheus_client.Counter
    logger.warning("CA unavailable for worker=%s", worker_id)
