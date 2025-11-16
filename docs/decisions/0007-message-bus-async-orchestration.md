# ADR-0007: Use Message-Bus-Backed Asynchronous Orchestration

**Status**: Proposed
**Date**: 2025-11-16
**Deciders**: Platform Team
**Technical Story**: [ADR Backlog 2025-11-16 – Core Platform & Agent Architecture](../planning/adr-backlog-2025-11-16.md#core-platform--agent-architecture)

## Context and Problem Statement

Long-running agent tasks (document processing, model training, batch classification) need asynchronous execution. Cloud escalation requires request/response across network boundaries. We need an orchestration mechanism that supports async workflows, retries, and distributed execution.

## Decision Drivers

- Asynchronous execution: Don't block on long-running tasks
- Cloud escalation: Route jobs to remote workers
- Reliability: Retries and dead-letter queues
- Observability: Track job progress and failures
- Scalability: Handle burst workloads
- Simplicity: Avoid overengineering for current scale

## Considered Options

- **Option 1**: Message bus (RabbitMQ/Redis Streams) - Proposed
- **Option 2**: HTTP polling with job queue
- **Option 3**: Full workflow engine (Temporal/Airflow)

## Decision Outcome

**Chosen option**: "Message bus (technology TBD)", because it provides the right balance of async capability, reliability, and operational simplicity for distributed agent execution.

### Positive Consequences

- Async job execution out of the box
- Reliable message delivery (acks, retries)
- Decouples producers from consumers
- Enables cloud escalation naturally
- Progress tracking via message state
- Dead-letter queues for failed jobs

### Negative Consequences

- Requires message bus infrastructure
- Message ordering guarantees needed
- Debugging distributed workflows harder
- Need monitoring for queue depth/lag
- Technology choice deferred (RabbitMQ vs Redis vs Kafka)

## Pros and Cons of the Options

### Option 1: Message Bus (RabbitMQ/Redis Streams)

Async message queue handles job distribution.

**Pros:**
- Async by default
- Reliable delivery
- Decoupling
- Scales horizontally
- Mature tooling

**Cons:**
- Infrastructure dependency
- Complexity in failure modes
- Need monitoring
- Technology choice pending

### Option 2: HTTP Polling with Job Queue

Database-backed job queue, workers poll for jobs.

**Pros:**
- Simple to implement
- No external dependencies
- Easy to debug
- Transactional guarantees

**Cons:**
- Polling overhead
- Not truly async
- Doesn't scale well
- Manual retry logic
- Poor for real-time jobs

### Option 3: Full Workflow Engine (Temporal/Airflow)

Dedicated workflow orchestration system.

**Pros:**
- Rich workflow features
- Battle-tested
- Visual workflow editor
- Automatic retries
- Strong durability

**Cons:**
- Heavy infrastructure
- Overkill for current needs
- Steep learning curve
- Vendor lock-in
- High operational overhead

## Links

- [Related to] ADR-0004 (Cloud escalation needs message bus)
- [Related to] ADR-0001 (Controller routes jobs to workers)
- [Enables] Distributed agent execution across local/cloud boundary

## Implementation Notes

**Deferred Technology Choice:**
Evaluating:
- **RabbitMQ**: Full-featured, AMQP standard
- **Redis Streams**: Lightweight, already in stack
- **NATS**: Cloud-native, simple
- **Kafka**: Overkill for current scale

**Initial Implementation** (Redis Streams as MVP):

```python
# Producer (Controller)
redis.xadd("jobs:classify", {
    "job_id": "job-123",
    "capability": "classify_email",
    "input": json.dumps({"email": "..."}),
    "callback": "https://local-controller/results/job-123"
})

# Consumer (Worker)
jobs = redis.xread({"jobs:classify": "$"}, block=5000)
for job in jobs:
    result = process_job(job)
    requests.post(job["callback"], json=result)
    redis.xack("jobs:classify", "worker-group", job["id"])
```

**Future Enhancements:**
- Priority queues
- Job scheduling
- Workflow composition
- Saga pattern for transactions

## Review History

- 2025-11-16 - Initial proposal (technology TBD)
