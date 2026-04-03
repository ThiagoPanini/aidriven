# Observability Constitution

Standards for logging, metrics, tracing, and alerting.

## Logging

### Structure
Use structured JSON logging in production:

```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "level": "INFO",
  "service": "user-service",
  "trace_id": "abc123",
  "message": "User created successfully",
  "duration_ms": 45
}
```

### Log Levels
- **DEBUG**: Detailed diagnostic information (development only)
- **INFO**: Normal application events
- **WARNING**: Recoverable issues
- **ERROR**: Errors requiring attention
- **CRITICAL**: System failures requiring immediate action

### What NOT to Log
- Passwords, tokens, API keys
- Full credit card numbers
- Personally identifiable information (PII) without masking

## Metrics

### Standard Metrics
Every service must expose:

1. **Request rate**: requests per second
2. **Error rate**: percentage of 4xx/5xx responses
3. **Latency**: p50, p95, p99 response times
4. **Saturation**: CPU, memory, queue depth

## Alerting

### Severity Levels
- **P1 (Critical)**: Service down, data loss - wake on-call immediately
- **P2 (High)**: Degraded service, significant user impact
- **P3 (Medium)**: Minor degradation - create ticket
- **P4 (Low)**: Informational - log only

## Health Checks

Every service must expose:
- `GET /health` - basic liveness check (returns 200 if running)
- `GET /ready` - readiness check (returns 200 if ready to serve traffic)
