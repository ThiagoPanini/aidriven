# Clean Architecture Principles

Rules for maintaining clean, maintainable software architecture.

## Core Rules

### 1. Layer Separation

The system is divided into layers with strict boundaries:

- **Domain** (innermost): entities, value objects, business rules
- **Application**: use cases, application services
- **Infrastructure**: databases, APIs, file systems, frameworks
- **Presentation**: UI, CLI, HTTP controllers

**Rule**: Dependencies point inward only. Inner layers must not import from outer layers.

### 2. Dependency Rule

```
Presentation → Application → Domain
Infrastructure → Application → Domain
```

- `domain/` must not import from `services/`, `infra/`, or `presentation/`
- `services/` may import from `domain/` only
- `infra/` implements interfaces defined in `domain/` or `services/`
- `presentation/` calls `services/` or `app/` - never directly touches `infra/`

### 3. Entity Independence

Domain entities must:
- Contain only business logic
- Have no framework dependencies
- Be serializable without ceremony
- Not know about persistence

### 4. Use Case Focus

Each use case (service function) should:
- Have a single responsibility
- Be independently testable
- Not know about HTTP, CLI, or UI concerns
- Accept and return domain objects

### 5. Testability

Each layer is independently testable:
- Domain: pure unit tests, no mocks needed
- Services: mock infrastructure interfaces
- Infrastructure: integration tests
- Presentation: test input/output handling

## File Organization

```
src/myapp/
  domain/          # entities, value objects, enums
  services/        # use cases, business logic
  infra/           # external systems integration
  presentation/    # CLI, HTTP, UI
  app.py           # orchestration, composition root
```

## Anti-Patterns to Avoid

- Business logic in CLI handlers or HTTP controllers
- Database queries in domain entities
- Direct framework imports in domain layer
- Circular dependencies between layers
- God objects that span multiple layers
