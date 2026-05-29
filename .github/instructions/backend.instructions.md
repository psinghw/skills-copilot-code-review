---
applyTo: "backend/**/*,*.py"
---

## Backend Guidelines

- All API endpoints must be defined in the `routers` folder.
- Load example database content from the `database.py` file.
- Log detailed internal errors on the server, but continue returning appropriate HTTP status codes and sanitized, user-safe error messages (for example via `HTTPException(..., detail=...)`) to the frontend. Do not expose sensitive details such as stack traces, secrets, or internal implementation data.
- Ensure all APIs are explained in the documentation.
- Verify changes in the backend are reflected in the frontend (`src/static/**`). If possible breaking changes are found, mention them to the developer.