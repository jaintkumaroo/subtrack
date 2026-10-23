"""SubTrack API: wires the routers together and prepares the database on startup."""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse

from app.config import settings
from app.database.init_db import init_db
from app.routers import categories, dashboard, subscriptions, system
from app.services.subscription_service import BadRequestError, ConflictError, NotFoundError


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        init_db()
    except Exception as error:  # noqa: BLE001
        print("\n" + "=" * 70)
        print(f"Could not prepare the {settings.db_label} database.")
        print(f"Reason: {error}")
        if settings.db_mode == "mssql":
            print("\nFix the SQL Server settings in the .env file, then run:")
            print("    python -m app.database.diagnose")
            print("It checks the driver and the server name step by step.")
        print("=" * 70 + "\n")
        raise
    yield


app = FastAPI(
    title="SubTrack API",
    description="Track recurring subscriptions, see what they cost you, and never miss a renewal.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(NotFoundError)
async def not_found_handler(_: Request, error: NotFoundError):
    return JSONResponse(status_code=404, content={"detail": str(error)})


@app.exception_handler(ConflictError)
async def conflict_handler(_: Request, error: ConflictError):
    return JSONResponse(status_code=409, content={"detail": str(error)})


@app.exception_handler(BadRequestError)
async def bad_request_handler(_: Request, error: BadRequestError):
    return JSONResponse(status_code=400, content={"detail": str(error)})


app.include_router(system.router)
app.include_router(categories.router)
app.include_router(subscriptions.router)
app.include_router(dashboard.router)


@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse("/docs")
