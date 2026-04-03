# Backend Development Constitution

Standards and principles for backend service development.

## API Design

### REST Principles
- Use nouns for resources: `/users`, `/orders`, not `/getUser`, `/createOrder`
- Use HTTP methods semantically: GET (read), POST (create), PUT (replace), PATCH (update), DELETE (remove)
- Return appropriate HTTP status codes:
  - 200 OK, 201 Created, 204 No Content
  - 400 Bad Request, 401 Unauthorized, 403 Forbidden, 404 Not Found, 409 Conflict
  - 500 Internal Server Error

### Error Responses
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Human-readable description",
    "details": [
      {"field": "email", "message": "Invalid email format"}
    ]
  }
}
```

## Error Handling

1. Never expose internal errors to clients
2. Log full error details server-side
3. Use structured error types with codes
4. Distinguish between 4xx (client errors) and 5xx (server errors)

## Security

### Authentication & Authorization
- Use short-lived JWT tokens (15 minutes access, 7 days refresh)
- Validate all inputs server-side regardless of client-side validation
- Implement rate limiting on authentication endpoints
- Use HTTPS only in production

### Data Protection
- Hash passwords with bcrypt (cost factor >= 12)
- Never log sensitive data (passwords, tokens, PII)
- Encrypt sensitive data at rest

## Database

1. Use transactions for multi-step operations
2. Use parameterized queries to prevent SQL injection
3. Index foreign keys and frequently queried columns
4. Set appropriate timeouts for queries
5. Use connection pooling
