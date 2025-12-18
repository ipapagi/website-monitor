"""FastAPI application factory and router wiring."""
try:
    from fastapi import FastAPI
except ImportError:  # pragma: no cover - app factory guarded by import elsewhere
    FastAPI = None

from . import routes_daily, routes_export, routes_incoming, routes_procedures, routes_search, routes_status


def create_app() -> "FastAPI":
    if FastAPI is None:
        raise ImportError("FastAPI δεν είναι εγκατεστημένο")

    app = FastAPI(
        title="PKM Monitor API",
        version="1.0.0",
        description="API για πρόσβαση στα δεδομένα παρακολούθησης του PKM Portal",
    )

    app.include_router(routes_daily.router)
    app.include_router(routes_incoming.router)
    app.include_router(routes_procedures.router)
    app.include_router(routes_search.router)
    app.include_router(routes_status.router)
    app.include_router(routes_export.router)

    return app
