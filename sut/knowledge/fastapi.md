# FastAPI

FastAPI is a Python web framework built on Starlette and Pydantic. Routes are
declared with decorators such as @app.get and @app.post, and path and query
parameters are parsed from type-annotated function signatures.

Dependency injection uses Depends: a callable declared with Depends is
resolved per request and can provide database sessions or authentication.
Pydantic models validate request and response bodies automatically, and
FastAPI generates OpenAPI documentation at /docs from the type annotations.

FastAPI runs on an ASGI server such as uvicorn and supports async endpoints.
