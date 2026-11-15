
import os
import time
import math
import json
import socket
import logging
import uuid
from threading import Lock
from collections import deque

from fastapi import FastAPI, HTTPException, Query, Request

# --------------------------------------------------
# Configuration
# --------------------------------------------------

APP_NAME = "CloudPulse API"
APP_ENV = os.getenv("APP_ENV", "local")

DEFAULT_ITERATIONS = int(
    os.getenv("WORK_ITERATIONS_DEFAULT", "1200000")
)

MAX_ITERATIONS = int(
    os.getenv("MAX_WORK_ITERATIONS", "20000000")
)

# --------------------------------------------------
# Logging
# --------------------------------------------------

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(message)s"
)

logger = logging.getLogger("cloudpulse")

# --------------------------------------------------
# Application
# --------------------------------------------------

app = FastAPI(
    title=APP_NAME,
    version="1.0.0"
)

started_at = time.time()

lock = Lock()

completed_requests = 0

recent_latencies = deque(maxlen=100)


# --------------------------------------------------
# Request logging middleware
# --------------------------------------------------

@app.middleware("http")
async def request_observer(request: Request, call_next):

    request_id = request.headers.get(
        "x-request-id",
        str(uuid.uuid4())
    )

    start = time.perf_counter()

    try:
        response = await call_next(request)

        response.headers["X-Request-ID"] = request_id

        return response

    finally:
        elapsed_ms = round(
            (time.perf_counter() - start) * 1000,
            2
        )

        logger.info(json.dumps({
            "event": "http_request",
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "duration_ms": elapsed_ms
        }))


# --------------------------------------------------
# Health checks
# --------------------------------------------------

@app.get("/health")
@app.get("/api/health")
def health():

    return {
        "status": "healthy",
        "service": "backend",
        "hostname": socket.gethostname()
    }


@app.get("/ready")
def readiness():

    return {
        "status": "ready",
        "service": "backend"
    }


# --------------------------------------------------
# Dashboard API
# --------------------------------------------------

@app.get("/api/dashboard")
def dashboard():

    with lock:

        count = completed_requests

        samples = list(recent_latencies)

    average_latency = (
        round(sum(samples) / len(samples), 2)
        if samples else 0
    )

    return {
        "application": "CloudPulse",
        "environment": APP_ENV,
        "hostname": socket.gethostname(),
        "uptime_seconds": round(
            time.time() - started_at, 1
        ),
        "completed_work_requests": count,
        "recent_average_processing_ms": average_latency,
        "default_iterations": DEFAULT_ITERATIONS,
        "max_iterations": MAX_ITERATIONS
    }


# --------------------------------------------------
# CPU workload simulation
# --------------------------------------------------

@app.get("/api/work")
def run_work(
    iterations: int = Query(
        default=None,
        ge=1000
    )
):

    global completed_requests

    n = (
        iterations
        if iterations is not None
        else DEFAULT_ITERATIONS
    )

    if n > MAX_ITERATIONS:

        raise HTTPException(
            status_code=400,
            detail=f"Maximum iterations: {MAX_ITERATIONS}"
        )

    start = time.perf_counter()

    # Deliberately CPU-intensive processing.
    result = 0.0

    for i in range(1, n + 1):

        result += math.sqrt(i) * math.sin(i)

    processing_time = round(
        (time.perf_counter() - start) * 1000,
        2
    )

    with lock:

        completed_requests += 1

        request_number = completed_requests

        recent_latencies.append(processing_time)

    logger.info(json.dumps({
        "event": "work_completed",
        "hostname": socket.gethostname(),
        "iterations": n,
        "duration_ms": processing_time,
        "task_request_count": request_number
    }))

    return {
        "status": "completed",
        "hostname": socket.gethostname(),
        "iterations": n,
        "processing_time_ms": processing_time,
        "task_completed_requests": request_number,
        "result_checksum": round(result, 4)
    }


# --------------------------------------------------
# Root endpoint
# --------------------------------------------------

@app.get("/")
def root():

    return {
        "application": APP_NAME,
        "health": "/health",
        "dashboard": "/api/dashboard"
    }
