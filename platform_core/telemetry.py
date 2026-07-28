import logging

from fastapi import FastAPI
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

LOGGER = logging.getLogger(__name__)
_httpx_instrumented = False


def configure_tracing(
    app: FastAPI,
    *,
    service_name: str,
    service_version: str,
    namespace: str,
    endpoint: str,
    enabled: bool,
) -> None:
    global _httpx_instrumented
    if not enabled:
        LOGGER.info("Tracing disabled", extra={"service": service_name})
        return

    resource = Resource.create(
        {
            "service.name": service_name,
            "service.version": service_version,
            "service.namespace": namespace,
            "deployment.environment": "cloud-native",
        }
    )
    provider = TracerProvider(resource=resource)
    provider.add_span_processor(
        BatchSpanProcessor(OTLPSpanExporter(endpoint=endpoint, insecure=True))
    )
    trace.set_tracer_provider(provider)
    FastAPIInstrumentor.instrument_app(app)
    if not _httpx_instrumented:
        HTTPXClientInstrumentor().instrument()
        _httpx_instrumented = True
