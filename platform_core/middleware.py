import asyncio
import hashlib
import logging
import time
import uuid

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response
from starlette.routing import Match

from platform_core.faults import FaultController
from platform_core.logging import request_id_context
from platform_core.metrics import HTTP_DURATION, HTTP_REQUESTS

LOGGER = logging.getLogger(__name__)


UNMATCHED_ROUTE = "unmatched"


def _route_template(request: Request) -> str:
    """Return the matched route template (e.g. ``/products/{sku}``) for metric labels.

    Using the raw URL path as a label value creates one Prometheus time series per id
    and per scanner probe (unbounded cardinality). Requests that match no route share a
    single ``unmatched`` label value.
    """
    route = request.scope.get("route")
    if route is None:
        # Not routed yet, e.g. a synthetic fault answered before call_next.
        for candidate in getattr(request.app, "routes", ()):
            match, _ = candidate.matches(request.scope)
            if match is Match.FULL:
                route = candidate
                break
    template = getattr(route, "path_format", None) or getattr(route, "path", None)
    return template or UNMATCHED_ROUTE


def _deterministic_failure(request_id: str, error_rate: float) -> bool:
    if error_rate <= 0:
        return False
    digest = hashlib.sha256(request_id.encode()).hexdigest()
    sample = int(digest[:8], 16) / 0xFFFFFFFF
    return sample < error_rate


class ObservabilityMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app: object,
        *,
        service_name: str,
        fault_controller: FaultController,
    ) -> None:
        super().__init__(app)
        self.service_name = service_name
        self.fault_controller = fault_controller

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        request_id = request.headers.get("x-request-id", str(uuid.uuid4()))
        token = request_id_context.set(request_id)
        started = time.perf_counter()
        route = request.url.path
        status = 500
        try:
            bypass_faults = (
                route.startswith(("/health/", "/internal/faults")) or route == "/metrics"
            )
            if not bypass_faults:
                profile = self.fault_controller.current()
                if profile.latency_ms:
                    await asyncio.sleep(profile.latency_ms / 1000)
                if _deterministic_failure(request_id, profile.error_rate):
                    status = 503
                    return JSONResponse(
                        status_code=status,
                        content={
                            "detail": "synthetic fault injected",
                            "request_id": request_id,
                        },
                    )
            response = await call_next(request)
            status = response.status_code
            response.headers["x-request-id"] = request_id
            return response
        except Exception:
            LOGGER.exception("Unhandled request failure")
            raise
        finally:
            duration = time.perf_counter() - started
            route_label = _route_template(request)
            HTTP_REQUESTS.labels(
                service=self.service_name,
                method=request.method,
                route=route_label,
                status=str(status),
            ).inc()
            HTTP_DURATION.labels(
                service=self.service_name,
                method=request.method,
                route=route_label,
            ).observe(duration)
            request_id_context.reset(token)
