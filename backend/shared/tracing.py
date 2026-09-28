import os

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (
    OTLPSpanExporter,
)
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor


def init_tracing(service_name: str):

    resource = Resource.create(
        {
            "service.name": service_name,
            "service.version": os.getenv(
                "SERVICE_VERSION",
                "1.0.0",
            ),
            "deployment.environment": os.getenv(
                "ENVIRONMENT",
                "production",
            ),
        }
    )

    provider = TracerProvider(
        resource=resource
    )

    exporter = OTLPSpanExporter(
        endpoint=os.getenv(
            "OTEL_EXPORTER_OTLP_ENDPOINT",
            "http://127.0.0.1:4317",
        ),
        insecure=True,
    )

    provider.add_span_processor(
        BatchSpanProcessor(exporter)
    )

    trace.set_tracer_provider(provider)


def instrument_fastapi(app):

    FastAPIInstrumentor.instrument_app(app)