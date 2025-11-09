# Resilient Discovery Service Configuration

The resilient discovery service supports the following environment variables for tuning worker registration and heartbeat behavior:

## Environment Variables

### `WORKER_HEARTBEAT_INTERVAL` (default: 45)

- **Description**: How often workers should send heartbeats to the platform (in seconds)

- **Recommended range**: 30-60 seconds

- **Impact**: Lower values = faster failure detection, higher network traffic

### `WORKER_TIMEOUT` (default: 120)

- **Description**: How long to wait before considering a worker dead (in seconds)

- **Recommended range**: 2-3x heartbeat interval (90-180 seconds)

- **Impact**: Lower values = faster failover, higher risk of false positives

### `WORKER_CLEANUP_INTERVAL` (default: 30)

- **Description**: How often the platform cleans up expired workers (in seconds)  

- **Recommended range**: 15-60 seconds

- **Impact**: Lower values = faster cleanup, slightly higher CPU usage

### `WORKER_HEARTBEAT_GRACE` (default: 2x heartbeat interval)

- **Description**: Grace period for heartbeat tolerance (in seconds)

- **Recommended range**: 1.5-3x heartbeat interval

- **Impact**: Lower values = stricter timing, higher risk of network-induced failures

## Configuration Examples

### High Availability (fast failover)

```bash
WORKER_HEARTBEAT_INTERVAL=30
WORKER_TIMEOUT=90
WORKER_CLEANUP_INTERVAL=15
WORKER_HEARTBEAT_GRACE=60

```

### Balanced (recommended for most workloads)

```bash
WORKER_HEARTBEAT_INTERVAL=45
WORKER_TIMEOUT=120
WORKER_CLEANUP_INTERVAL=30
WORKER_HEARTBEAT_GRACE=90

```

### IoT/Low Bandwidth (conservative)

```bash
WORKER_HEARTBEAT_INTERVAL=60
WORKER_TIMEOUT=180
WORKER_CLEANUP_INTERVAL=60
WORKER_HEARTBEAT_GRACE=120

```

## Monitoring

The discovery service logs important events:

- Worker registrations: `✅ Registered worker {id} ({type})`

- Heartbeats: `💓 Heartbeat from {id}` (debug level)

- Cleanup: `🧹 Cleaned up {count} expired workers`

- Unknown workers: `💔 Heartbeat from unknown worker {id}`

## Tuning Guidelines

1. **Start with defaults** - they work well for most scenarios

2. **Monitor worker logs** for "unknown worker" messages after platform restarts  

3. **Adjust heartbeat interval** based on your network reliability

4. **Set timeout to 2.5-3x heartbeat interval** for good failure detection

5. **Keep cleanup interval ≤ heartbeat interval** for responsive cleanup

## Platform Restart Recovery

Typical recovery times after platform restart:

- **With defaults**: ~60-90 seconds for full worker registry rebuild

- **With fast config**: ~30-45 seconds

- **With conservative config**: ~90-120 seconds

The recovery window depends on heartbeat timing - workers discover they need to re-register when their next heartbeat fails.
