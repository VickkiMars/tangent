import structlog
import logging
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource, SERVICE_NAME

def setup_telemetry():
    # Basic logging config to catch standard logging output
    logging.basicConfig(format="%(message)s", level=logging.INFO)

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
    
    # We use a dummy endpoint by default; in prod, configure OTEL_EXPORTER_OTLP_ENDPOINT
    processor = BatchSpanProcessor(OTLPSpanExporter())
    provider.add_span_processor(processor)
    trace.set_tracer_provider(provider)

def get_tracer(name):
    return trace.get_tracer(name)
