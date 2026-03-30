import structlog
import logging
import logging.handlers
import os
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource, SERVICE_NAME

def setup_telemetry():
    log_file = os.environ.get("LOG_FILE", "tangent.log")

    file_handler = logging.handlers.RotatingFileHandler(
        log_file, maxBytes=10 * 1024 * 1024, backupCount=5, encoding="utf-8"
    )
    file_handler.setLevel(logging.INFO)

    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.INFO)

    logging.basicConfig(
        format="%(message)s",
        level=logging.INFO,
        handlers=[stream_handler, file_handler],
    )

    # Structlog JSON setup
    structlog.configure(
        processors=[
            structlog.stdlib.add_log_level,
            structlog.stdlib.add_logger_name,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.dict_tracebacks,
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # OpenTelemetry setup
    resource = Resource(attributes={
        SERVICE_NAME: "nagent"
    })
    provider = TracerProvider(resource=resource)

    # Only enable OTLP export when an endpoint is explicitly configured.
    # Without this guard the exporter hammers localhost:4318 and floods the
    # log with ConnectionRefusedError stack traces when no collector is running.
    if os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT"):
        processor = BatchSpanProcessor(OTLPSpanExporter())
        provider.add_span_processor(processor)

    trace.set_tracer_provider(provider)

def get_tracer(name):
    return trace.get_tracer(name)
