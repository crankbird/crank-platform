# Docker Security and Base Image Management

## Current Status

### Base Image Security Policy

- **GPU Classifier**: `python:3.12-slim-bookworm` (Updated from vulnerable `python:3.12-bookworm`)

- **CPU Classifier**: `python:3.11-slim` (Secure baseline)

- **Policy**: Use `-slim` variants to minimize attack surface

### Security Improvements Applied

#### 1. Base Image Updates

```dockerfile
# ❌ BEFORE: Full bookworm with vulnerabilities

FROM python:3.12-bookworm

# ✅ AFTER: Slim variant with reduced attack surface

FROM python:3.12-slim-bookworm

```

#### 2. Why Slim Variants

- **Reduced Attack Surface**: 75% fewer packages than full images

- **Faster Security Patches**: Smaller update footprint

- **Better Cache Efficiency**: Smaller base layers

- **Production Standard**: Industry best practice for production deployments

### Base Image Maintenance Schedule

#### Monthly Review Process

1. Check for security advisories: `docker scout cves [image]`

2. Update to latest patch versions

3. Test all services after base image updates

4. Document any breaking changes

#### Automated Scanning

```bash
# Scan for vulnerabilities

docker scout cves python:3.12-slim-bookworm
docker scout cves python:3.11-slim

# Quick scan all local images

docker images --format "table {{.Repository}}:{{.Tag}}" | grep python | xargs -I {} docker scout cves {}

```

### Security Configuration

#### Non-Root User Pattern

```dockerfile
# Create dedicated service user

RUN addgroup --gid 1000 worker && \
    adduser --uid 1000 --gid 1000 --disabled-password worker

# Switch to non-root for execution

USER worker

```

#### Minimal Dependencies

```dockerfile
# Only install required system packages

RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

```

### GPU-Specific Security Considerations

#### NVIDIA Runtime Security

```dockerfile
# Restrict GPU access to compute capabilities only

ENV NVIDIA_DRIVER_CAPABILITIES=compute,utility
ENV NVIDIA_VISIBLE_DEVICES=all

```

#### CUDA Version Management

- Pin CUDA versions in requirements for reproducibility

- Use PyTorch with specific CUDA compatibility

- Test GPU functionality in security-hardened environments

### Monitoring and Alerts

#### Security Scanning Integration

- **CI/CD Pipeline**: Fail builds on HIGH/CRITICAL vulnerabilities

- **Runtime Monitoring**: Weekly vulnerability scans of deployed containers

- **Update Notifications**: Subscribe to Python Docker image security advisories

#### Response Procedures

1. **Critical Vulnerability**: Emergency patch within 24 hours

2. **High Vulnerability**: Patch within 72 hours

3. **Medium/Low**: Include in next scheduled maintenance

### Best Practices Summary

1. **Always Use Slim Variants**: Unless specific packages required

2. **Pin Specific Versions**: Avoid `latest` tags in production

3. **Regular Security Scans**: Automated vulnerability assessment

4. **Non-Root Execution**: Create dedicated service users

5. **Minimal Dependencies**: Only install required packages

6. **Multi-Stage Builds**: Separate build and runtime environments

### Example Secure Dockerfile Pattern

```dockerfile
# Multi-stage build for security and efficiency

FROM python:3.12-slim-bookworm as builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM python:3.12-slim-bookworm as runtime
# Create non-root user

RUN addgroup --gid 1000 crank && \
    adduser --uid 1000 --gid 1000 --disabled-password crank

# Copy only runtime dependencies

COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Application code

COPY --chown=crank:crank . /app
USER crank
WORKDIR /app
EXPOSE 8000
CMD ["python", "main.py"]

```

This approach ensures minimal attack surface while maintaining full functionality for ML workloads.
