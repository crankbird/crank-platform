# ADR-0024: Observability Strategy - Logs, Metrics, Traces

**Status**: Proposed (Extended in Phase 3 with Controller Tracing)
**Date**: 2025-11-16
**Deciders**: Platform Team
**Technical Story**: [ADR Backlog 2025-11-16 – Platform Services / Extensions](../planning/adr-backlog-2025-11-16.md#platform-services--extensions), [Enhancement Roadmap - Observability](../proposals/enhancement-roadmap.md#observability--reliability-new--enterprise-requirements)

## Context and Problem Statement

A distributed system with controllers and workers needs observability for debugging, performance monitoring, and operational insights. Logs, metrics, and traces provide different views. How should we implement observability across the platform?

## Decision Drivers

- Debugging: Find root causes quickly
- Performance: Monitor latency and throughput
- Operations: Health and capacity monitoring
- Distributed tracing: Follow requests across services
- Cost: Avoid expensive proprietary tools
- Local-first: Works in development

## Considered Options

- **Option 1**: Structured logging + Prometheus + OpenTelemetry - Proposed
- **Option 2**: Proprietary observability platform (Datadog/New Relic)
- **Option 3**: Logs-only approach

## Decision Outcome

**Chosen option**: "Structured logging + Prometheus + OpenTelemetry", because it provides comprehensive observability (logs, metrics, traces) using open standards and works identically in local development and production.

### Positive Consequences

- Structured logs for easy parsing
- Prometheus metrics for monitoring
- OpenTelemetry traces for distributed debugging
- Open standards (no vendor lock-in)
- Works locally (no cloud required)
- Grafana for visualization

### Negative Consequences

- Multiple tools to configure
- Learning curve
- Storage management for metrics/traces
- No built-in alerting (need Alertmanager)

## Pros and Cons of the Options

### Option 1: Structured Logging + Prometheus + OpenTelemetry

Open-source observability stack.

**Pros:**
- Comprehensive (logs, metrics, traces)
- Open standards
- Local-first
- No vendor lock-in
- Rich ecosystem
- Free

**Cons:**
- Multiple tools
- Configuration complexity
- Storage management
- Manual alerting setup

### Option 2: Proprietary Observability Platform

Datadog, New Relic, Honeycomb.

**Pros:**
- Integrated solution
- Rich features
- Built-in alerting
- Managed service
- Easy setup

**Cons:**
- Expensive at scale
- Vendor lock-in
- Cloud-only (no local dev)
- Data privacy concerns

### Option 3: Logs-Only Approach

Just structured logging.

**Pros:**
- Simple
- Universal
- Easy to implement
- Low overhead

**Cons:**
- No metrics
- No distributed tracing
- Limited performance insights
- Manual log analysis

## Links

- [Related to] ADR-0004 (Local-first execution)
- [Related to] ADR-0001 (Controller/worker model)
- [Related to] ADR-0020 (Git-based CI - for log analysis in CI)
- [Implemented in] Phase 3 Session 2 (Controller OpenTelemetry instrumentation - see PHASE_3_ATTACK_PLAN.md)
- [Related to] Enhancement Roadmap (W3C Trace Context propagation, Jaeger/Tempo integration)

## Implementation Notes

**Three Pillars of Observability**:

1. **Logs**: Discrete events (errors, state changes)
2. **Metrics**: Aggregated measurements (latency, throughput)
3. **Traces**: Request flows across services

**Structured Logging** (Python `structlog`):

```python
# All workers and controller use structured logging
import structlog

logger = structlog.get_logger()

# Instead of: print(f"Processing request {req_id}")
logger.info(
    "processing_request",
    request_id=req_id,
    worker_id=self.worker_id,
    capability="convert_document_to_pdf",
    input_size_bytes=len(doc_bytes)
)

# Errors with context
logger.error(
    "conversion_failed",
    request_id=req_id,
    error=str(e),
    exc_info=True
)
```

**Configuration** (`logging_config.py`):

```python
import structlog

def configure_logging():
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()  # JSON for parsing
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
    )
```

**Prometheus Metrics**:

```python
# Expose metrics at /metrics endpoint
from prometheus_client import Counter, Histogram, Gauge, start_http_server

# Counters (ever-increasing)
requests_total = Counter(
    'worker_requests_total',
    'Total requests processed',
    ['worker_id', 'capability', 'status']
)

# Histograms (distributions)
request_duration = Histogram(
    'worker_request_duration_seconds',
    'Request processing time',
    ['worker_id', 'capability']
)

# Gauges (current values)
active_requests = Gauge(
    'worker_active_requests',
    'Currently processing requests',
    ['worker_id']
)

# Usage in worker
async def handle_request(self, request):
    active_requests.labels(worker_id=self.worker_id).inc()

    with request_duration.labels(
        worker_id=self.worker_id,
        capability=request.capability
    ).time():
        try:
            result = await self.process(request)
            requests_total.labels(
                worker_id=self.worker_id,
                capability=request.capability,
                status='success'
            ).inc()
            return result
        except Exception as e:
            requests_total.labels(
                worker_id=self.worker_id,
                capability=request.capability,
                status='error'
            ).inc()
            raise
        finally:
            active_requests.labels(worker_id=self.worker_id).dec()
```

**Metrics Endpoint**:

```python
from fastapi import FastAPI
from prometheus_client import make_asgi_app

app = FastAPI()

# Mount Prometheus /metrics endpoint
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)
```

**OpenTelemetry Tracing**:

```python
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

# Setup tracer
trace.set_tracer_provider(TracerProvider())
tracer = trace.get_tracer(__name__)

# Export to Jaeger/Tempo
otlp_exporter = OTLPSpanExporter(endpoint="http://localhost:4317")
trace.get_tracer_provider().add_span_processor(
    BatchSpanProcessor(otlp_exporter)
)

# Trace request flow
@tracer.start_as_current_span("convert_document")
async def convert_document(self, doc_bytes: bytes) -> bytes:
    span = trace.get_current_span()
    span.set_attribute("document.size_bytes", len(doc_bytes))

    # Nested spans
    with tracer.start_as_current_span("parse_document"):
        parsed = await self.parse(doc_bytes)

    with tracer.start_as_current_span("render_pdf"):
        pdf = await self.render(parsed)

    span.set_attribute("pdf.size_bytes", len(pdf))
    return pdf
```

**Docker Compose Observability Stack**:

```yaml
# docker-compose.observability.yml
version: '3.8'

services:
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus-data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    volumes:
      - grafana-data:/var/lib/grafana
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin

  jaeger:
    image: jaegertracing/all-in-one:latest
    ports:
      - "16686:16686"  # UI
      - "4317:4317"    # OTLP gRPC
    environment:
      - COLLECTOR_OTLP_ENABLED=true

  loki:
    image: grafana/loki:latest
    ports:
      - "3100:3100"
    volumes:
      - ./loki-config.yml:/etc/loki/local-config.yaml

volumes:
  prometheus-data:
  grafana-data:
```

**Prometheus Scrape Config**:

```yaml
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'crank-controller'
    static_configs:
      - targets: ['host.docker.internal:9090']

  - job_name: 'crank-workers'
    static_configs:
      - targets:
          - 'worker-streaming:8500'
          - 'worker-document:8501'
          - 'worker-email:8502'
```

**Grafana Dashboard** (JSON):

```json
{
  "dashboard": {
    "title": "Crank Platform Overview",
    "panels": [
      {
        "title": "Request Rate",
        "targets": [{
          "expr": "rate(worker_requests_total[5m])"
        }]
      },
      {
        "title": "Request Duration (p95)",
        "targets": [{
          "expr": "histogram_quantile(0.95, worker_request_duration_seconds_bucket)"
        }]
      },
      {
        "title": "Active Workers",
        "targets": [{
          "expr": "up{job=~'crank-.*'}"
        }]
      }
    ]
  }
}
```

**Local Development**:

```bash
# Start observability stack
docker-compose -f docker-compose.observability.yml up -d

# Access UIs
open http://localhost:3000  # Grafana
open http://localhost:9090  # Prometheus
open http://localhost:16686 # Jaeger
```

**Query Examples**:

```promql
# Prometheus queries

# Request rate per worker
rate(worker_requests_total[5m])

# Error rate
rate(worker_requests_total{status="error"}[5m]) /
rate(worker_requests_total[5m])

# 95th percentile latency
histogram_quantile(0.95, worker_request_duration_seconds_bucket)

# Workers under high load
worker_active_requests > 50
```

## Review History

- 2025-11-16 - Initial proposal (future implementation)
- 2025-11-16 - Extended with controller tracing plan (Phase 3 Session 2)

## Phase 3 Extension: Controller OpenTelemetry Instrumentation

**Implementation**: Phase 3 Session 2 adds W3C Trace Context propagation to all controller endpoints.

**Goals**:
- Distributed tracing across controller → worker calls
- Trace context propagation via `traceparent` header
- Exemplar linking (traces ↔ metrics ↔ logs)
- Integration with Jaeger/Tempo (future)

**Controller Instrumentation**:

```python
from opentelemetry import trace
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import ConsoleSpanExporter, BatchSpanProcessor

# Setup tracer (console export in Phase 3, Jaeger later)
trace.set_tracer_provider(TracerProvider())
tracer = trace.get_tracer(__name__)
trace.get_tracer_provider().add_span_processor(
    BatchSpanProcessor(ConsoleSpanExporter())
)

app = FastAPI()
FastAPIInstrumentor.instrument_app(app)  # Auto-instrument all endpoints

@app.post("/route")
async def route(request: Request, verb: str, capability: str):
    # Span automatically created by FastAPIInstrumentor
    # Add custom attributes
    span = trace.get_current_span()
    span.set_attribute("capability", f"{verb}:{capability}")

    with tracer.start_as_current_span("registry_lookup") as lookup_span:
        workers = registry.get_workers_for_capability(f"{verb}:{capability}")
        lookup_span.set_attribute("workers_found", len(workers))

    with tracer.start_as_current_span("worker_call") as call_span:
        result = await call_worker(workers[0], request)
        call_span.set_attribute("worker_id", workers[0].worker_id)

    return result
```

**Trace Propagation to Workers**:

```python
# Controller propagates trace context to workers
from opentelemetry.propagate import inject

async def call_worker(worker: WorkerEndpoint, request: dict):
    headers = {}
    inject(headers)  # Adds traceparent, tracestate headers

    async with httpx.AsyncClient() as client:
        response = await client.post(
            worker.url,
            json=request,
            headers=headers,  # Propagate trace context
            cert=(cert_path, key_path)
        )
    return response.json()
```

**Worker Trace Continuation**:

```python
# Workers extract trace context and create child spans
from opentelemetry.propagate import extract

@app.post("/execute")
async def execute(request: Request, payload: dict):
    # Extract parent trace context from headers
    context = extract(request.headers)

    with tracer.start_as_current_span(
        "worker_execute",
        context=context  # Child of controller span
    ) as span:
        span.set_attribute("worker_id", self.worker_id)
        result = await self.process(payload)
        return result
```

**Metrics Exemplars** (link traces to metrics):

```python
from opentelemetry.sdk.metrics.export import ConsoleMetricExporter, PeriodicExportingMetricReader
from opentelemetry.metrics import get_meter_provider, set_meter_provider
from opentelemetry.sdk.metrics import MeterProvider

# Setup meter with exemplars
set_meter_provider(
    MeterProvider(
        metric_readers=[PeriodicExportingMetricReader(ConsoleMetricExporter())]
    )
)

meter = get_meter_provider().get_meter(__name__)

# Histogram with exemplars (links to traces)
routing_duration = meter.create_histogram(
    "controller.routing.duration",
    unit="ms",
    description="Time to route request"
)

# Record with trace context
span = trace.get_current_span()
routing_duration.record(
    duration_ms,
    attributes={"capability": capability},
    # Exemplar automatically links to current span
)
```

**Future Integration**:
- **Jaeger** backend for trace storage/visualization
- **Tempo** for scalable trace storage
- **Grafana** for unified traces + metrics + logs view
- **Honeycomb** for advanced trace analysis (optional)

**Phase 3 Deliverable**: Console-based tracing proves wiring works. Backend integration is post-Phase 3.
