import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from config import get_settings
from database import init_db
from routers import predictions_router, readings_router, stream_router
from routers.status import router as status_router  # ← add this
from services.iot_poller import create_scheduler
from services.ml_service import init_ml_service

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── Startup ──────────────────────────────────────────────────────────
    logger.info("Initialising database tables...")
    await init_db()

    logger.info("Loading ML model (version=%s)...", settings.model_version)
    init_ml_service(
        model_path=settings.model_path,
        scaler_path=settings.scaler_path,
    )

    logger.info("Starting IoT poller (interval=%ds)...", settings.poll_interval_seconds)
    scheduler = create_scheduler()
    scheduler.start()

    logger.info("🚀 Backend ready")
    yield

    # ── Shutdown ─────────────────────────────────────────────────────────
    logger.info("Shutting down scheduler...")
    scheduler.shutdown(wait=False)
    logger.info("Goodbye.")


app = FastAPI(
    title="Predictive Maintenance API",
    description="IoT sensor ingestion + ML failure prediction backend.",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ── CORS ─────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
API_PREFIX = "/v1"
app.include_router(readings_router, prefix=API_PREFIX)
app.include_router(predictions_router, prefix=API_PREFIX)
app.include_router(stream_router, prefix=API_PREFIX)
app.include_router(status_router, prefix=API_PREFIX)  # ← add this


# ── Global exception handler ─────────────────────────────────────────────────
@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled exception for %s %s", request.method, request.url)
    return JSONResponse(
        status_code=500,
        content={
            "type": "about:blank",
            "title": "Internal Server Error",
            "detail": str(exc),
        },
    )


# ── Health check ─────────────────────────────────────────────────────────────
@app.get("/health", tags=["meta"])
async def health():
    return {"status": "ok", "version": app.version}