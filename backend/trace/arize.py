from phoenix.otel import register
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
import logging

# Configure logging to reduce noise
logging.getLogger("opentelemetry").setLevel(logging.WARNING)

# Register Phoenix with selective instrumentation
tracer_provider = register(
  project_name="learned",
  endpoint="http://localhost:6006/v1/traces",
  auto_instrument=True  # Disable auto-instrumentation
)

# # Manually instrument specific components (excluding async generators)
# FastAPIInstrumentor().instrument()
# HTTPXClientInstrumentor().instrument()
# SQLAlchemyInstrumentor().instrument()
